//! Port of shutter_value_generator/make_shutter_value_file.py (the parts used by
//! the step1/step2/step3 scripts).

use anyhow::{bail, Result};

// h / m_n * 1e6 — same constant the Python library computes
pub const COEFF: f64 = (6.626_070_04e-34 / 1.674_927_471e-27) * 1e6;

// The step1 script uses the rounded value 0.3956 for its conversions; kept
// separate so the displayed detector offset matches the Python output exactly.
pub const COEFF_STEP1: f64 = 0.3956;

pub const TOF_FRAMES_60HZ: [[f64; 2]; 3] = [[1e-6, 2.5e-3], [2.9e-3, 5.8e-3], [6.2e-3, 15.9e-3]];

pub const TOF_FRAMES_30HZ: [[f64; 2]; 5] = [
    [1e-6, 2.5e-3],
    [2.9e-3, 5.8e-3],
    [6.2e-3, 15.9e-3],
    [16.3e-3, 25.9e-3],
    [26.3e-3, 31.8e-3],
];

pub const MIN_TOF_BETWEEN_FRAMES: f64 = 2.9e-3 - 2.5e-3; // s
pub const MIN_LAMBDA_PEAK_VALUE_INTERVAL: f64 = 0.3; // Angstroms

// clock_cycle.txt: (Clock, Divided)
pub const CLOCK_CYCLE_TABLE: &[(f64, i64)] = &[
    (100.0, 0),
    (50.0, 1),
    (25.0, 2),
    (12.5, 3),
    (6.25, 4),
    (3.125, 5),
    (1.5625, 6),
    (0.78125, 7),
    (0.390625, 8),
    (0.195313, 9),
    (0.097656, 10),
    (0.048828, 11),
    (0.024414, 12),
    (0.012207, 13),
    (0.006104, 14),
    (0.003052, 15),
    (0.001526, 16),
    (0.000763, 17),
    (0.000382, 18),
    (0.000191, 19),
];

pub fn tof_frames(source_frequency: f64) -> &'static [[f64; 2]] {
    if source_frequency == 60.0 {
        &TOF_FRAMES_60HZ
    } else {
        &TOF_FRAMES_30HZ
    }
}

/// lambda (Angstroms) -> TOF, library version (COEFF), in seconds
pub fn lambda_to_tof_s(lambda: f64, detector_offset_us: f64, detector_sample_distance_m: f64) -> f64 {
    (lambda * (detector_sample_distance_m * 100.0) / COEFF - detector_offset_us) * 1e-6
}

/// last clock-table row whose Clock value is >= delta_tof (ms); -1 when none
pub fn get_above_closest_divided(delta_tof_s: f64) -> i64 {
    let delta_tof_ms = delta_tof_s * 1e3;
    CLOCK_CYCLE_TABLE
        .iter()
        .rev()
        .find(|(clock, _)| delta_tof_ms <= *clock)
        .map(|(_, divided)| *divided)
        .unwrap_or(-1)
}

pub fn list_lambda_dead_time_too_close(list_lambda_dead_time: &[f64]) -> bool {
    list_lambda_dead_time
        .windows(2)
        .any(|w| w[1] - w[0] <= MIN_LAMBDA_PEAK_VALUE_INTERVAL)
}

/// Faithful port of MakeShutterValueFile.make_list_tof_frames (dead times in s)
pub fn make_list_tof_frames(list_tof_dead_time: &[f64], source_frequency: f64) -> Vec<[f64; 2]> {
    let frames = tof_frames(source_frequency);
    let mut list_tof_frames: Vec<[f64; 2]> = Vec::new();

    for (index, &tof_dead_time) in list_tof_dead_time.iter().enumerate() {
        if index == 0 {
            let left = frames[0][0];
            let right = tof_dead_time - MIN_TOF_BETWEEN_FRAMES;
            list_tof_frames.push([left, right]);
        }

        if index == list_tof_dead_time.len() - 1 {
            let left = tof_dead_time + MIN_TOF_BETWEEN_FRAMES;
            let right = frames[frames.len() - 1][1];
            if left > right {
                break;
            }
            list_tof_frames.push([left, right]);
            break;
        }

        let left = tof_dead_time + MIN_TOF_BETWEEN_FRAMES;
        let right = list_tof_dead_time[index + 1] - MIN_TOF_BETWEEN_FRAMES;
        list_tof_frames.push([left, right]);
    }
    list_tof_frames
}

/// Format an f64 the way Python's str() does, so the written file is
/// byte-identical to the Python version: shortest round-trip digits, fixed
/// notation for exponents in [-4, 16), otherwise scientific with a signed
/// two-digit exponent ("1e-06").
pub fn python_float_repr(value: f64) -> String {
    if value == 0.0 {
        return if value.is_sign_negative() { "-0.0".into() } else { "0.0".into() };
    }
    if !value.is_finite() {
        return if value.is_nan() {
            "nan".into()
        } else if value > 0.0 {
            "inf".into()
        } else {
            "-inf".into()
        };
    }
    let sci = format!("{value:e}"); // shortest mantissa, e.g. "1e-6"
    let (mantissa, exp) = sci.split_once('e').unwrap();
    let exp: i32 = exp.parse().unwrap();
    if (-4..16).contains(&exp) {
        let fixed = format!("{value}");
        if fixed.contains('.') {
            fixed
        } else {
            format!("{fixed}.0")
        }
    } else {
        format!("{}e{}{:02}", mantissa, if exp < 0 { '-' } else { '+' }, exp.abs())
    }
}

pub fn make_shutter_values_string(list_tof_frames: &[[f64; 2]], time_bin: f64) -> String {
    list_tof_frames
        .iter()
        .map(|frame| {
            let divided = get_above_closest_divided(frame[1] - frame[0]);
            format!(
                "{}\t{}\t{}\t{}",
                python_float_repr(frame[0]),
                python_float_repr(frame[1]),
                divided,
                python_float_repr(time_bin)
            )
        })
        .collect::<Vec<_>>()
        .join("\n")
}

pub struct ShutterComputation {
    pub frames_s: Vec<[f64; 2]>,
    pub shutter_values_string: String,
}

/// Equivalent of MakeShutterValueFile(...).run(list_lambda_dead_time=...) for the
/// non-resonance, non-default path used by step2/step3.
pub fn compute_shutter_values(
    list_lambda_dead_time: &[f64],
    detector_offset_us: f64,
    detector_sample_distance_m: f64,
    source_frequency: f64,
    time_bin: f64,
) -> Result<ShutterComputation> {
    if list_lambda_dead_time.len() < 2 {
        bail!("list of lambda dead time should contain at least 2 values!");
    }
    if list_lambda_dead_time_too_close(list_lambda_dead_time) {
        bail!(
            "Make sure the list of lambda dead time are at least {} Angstroms from each other",
            MIN_LAMBDA_PEAK_VALUE_INTERVAL
        );
    }

    let list_tof_dead_time_s: Vec<f64> = list_lambda_dead_time
        .iter()
        .map(|&l| lambda_to_tof_s(l, detector_offset_us, detector_sample_distance_m))
        .collect();

    let frames_s = make_list_tof_frames(&list_tof_dead_time_s, source_frequency);
    let shutter_values_string = make_shutter_values_string(&frames_s, time_bin);

    Ok(ShutterComputation {
        frames_s,
        shutter_values_string,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn divided_matches_clock_table() {
        // frame width 2.499 ms -> clocks >= 2.499 end at 3.125 (Divided 5)
        assert_eq!(get_above_closest_divided(2.499e-3), 5);
        // 9.7 ms -> 12.5 (Divided 3)
        assert_eq!(get_above_closest_divided(9.7e-3), 3);
        // wider than 100 ms clock -> everything matches down to first row? no: none match
        assert_eq!(get_above_closest_divided(0.2), -1);
    }

    #[test]
    fn frames_for_two_dead_times() {
        // 60 Hz, two dead times at 3 ms and 8 ms
        let frames = make_list_tof_frames(&[3e-3, 8e-3], 60.0);
        assert_eq!(frames.len(), 3);
        assert!((frames[0][0] - 1e-6).abs() < 1e-12);
        assert!((frames[0][1] - (3e-3 - 0.4e-3)).abs() < 1e-12);
        assert!((frames[1][0] - (3e-3 + 0.4e-3)).abs() < 1e-12);
        assert!((frames[1][1] - (8e-3 - 0.4e-3)).abs() < 1e-12);
        assert!((frames[2][1] - 15.9e-3).abs() < 1e-12);
    }

    #[test]
    fn matches_python_reference_output() {
        // Reference produced by the Python library with the step1/step2 defaults:
        // min lambda 1.9 A, distance 25 m, 60 Hz, time bin 5.12, dead times [2.95, 3.60]
        let detector_offset = 1.9 * 2500.0 / 0.3956;
        let result = compute_shutter_values(&[2.95, 3.60], detector_offset, 25.0, 60.0, 5.12).unwrap();

        let expected_frames = [
            [1e-6, 0.0062353301230534345],
            [0.007035330123053433, 0.01034297933886975],
            [0.011142979338869749, 0.0159],
        ];
        assert_eq!(result.frames_s.len(), expected_frames.len());
        for (frame, expected) in result.frames_s.iter().zip(expected_frames.iter()) {
            assert!((frame[0] - expected[0]).abs() < 1e-12);
            assert!((frame[1] - expected[1]).abs() < 1e-12);
        }
        for line in result.shutter_values_string.lines() {
            let cols: Vec<&str> = line.split('\t').collect();
            assert_eq!(cols[2], "4");
            assert_eq!(cols[3], "5.12");
        }
    }

    #[test]
    fn float_repr_matches_python_str() {
        assert_eq!(python_float_repr(1e-6), "1e-06");
        assert_eq!(python_float_repr(1.5e-6), "1.5e-06");
        assert_eq!(python_float_repr(1e-4), "0.0001");
        assert_eq!(python_float_repr(1e-5), "1e-05");
        assert_eq!(python_float_repr(0.0159), "0.0159");
        assert_eq!(python_float_repr(5.12), "5.12");
        assert_eq!(python_float_repr(10.24), "10.24");
        assert_eq!(python_float_repr(0.0), "0.0");
        assert_eq!(python_float_repr(1e15), "1000000000000000.0");
        assert_eq!(python_float_repr(1e16), "1e+16");
        assert_eq!(python_float_repr(-2.5e-3), "-0.0025");
    }

    #[test]
    fn file_content_is_byte_identical_to_python() {
        // Reference bytes produced by running the Python library directly:
        //   MakeShutterValueFile(detector_sample_distance=25.0, detector_offset=1.9*2500/0.3956,
        //                        source_frequency=60.0, time_bin=5.12, ...)
        //       .run(list_lambda_dead_time=[2.95, 3.60])
        let detector_offset = 1.9 * 2500.0 / 0.3956;
        let result = compute_shutter_values(&[2.95, 3.60], detector_offset, 25.0, 60.0, 5.12).unwrap();
        let expected = "1e-06\t0.0062353301230534345\t4\t5.12\n\
                        0.007035330123053433\t0.01034297933886975\t4\t5.12\n\
                        0.011142979338869749\t0.0159\t4\t5.12";
        assert_eq!(result.shutter_values_string, expected);
    }

    #[test]
    fn file_content_is_byte_identical_to_python_30hz() {
        // Reference bytes from the Python library: distance 23 m, offset from
        // 2.5 A, 30 Hz, time bin 10.24, dead times [3.1, 4.2, 6.0]
        let detector_offset = 2.5 * 2300.0 / 0.3956;
        let result =
            compute_shutter_values(&[3.1, 4.2, 6.0], detector_offset, 23.0, 30.0, 10.24).unwrap();
        let expected = "1e-06\t0.0030882171460053652\t5\t10.24\n\
                        0.0038882171460053647\t0.009483511002014774\t4\t10.24\n\
                        0.010283511002014772\t0.01994853731184834\t3\t10.24\n\
                        0.020748537311848343\t0.0318\t3\t10.24";
        assert_eq!(result.shutter_values_string, expected);
    }

    #[test]
    fn dead_time_spacing_check() {
        assert!(list_lambda_dead_time_too_close(&[2.0, 2.2]));
        assert!(!list_lambda_dead_time_too_close(&[2.0, 2.5]));
    }
}
