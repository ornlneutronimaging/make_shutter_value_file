Shutter Value Maker (Windows)
=============================

Double-click ShutterValueMaker.exe to start. No installation needed — the
executable is fully self-contained (no DLLs, no Python, no runtime to install).

The first time you run it, Windows SmartScreen may show "Windows protected
your PC" because the exe is not code-signed: click "More info" then
"Run anyway".

What it does
------------
Single-window replacement for the three VENUS Python scripts
(create_shutter_value_file_step1/2/3.py):

  Step 1 - Gaps preview   : enter minimum lambda measurable, detector-sample
                            distance, source frequency (30/60 Hz), time bin
                            (5.12/10.24 us) and the list of requested Bragg
                            peaks. The plot shows the 5 largest gaps and the
                            measurable range; switch the x-axis between TOF
                            (us) and lambda (Angstroms) with the toggle above
                            the plot. The detector offset is computed from the
                            minimum lambda ("auto") or can be typed in
                            directly in us ("manual").
  Step 2 - Shutter frames : enter the dead-time lambdas (>= 2 values,
                            >= 0.3 Angstroms apart); preview the shutter
                            frames and the shutter-values table, with the
                            same TOF/lambda x-axis toggle.
  Step 3 - Write file     : writes ShutterValues_<freq>_hz_<offset>_micros.txt
                            to the folder you choose (use the Browse button).

Everything updates live as you type - there is no "compute" button to press.

Requirements: 64-bit Windows 10/11.
