//! Shutter Value Maker — Rust port of the three-step Python workflow
//! (create_shutter_value_file_step1/2/3.py) as a single interactive GUI.

// on Windows, don't open a console window behind the GUI
#![windows_subsystem = "windows"]

mod physics;
mod shutter;
mod theme;

use anyhow::{anyhow, Result};
use egui::{Color32, RichText};
use egui_plot::{CoordinatesFormatter, Corner, Legend, LineStyle, MarkerShape, Plot, PlotPoint, PlotPoints, Points, Polygon, Text, VLine};

const NUMBER_OF_GAPS_TO_DISPLAY: usize = 5;

fn main() -> eframe::Result {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default().with_inner_size([1500.0, 950.0]),
        ..Default::default()
    };
    eframe::run_native(
        "Shutter Value Maker",
        options,
        Box::new(|cc| {
            // Saved light/dark preference, shared by all the VENUS rust
            // tools (dark when none is saved); the toolbar has a toggle.
            cc.egui_ctx.set_theme(theme::load());
            Ok(Box::new(App::default()))
        }),
    )
}

#[derive(PartialEq, Clone, Copy)]
enum Step {
    Gaps,
    Frames,
    WriteFile,
}

#[derive(PartialEq, Clone, Copy)]
enum XAxis {
    Tof,
    Lambda,
}

struct App {
    step: Step,
    gaps_axis: XAxis,
    frames_axis: XAxis,
    // step 1 inputs (defaults match the Python prompts)
    minimum_lambda_measurable: f64,
    detector_offset_is_manual: bool,
    manual_detector_offset: f64, // microseconds
    detector_sample_distance: f64,
    source_frequency: f64,
    time_bin: f64,
    lambda_requested_text: String,
    // step 2 input
    dead_time_text: String,
    // step 3 inputs
    output_folder: String,
    status: String,
}

impl Default for App {
    fn default() -> Self {
        Self {
            step: Step::Gaps,
            gaps_axis: XAxis::Tof,
            frames_axis: XAxis::Tof,
            minimum_lambda_measurable: 1.9,
            detector_offset_is_manual: false,
            manual_detector_offset: 12006.0,
            detector_sample_distance: 25.0,
            source_frequency: 60.0,
            time_bin: 5.12,
            lambda_requested_text: "4.07 3.36 6.73 2.62 2.49 2.22 3.28 3.84 6.23".to_string(),
            dead_time_text: "2.95 3.60".to_string(),
            output_folder: "./".to_string(),
            status: String::new(),
        }
    }
}

struct Step1Result {
    detector_offset: f64,        // microseconds
    minimum_lambda_measurable: f64, // Angstroms (equals the input in auto mode, derived in manual mode)
    list_lambda: Vec<f64>,       // sorted, only measurable (tof >= 0)
    list_tof: Vec<f64>,        // microseconds, same order
    largest_gaps_tof: Vec<f64>,
    largest_gaps_lambda: Vec<f64>,
    max_time_measurable: f64,  // microseconds
}

struct Step2Result {
    frames_s: Vec<[f64; 2]>,
    shutter_values_string: String,
    output_file_name: String,
}

fn parse_float_list(text: &str) -> Result<Vec<f64>> {
    let cleaned = text.trim().replace(',', " ");
    let mut values = Vec::new();
    for token in cleaned.split_whitespace() {
        values.push(
            token
                .parse::<f64>()
                .map_err(|_| anyhow!("'{token}' is not a valid number"))?,
        );
    }
    if values.is_empty() {
        return Err(anyhow!("the list is empty"));
    }
    Ok(values)
}

impl App {
    fn compute_step1(&self) -> Result<Step1Result> {
        let mut list_lambda = parse_float_list(&self.lambda_requested_text)?;
        list_lambda.sort_by(|a, b| a.partial_cmp(b).unwrap());

        let detector_offset = if self.detector_offset_is_manual {
            self.manual_detector_offset
        } else {
            physics::convert_lambda_into_offset(self.minimum_lambda_measurable, self.detector_sample_distance)
        };
        // lambda reaching the detector at TOF = 0; equals the input minimum lambda in auto mode
        let minimum_lambda_measurable =
            physics::from_tof_to_lambda(0.0, detector_offset, self.detector_sample_distance);

        // drop lambdas whose TOF falls below zero, like step1 does
        let mut list_tof = Vec::new();
        let mut kept_lambda = Vec::new();
        for &lambda in &list_lambda {
            let tof = physics::from_lambda_to_tof(lambda, detector_offset, self.detector_sample_distance);
            if tof >= 0.0 {
                list_tof.push(tof);
                kept_lambda.push(lambda);
            }
        }
        if kept_lambda.is_empty() {
            return Err(anyhow!(
                "all requested lambdas are below the minimum lambda measurable"
            ));
        }

        let largest_gaps_tof = physics::find_largest_gaps(&list_tof, NUMBER_OF_GAPS_TO_DISPLAY);
        let largest_gaps_lambda = physics::find_largest_gaps(&kept_lambda, NUMBER_OF_GAPS_TO_DISPLAY);
        let max_time_measurable = 1.0 / self.source_frequency * 1e6;

        Ok(Step1Result {
            detector_offset,
            minimum_lambda_measurable,
            list_lambda: kept_lambda,
            list_tof,
            largest_gaps_tof,
            largest_gaps_lambda,
            max_time_measurable,
        })
    }

    fn compute_step2(&self, step1: &Step1Result) -> Result<Step2Result> {
        let mut dead_times = parse_float_list(&self.dead_time_text)?;
        dead_times.sort_by(|a, b| a.partial_cmp(b).unwrap());

        let computation = shutter::compute_shutter_values(
            &dead_times,
            step1.detector_offset,
            self.detector_sample_distance,
            self.source_frequency,
            self.time_bin,
        )?;

        let output_file_name = format!(
            "ShutterValues_{:?}_hz_{}_micros.txt",
            self.source_frequency, step1.detector_offset as i64
        );

        Ok(Step2Result {
            frames_s: computation.frames_s,
            shutter_values_string: computation.shutter_values_string,
            output_file_name,
        })
    }
}

impl eframe::App for App {
    fn ui(&mut self, root: &mut egui::Ui, _frame: &mut eframe::Frame) {
        let step1 = self.compute_step1();
        let step2 = match &step1 {
            Ok(s1) => Some(self.compute_step2(s1)),
            Err(_) => None,
        };

        egui::Panel::top("steps").show_inside(root, |ui| {
            ui.horizontal(|ui| {
                ui.heading("Shutter Value Maker");
                ui.separator();
                ui.selectable_value(&mut self.step, Step::Gaps, "Step 1 — Gaps preview");
                ui.selectable_value(&mut self.step, Step::Frames, "Step 2 — Shutter frames");
                ui.selectable_value(&mut self.step, Step::WriteFile, "Step 3 — Write file");
                ui.separator();
                theme::toggle_button(ui);
            });
        });

        egui::Panel::left("inputs").min_size(330.0).show_inside(root, |ui| {
            if self.step != Step::WriteFile {
                egui::Panel::bottom("color_legend").show_inside(ui, |ui| {
                    show_color_legend(ui, self.step, self.gaps_axis);
                });
            }
            ui.add_space(6.0);
            ui.heading("Parameters");
            ui.add_space(6.0);

            egui::Grid::new("param_grid").num_columns(2).spacing([8.0, 8.0]).show(ui, |ui| {
                ui.label("Minimum lambda measurable (Å)");
                ui.add_enabled(
                    !self.detector_offset_is_manual,
                    egui::DragValue::new(&mut self.minimum_lambda_measurable).speed(0.01).range(0.0..=100.0),
                );
                ui.end_row();

                ui.label("Detector offset");
                ui.horizontal(|ui| {
                    ui.selectable_value(&mut self.detector_offset_is_manual, false, "auto");
                    ui.selectable_value(&mut self.detector_offset_is_manual, true, "manual");
                    if self.detector_offset_is_manual {
                        ui.add(
                            egui::DragValue::new(&mut self.manual_detector_offset)
                                .speed(10.0)
                                .range(0.0..=1e7)
                                .suffix(" µs"),
                        );
                    }
                });
                ui.end_row();

                ui.label("Detector-sample distance (m)");
                ui.add(egui::DragValue::new(&mut self.detector_sample_distance).speed(0.1).range(0.1..=100.0));
                ui.end_row();

                ui.label("Source frequency (Hz)");
                ui.horizontal(|ui| {
                    ui.selectable_value(&mut self.source_frequency, 60.0, "60");
                    ui.selectable_value(&mut self.source_frequency, 30.0, "30");
                });
                ui.end_row();

                ui.label("Time bin (µs)");
                ui.horizontal(|ui| {
                    ui.selectable_value(&mut self.time_bin, 5.12, "5.12");
                    ui.selectable_value(&mut self.time_bin, 10.24, "10.24");
                });
                ui.end_row();
            });

            ui.add_space(8.0);
            ui.label("List of lambda requested (Å):");
            ui.text_edit_singleline(&mut self.lambda_requested_text);

            ui.add_space(8.0);
            match &step1 {
                Ok(s1) => {
                    ui.label(
                        RichText::new(format!("detector offset = {:.0} µs", s1.detector_offset))
                            .strong()
                            .color(Color32::from_rgb(0, 140, 0)),
                    );
                    if self.detector_offset_is_manual {
                        ui.label(
                            RichText::new(format!(
                                "minimum lambda measurable = {:.2} Å",
                                s1.minimum_lambda_measurable
                            ))
                            .strong()
                            .color(Color32::from_rgb(0, 140, 0)),
                        );
                    }
                }
                Err(e) => {
                    ui.colored_label(Color32::RED, format!("Step 1 input error: {e}"));
                }
            }

            ui.separator();
            ui.label("Dead time values (Å):");
            ui.text_edit_singleline(&mut self.dead_time_text);
            if let Some(Err(e)) = &step2 {
                ui.colored_label(Color32::RED, format!("Step 2 error: {e}"));
            }

            ui.separator();
            ui.label("Output folder:");
            ui.horizontal(|ui| {
                ui.text_edit_singleline(&mut self.output_folder);
                if ui.button("Browse…").clicked() {
                    if let Some(folder) = rfd::FileDialog::new().pick_folder() {
                        self.output_folder = folder.display().to_string();
                    }
                }
            });

            if let Some(Ok(s2)) = &step2 {
                ui.add_space(4.0);
                ui.label(format!("File name: {}", s2.output_file_name));
                ui.add_space(4.0);
                if ui.button(RichText::new("Write shutter value file").strong()).clicked() {
                    let path = std::path::Path::new(&self.output_folder).join(&s2.output_file_name);
                    match std::fs::write(&path, &s2.shutter_values_string) {
                        Ok(()) => self.status = format!("Saved {}", path.display()),
                        Err(e) => self.status = format!("ERROR writing {}: {e}", path.display()),
                    }
                }
            }
            if !self.status.is_empty() {
                let color = if self.status.starts_with("ERROR") { Color32::RED } else { Color32::from_rgb(0, 140, 0) };
                ui.colored_label(color, &self.status);
            }
        });

        egui::CentralPanel::default().show_inside(root, |ui| match self.step {
            Step::Gaps => {
                if let Ok(s1) = &step1 {
                    ui.horizontal(|ui| {
                        ui.label("X-axis units:");
                        ui.selectable_value(&mut self.gaps_axis, XAxis::Tof, "TOF (µs)");
                        ui.selectable_value(&mut self.gaps_axis, XAxis::Lambda, "Lambda (Å)");
                    });
                    ui.add_space(4.0);
                    show_gaps_plots(ui, s1, self.detector_sample_distance, self.gaps_axis);
                } else {
                    ui.label("Fix the step 1 inputs to see the gaps preview.");
                }
            }
            Step::Frames => match (&step1, &step2) {
                (Ok(s1), Some(Ok(s2))) => {
                    ui.horizontal(|ui| {
                        ui.label("X-axis units:");
                        ui.selectable_value(&mut self.frames_axis, XAxis::Tof, "TOF (µs)");
                        ui.selectable_value(&mut self.frames_axis, XAxis::Lambda, "Lambda (Å)");
                    });
                    ui.add_space(4.0);
                    show_frames_plot(ui, s1, s2, self.detector_sample_distance, self.frames_axis);
                }
                _ => {
                    ui.label("Fix the inputs (lambda list and dead time values) to see the shutter frames preview.");
                }
            },
            Step::WriteFile => match &step2 {
                Some(Ok(s2)) => {
                    ui.heading("Shutter values file preview");
                    ui.add_space(6.0);
                    ui.label(format!("File name: {}", s2.output_file_name));
                    ui.add_space(6.0);
                    ui.label("Content (TOF start [s]  TOF end [s]  divided  time bin [µs]):");
                    ui.add_space(4.0);
                    egui::Frame::group(ui.style()).show(ui, |ui| {
                        ui.monospace(&s2.shutter_values_string);
                    });
                    ui.add_space(8.0);
                    ui.label("Use the 'Write shutter value file' button in the left panel to save it.");
                }
                _ => {
                    ui.label("Fix the inputs first (steps 1 and 2).");
                }
            },
        });
    }
}

/// one row of the color legend: a small color swatch followed by its explanation
fn legend_row(ui: &mut egui::Ui, color: Color32, text: &str) {
    ui.horizontal_top(|ui| {
        let (rect, _) = ui.allocate_exact_size(egui::vec2(14.0, 14.0), egui::Sense::hover());
        ui.painter().rect_filled(rect, 2.0, color);
        ui.add(egui::Label::new(text).wrap());
    });
}

/// explanation of the colors used in the plot of the current step
fn show_color_legend(ui: &mut egui::Ui, step: Step, gaps_axis: XAxis) {
    ui.add_space(6.0);
    ui.label(RichText::new("Plot colors").strong());
    ui.add_space(2.0);
    legend_row(ui, Color32::RED, "Red dots: the lambda requested (one dot per value, y is its index in the list).");
    match step {
        Step::Gaps => {
            let unit = match gaps_axis {
                XAxis::Tof => "TOF",
                XAxis::Lambda => "lambda",
            };
            legend_row(
                ui,
                gap_fill_color(0, NUMBER_OF_GAPS_TO_DISPLAY),
                "Green bands: the largest gaps between two consecutive requested values. The darker the green, the larger the gap.",
            );
            legend_row(
                ui,
                Color32::BLUE,
                "Blue dashed lines: center of each gap (value written at the top), a good candidate for a dead time position.",
            );
            legend_row(
                ui,
                Color32::BLACK,
                &format!("Black dotted line: minimum {unit} measurable. Black solid line: maximum {unit} measurable (end of the source frame)."),
            );
            legend_row(
                ui,
                Color32::from_rgba_unmultiplied(200, 0, 0, 80),
                "Light red band: not measurable, beyond the end of the source frame.",
            );
        }
        Step::Frames => {
            legend_row(
                ui,
                Color32::from_rgba_unmultiplied(0, 0, 220, 128),
                "Blue bands: the shutter frames (data are recorded there). Each successive frame is drawn darker; the white space between two frames is a dead time.",
            );
            legend_row(
                ui,
                Color32::from_rgba_unmultiplied(200, 0, 0, 80),
                "Light red band: not measurable, beyond the end of the source frame.",
            );
        }
        Step::WriteFile => {}
    }
    ui.add_space(6.0);
}

/// green span whose darkness reflects the gap rank (port of the alpha logic in step1)
fn gap_fill_color(rank: usize, total: usize) -> Color32 {
    let alpha = 1.0 - (rank as f32 + 1.0) / (total as f32 + 1.0);
    Color32::from_rgba_unmultiplied(0, 150, 0, (alpha * 160.0) as u8)
}

fn vspan(name: &str, left: f64, right: f64, y_max: f64, color: Color32) -> Polygon<'static> {
    let pts: PlotPoints = vec![
        [left, -0.5],
        [right, -0.5],
        [right, y_max],
        [left, y_max],
    ]
    .into();
    Polygon::new(name, pts)
        .fill_color(color)
        .stroke(egui::Stroke::NONE)
}

/// live readout of the cursor position, shown in the bottom-left corner of a plot
fn cursor_readout(axis: XAxis) -> CoordinatesFormatter<'static> {
    CoordinatesFormatter::new(move |p, _| match axis {
        XAxis::Tof => format!("TOF: {:.1} µs\nIndex: {:.2}", p.x, p.y),
        XAxis::Lambda => format!("Lambda: {:.4} Å\nIndex: {:.2}", p.x, p.y),
    })
}

fn show_gaps_plots(ui: &mut egui::Ui, s1: &Step1Result, distance: f64, axis: XAxis) {
    let y_max = s1.list_tof.len() as f64;
    let plot_height = ui.available_height() - 30.0;
    match axis {
        XAxis::Tof => show_gaps_plot_tof(ui, s1, distance, y_max, plot_height),
        XAxis::Lambda => show_gaps_plot_lambda(ui, s1, distance, y_max, plot_height),
    }
}

fn show_gaps_plot_tof(ui: &mut egui::Ui, s1: &Step1Result, distance: f64, y_max: f64, plot_height: f32) {
    ui.label(RichText::new("TOF with largest gaps highlighted (gap center position value displayed)").strong());
    let min_tof = physics::from_lambda_to_tof(s1.minimum_lambda_measurable, s1.detector_offset, distance);
    let x_max_tof = s1
        .list_tof
        .last()
        .copied()
        .unwrap_or(0.0)
        .max(s1.max_time_measurable)
        * 1.05;

    Plot::new("tof_plot")
        .height(plot_height)
        .legend(Legend::default())
        .x_axis_label("TOF (microseconds)")
        .y_axis_label("Index")
        .coordinates_formatter(Corner::LeftBottom, cursor_readout(XAxis::Tof))
        .show(ui, |plot_ui| {
            // gap spans + mid lines
            for w in s1.list_tof.windows(2) {
                let gap = w[1] - w[0];
                if let Some(rank) = s1.largest_gaps_tof.iter().position(|&g| g == gap) {
                    let mid = w[0] + gap / 2.0;
                    plot_ui.polygon(vspan(
                        "Gap area (darkness % to size)",
                        w[0],
                        w[1],
                        y_max,
                        gap_fill_color(rank, s1.largest_gaps_tof.len()),
                    ));
                    plot_ui.vline(
                        VLine::new("Mid value of gap", mid)
                            .color(Color32::BLUE)
                            .style(LineStyle::dashed_loose()),
                    );
                    plot_ui.text(Text::new("", PlotPoint::new(mid, y_max - 2.0), format!("{mid:.0}")));
                }
            }

            plot_ui.points(
                Points::new(
                    "lambda requested",
                    s1.list_tof
                        .iter()
                        .enumerate()
                        .map(|(i, &t)| [t, i as f64])
                        .collect::<Vec<_>>(),
                )
                .color(Color32::RED)
                .shape(MarkerShape::Circle)
                .radius(4.0),
            );

            plot_ui.vline(
                VLine::new("Minimum TOF measurable", min_tof)
                    .color(Color32::BLACK)
                    .style(LineStyle::dotted_dense()),
            );
            plot_ui.vline(
                VLine::new("Maximum TOF measurable", s1.max_time_measurable).color(Color32::BLACK),
            );
            if x_max_tof > s1.max_time_measurable {
                plot_ui.polygon(vspan(
                    "Not measurable area",
                    s1.max_time_measurable,
                    x_max_tof,
                    y_max,
                    Color32::from_rgba_unmultiplied(200, 0, 0, 80),
                ));
            }
        });
}

fn show_gaps_plot_lambda(ui: &mut egui::Ui, s1: &Step1Result, distance: f64, y_max: f64, plot_height: f32) {
    ui.label(RichText::new("Bragg peaks with largest gaps highlighted (gap center position value displayed)").strong());
    let minimum_lambda = s1.minimum_lambda_measurable;
    let last_lambda_measurable =
        physics::from_tof_to_lambda(s1.max_time_measurable, s1.detector_offset, distance);
    let x_max_lambda = s1
        .list_lambda
        .last()
        .copied()
        .unwrap_or(0.0)
        .max(last_lambda_measurable)
        * 1.05;

    Plot::new("lambda_plot")
        .height(plot_height)
        .legend(Legend::default())
        .x_axis_label("Bragg peaks (Angstrom)")
        .y_axis_label("Index")
        .coordinates_formatter(Corner::LeftBottom, cursor_readout(XAxis::Lambda))
        .show(ui, |plot_ui| {
            for w in s1.list_lambda.windows(2) {
                let gap = w[1] - w[0];
                if let Some(rank) = s1.largest_gaps_lambda.iter().position(|&g| g == gap) {
                    let mid = w[0] + gap / 2.0;
                    plot_ui.polygon(vspan(
                        "Gap area (darkness % to size)",
                        w[0],
                        w[1],
                        y_max,
                        gap_fill_color(rank, s1.largest_gaps_lambda.len()),
                    ));
                    plot_ui.vline(
                        VLine::new("Mid value of gap", mid)
                            .color(Color32::BLUE)
                            .style(LineStyle::dashed_loose()),
                    );
                    plot_ui.text(Text::new("", PlotPoint::new(mid, y_max - 2.0), format!("{mid:.2}")));
                }
            }

            plot_ui.points(
                Points::new(
                    "lambda requested",
                    s1.list_lambda
                        .iter()
                        .enumerate()
                        .map(|(i, &l)| [l, i as f64])
                        .collect::<Vec<_>>(),
                )
                .color(Color32::RED)
                .shape(MarkerShape::Circle)
                .radius(4.0),
            );

            plot_ui.vline(
                VLine::new("Minimum lambda measurable", minimum_lambda)
                    .color(Color32::BLACK)
                    .style(LineStyle::dotted_dense()),
            );
            plot_ui.text(Text::new(
                "",
                PlotPoint::new(minimum_lambda, y_max - 2.0),
                format!("{minimum_lambda:.2}"),
            ));
            plot_ui.vline(
                VLine::new("Maximum lambda measurable", last_lambda_measurable).color(Color32::BLACK),
            );
            if x_max_lambda > last_lambda_measurable {
                plot_ui.polygon(vspan(
                    "Not measurable area",
                    last_lambda_measurable,
                    x_max_lambda,
                    y_max,
                    Color32::from_rgba_unmultiplied(200, 0, 0, 80),
                ));
            }
        });
}

fn show_frames_plot(ui: &mut egui::Ui, s1: &Step1Result, s2: &Step2Result, distance: f64, axis: XAxis) {
    ui.label(RichText::new("Preview of TimeSpectra file — shutter values gaps and frames").strong());

    // map a TOF (µs) onto the selected x-axis; from_tof_to_lambda is linear
    // and increasing, so spans and maxima keep their order after conversion
    let to_x = |tof_us: f64| match axis {
        XAxis::Tof => tof_us,
        XAxis::Lambda => physics::from_tof_to_lambda(tof_us, s1.detector_offset, distance),
    };
    let x_axis_label = match axis {
        XAxis::Tof => "TOF (microseconds)",
        XAxis::Lambda => "Bragg peaks (Angstrom)",
    };

    let y_max = s1.list_tof.len() as f64;
    let max_measurable_x = to_x(s1.max_time_measurable);
    let x_max = to_x(s1
        .list_tof
        .last()
        .copied()
        .unwrap_or(0.0)
        .max(s1.max_time_measurable)
        .max(s2.frames_s.last().map(|f| f[1] * 1e6).unwrap_or(0.0)))
        * 1.05;

    Plot::new("frames_plot")
        .height(ui.available_height() - 140.0)
        .legend(Legend::default())
        .x_axis_label(x_axis_label)
        .y_axis_label("Index")
        .coordinates_formatter(Corner::LeftBottom, cursor_readout(axis))
        .show(ui, |plot_ui| {
            let mut alpha = 0.1f32;
            for frame in &s2.frames_s {
                let left = to_x(frame[0] * 1e6);
                let right = to_x(frame[1] * 1e6);
                plot_ui.polygon(vspan(
                    "Shutter frame",
                    left,
                    right,
                    y_max,
                    Color32::from_rgba_unmultiplied(0, 0, 220, (alpha * 255.0).min(255.0) as u8),
                ));
                alpha += 0.1;
            }

            plot_ui.points(
                Points::new(
                    "lambda requested",
                    s1.list_tof
                        .iter()
                        .enumerate()
                        .map(|(i, &t)| [to_x(t), i as f64])
                        .collect::<Vec<_>>(),
                )
                .color(Color32::RED)
                .shape(MarkerShape::Circle)
                .radius(4.0),
            );

            if x_max > max_measurable_x {
                plot_ui.polygon(vspan(
                    "Not measurable range",
                    max_measurable_x,
                    x_max,
                    y_max,
                    Color32::from_rgba_unmultiplied(200, 0, 0, 80),
                ));
            }
        });

    ui.add_space(6.0);
    ui.label("Shutter values:");
    egui::Frame::group(ui.style()).show(ui, |ui| {
        ui.monospace(&s2.shutter_values_string);
    });
}
