import argparse
import numpy as np
from shutter_value_generator.make_shutter_value_file import MakeShutterValueFile

parser = argparse.ArgumentParser(description="Generate ShutterValue.txt file used by the MCP detector")
parser.add_argument('--verbose', '-v', default=0, action='count',
                    help='display resulting shutter value file')
parser.add_argument('--output_folder', default='./', help='output folder where the ShutterValue.txt file will be '
                                                         'created')
parser.add_argument('--epics_chopper_wavelength_range',
                    help='left,right wavelength range defined by the choppers')
parser.add_argument('--list_wavelength_dead_time',
                    default=None,
                    help='Comma separated list of wavelength that do not have any bragg edges of interest')
parser.add_argument('--detector_sample_distance',
                    default=13,
                    help='Distance detector to sample in m',
                    type=float)
parser.add_argument('--detector_offset',
                    default=6500,
                    help='Detector offset in micro seconds',
                    type=float)
parser.add_argument('--resonance_mode', '-r',
                    default=0,
                    action='count',
                    help='Generate shutter value in resonance mode')
parser.add_argument('--default_mode', '-d',
                    default=0,
                    action='count',
                    help='Generate default shutter value file')

args = parser.parse_args()

output_folder = args.output_folder
detector_sample_distance = args.detector_sample_distance
detector_offset = args.detector_offset
resonance_mode = args.resonance_mode
default_mode = args.default_mode
epics_chopper_wavelength_range = args.epics_chopper_wavelength_range
list_wavelength_dead_time = args.list_wavelength_dead_time
if args.verbose == 0:
    verbose = False
else:
    verbose = True

resonance_mode = True if args.resonance_mode else False
default_mode = True if args.default_mode else False

if epics_chopper_wavelength_range:
    epics_chopper_wavelength_range = epics_chopper_wavelength_range.split(",")
else:
    epics_chopper_wavelength_range = None

if epics_chopper_wavelength_range:
    epics_chopper_wavelength_range = [np.float32(_value) for _value in
                                                                    epics_chopper_wavelength_range]
else:
    epics_chopper_wavelength_range = None

if list_wavelength_dead_time:
	list_wavelength_dead_time = list_wavelength_dead_time.split(",")
	list_wavelength_dead_time = [np.float32(_value) for _value in list_wavelength_dead_time]

o_make = MakeShutterValueFile(output_folder=output_folder,
                              detector_sample_distance=detector_sample_distance,
                              detector_offset=detector_offset,
                              resonance_mode=resonance_mode,
                              default_mode=default_mode,
                              epics_chopper_wavelength_range=epics_chopper_wavelength_range,
                              verbose=verbose)
o_make.run(list_lambda_dead_time=list_wavelength_dead_time)
