********
Tutorial
********

This library allows you to create the ShutterValue.txt file the MCP detector needs.

A few parameters must be provided to the command line in order to produce that file.

In order to see the list of arguments required, simply type

.. code-block:: html

    > python make_shutter_value_file --help
    usage: make_shutter_value_file.py [-h] [--verbose]
                                      [--output_folder OUTPUT_FOLDER]
                                      [--detector_sample_distance DETECTOR_SAMPLE_DISTANCE]
                                      [--detector_offset DETECTOR_OFFSET]
                                      [--resonance_mode RESONANCE_MODE]
                                      [--default_mode DEFAULT_MODE]
                                      epics_chopper_wavelength_range
                                      list_wavelength_dead_time

    Generate ShutterValue.txt file used by the MCP detector

    optional arguments:
      -h, --help            show this help message and exit
      --verbose, -v         display resulting shutter value file
      --epics_chopper_wavelength_range
                            left,right wavelength range defined by the choppers
      --list_wavelength_dead_time
                            Comma separated list of wavelength that do not have
                            any bragg edges of interest
      --output_folder OUTPUT_FOLDER
                            output folder where the ShutterValue.txt file will be
                            created
      --detector_sample_distance DETECTOR_SAMPLE_DISTANCE
                            Distance detector to sample in m
      --detector_offset DETECTOR_OFFSET
                            Detector offset in micro seconds
      --resonance_mode RESONANCE_MODE
                            Generate shutter value in resonance mode
      --default_mode DEFAULT_MODE
                            Generate default shutter value file


Some of the arguments have default values but **you must provide** a *comma separated range of EPICS chopper
wavength range* and a *comma separated list of wavelength of dead time*


EPICS chopper wavelength range (Angstroms)
==========================================

This comma separated argument (ex: 1,20) represents the range of lambda the chopper are set up. No lambda outside that
range won't be able to be measure.

*Example*:
1,20


List of wavelength dead time (Angstroms)
========================================

This comma separated argument (ex: 3, 5, 8) represents a list of wavelength the program can use to **pause** the
MCP detector. Once defined, the program will set a short interval (0.3A) around that value to pause the MCP detector.
Due to the profile of the input beam, make sure you define a dead time in the first 1/3 part of the beam. At least 2
lambda dead time must be provided!

*Example*:
2,4,8


Verbose
=======

If this flag is provided (--verbose, or -v) the contain of the output file will be displayed in the command line


Output folder
=============

Where to create the ShutterValue.txt file. The current location is used by default


Detector sample distance (m)
============================

The distance in m between the detector and the sample. Default value being 13m


Detector offset (micros)
========================

The offset used by the MCP detector in micros. Default value of 6500micros is used


Resonance mode
==============

If that flag is turned on (--resonance_mode True), the ShutterValue.txt file will be automatically produced using
the resonance mode as followed

.. code-block:: html

    1e-6    320e-6  3   0.16


Default mode
============

If that flag is turned on (--default_mode True), the default ShutterValue.txt file will be produced as followed

.. code-block:: html

    1e-6    2.5e-3  5   10.24
    2.9e-3  5.8e-3  6   10.24
    6.2e-3  15.9e-3 7   10.24









