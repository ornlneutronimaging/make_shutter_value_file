# Shutter Value Maker (Rust)

Single-window GUI that replaces the three Python scripts
`create_shutter_value_file_step1/2/3.py`. All inputs are live: every plot and the
output file preview update instantly as you edit a value — no more running three
scripts in sequence, and no `~/.shutter_value_parameters.json` hand-off file.

## Run

```bash
./launch_shutter_value_maker.sh
```

(needs a graphical session, e.g. ThinLinc; rebuilds automatically if sources changed)

## The three steps

- **Step 1 — Gaps preview**: enter minimum lambda measurable, detector-sample
  distance, source frequency (30/60 Hz), time bin (5.12/10.24 µs) and the list of
  requested Bragg peaks. Shows the TOF-scale and Angstrom-scale plots with the 5
  largest gaps highlighted (darkness proportional to gap size), gap mid-values, and
  the measurable range. The computed detector offset is shown in the left panel.
- **Step 2 — Shutter frames**: enter the dead-time lambdas (≥ 2 values, ≥ 0.3 Å
  apart). Shows the shutter frames overlaid on the requested peaks, plus the
  shutter-values table.
- **Step 3 — Write file**: preview of the file content, then use
  *Write shutter value file* to save `ShutterValues_<freq>_hz_<offset>_micros.txt`
  in the chosen output folder (same name and format as the Python version).

## Windows package

Cross-compile from this Linux machine (needs `cargo-xwin`, already installed):

```bash
cargo xwin build --release --target x86_64-pc-windows-msvc
```

Then refresh `package/ShutterValueMaker_windows_x64.zip` (self-contained exe +
README, no runtime needed on Windows):

```bash
cd package
cp ../target/x86_64-pc-windows-msvc/release/shutter_value_maker.exe ShutterValueMaker.exe
zip -9 ShutterValueMaker_windows_x64.zip ShutterValueMaker.exe README_WINDOWS.txt
```

## Physics parity with the Python code

- `src/physics.rs` ports the step1 utility functions (rounded 0.3956 coefficient).
- `src/shutter.rs` ports `shutter_value_generator/make_shutter_value_file.py`
  (exact h/m_n coefficient, 30/60 Hz TOF frames, 0.4 ms inter-frame dead time,
  embedded `clock_cycle.txt` table).
- `cargo test` includes a test asserting the frames match the Python library's
  output for the default parameters bit-for-bit (tolerance 1e-12 s).
