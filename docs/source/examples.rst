********
Examples
********

This page list a few cases

To create the default ShutterValue.txt file
-------------------------------------------

.. code-block:: html

    > python make_shutter_value_file --default_mode --verbose
    1e-6	2.5e-3	5	10.24
    2.9e-3	5.8e-3	6	10.24
    6.2e-3	15.9e-3	7	10.24

    > python make_shutter_value_file --default_mode True

In both cases, a file *ShutterValue.txt* was created in the current folder (./)

To create the ShutterValue.txt file for resonances experiments
--------------------------------------------------------------

.. code-block:: html

    > python make_shutter_value_file --resonance_mode --verbose
    1e-6	320e-6	3	0.16

    > python make_shutter_value_file --resonance_mode

In both cases, a file *ShutterValue.txt* was created in the current folder (./)

To define a new output location
-------------------------------

.. code-block:: html

    > python make_shutter_value_file --default_mode --output /SNS/users/Neymar

The ShutterValue.txt will be created in the output folder */SNS/users/Neymar*

To create a ShutterValue.txt file for a pre-defined setup
---------------------------------------------------------

In this configuration, we are telling the prograg that the choppers will produce lambda between 0.5 and 30
Angstroms and that we know for sure, that we don't have, or don't want to measure, lambda at the 3, 5 and 8
Angstroms position. The program will use those values to set a pause in the MCP detector.

.. code-block:: html

    > python make_shutter_value_file.py --list_wavelength_dead_time 3,5,8 --epics_chopper_wavelength_range 0.5,30 --verbose
    1e-06	0.002958358117959164	5	10.24
    0.0037583581179591635	0.009530596863265274	4	10.24
    0.010330596863265273	0.019388954981224435	3	10.24
    0.020188954981224437	0.0159	19	10.24

To customize the experiment setup
---------------------------------

In this case, we want to change the **detector offset** to use 6600 micros and
the **detector to sample distance** to use 22.5m.

.. code-block:: html

    > python make_shutter_value_file.py --list_wavelength_dead_time 3,5,8 --epics_chopper_wavelength_range 0.5,30 --detector_sample_distance 22.5 --detector_offset 6600 --verbose
    1e-06	0.010062542896467784	3	10.24
    0.010862542896467783	0.021437571494112972	3	10.24
    0.022237571494112974	0.03850011439058076	2	10.24
    0.03930011439058075	0.0159	19	10.24




