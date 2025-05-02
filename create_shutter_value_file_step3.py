import click
import numpy as np
import os
import json

from shutter_value_generator import make_shutter_value_file

output_folder = click.prompt("Enter the output folder ", type=str, default="./")
output_file_name = click.prompt("Enter the output file name ", type=str, default="ShutterValues.txt")

# load config file created in step1
home_dir = os.path.expanduser("~")
json_file = os.path.join(home_dir, ".shutter_value_parameters.json")
if os.path.exists(json_file):
    with open(json_file, 'r') as f:
        config = json.load(f)

if not config:
    print("No config file found. Please run step1 first.")
    exit(1)

# load parameters
detector_offset = config['detector_offset']
detector_sample_distance = config['detector_sample_distance']
minimum_lambda_measurable = config['minimum_lambda_measurable']
time_bin = config['time_bin']
list_lambda_requested = config['list_lambda_requested']
combine_list_tof = config['combine_list_tof']
combine_list = config['combine_list']
largest_gaps = config['largest_gaps']
largest_gaps_lambda = config['largest_gaps_lambda']
mid_values = config['mid_values']
mid_values_lambda = config['mid_values_lambda']
dead_time_values = config['dead_time_values']
source_frequency = config['source_frequency']

# main script

o_shutter_value = make_shutter_value_file.MakeShutterValueFile(detector_sample_distance=detector_sample_distance,
                                                              detector_offset=detector_offset,
                                                              source_frequency=source_frequency,
                                                              output_folder=output_folder,
                                                              output_file_name=output_file_name,
                                                              verbose=True,
                                                              time_bin=time_bin,
                                                              no_output_file=False,
                                                              epics_chopper_wavelength_range=[minimum_lambda_measurable, 
                                                                                            np.array(list_lambda_requested).max()],
                                                            )

shutter_values = o_shutter_value.run(list_lambda_dead_time=dead_time_values)

print()

# remove the temporary file
if os.path.exists(json_file):
    os.remove(json_file)
