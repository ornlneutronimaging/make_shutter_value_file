import click
import numpy as np
import matplotlib.pyplot as plt
import os
import json

from shutter_value_generator import make_shutter_value_file

# load config file created in step1
home_dir = os.path.expanduser("~")
json_file = os.path.join(home_dir, ".shutter_value_parameters.json")
if os.path.exists(json_file):
    with open(json_file, 'r') as f:
        config = json.load(f)

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

# main script
dead_time_value = click.prompt("Enter the dead time values (in Angstroms) (ex: 2.95 5.15)", 
                               type=str, 
                               default="2.95 3.60")
dead_time_values = dead_time_value.strip()
if "," in dead_time_values:
    dead_time_values = dead_time_values.replace(",", " ")
dead_time_values = dead_time_values.split(" ")
dead_time_values = [float(x) for x in dead_time_values]

o_shutter_value = make_shutter_value_file.MakeShutterValueFile(detector_sample_distance=detector_sample_distance,
                                                              detector_offset=detector_offset,
                                                              output_folder="",
                                                              verbose=True,
                                                              time_bin=time_bin,
                                                              no_output_file=True,
                                                              epics_chopper_wavelength_range=[minimum_lambda_measurable, 
                                                                                            np.array(list_lambda_requested).max()],
                                                            )

shutter_values = o_shutter_value.run(list_lambda_dead_time=dead_time_values)

# plot in TOF scale this time

fig3, axs3 = plt.subplots(1, 1, figsize=(10, 8), num='Shutter values gaps and frames')

axs3.plot(combine_list_tof, np.arange(len(combine_list)), 'ro', label='list_shutter_requested1')
axs3.set_xlabel('TOF (microseconds)')
axs3.set_title('Preview of TimeSpectra file')
plt.tight_layout()

# for left_value, right_value in zip(combine_list_tof[:-1], combine_list_tof[1:]):
#     gap_value = (right_value - left_value)
#     if gap_value in largest_gaps:
#         mid_value = calculate_mid_value(gap_value)
#         # plt.axvline(x=mid_value+left_value, color='b', linestyle='--', label='Mid value of gap')
        # plt.text(mid_value+left_value, len(combine_list)-2, f'{mid_value+left_value:.0f}', rotation=45, verticalalignment='bottom')
        # plt.text(mid_value, 0, f'{mid_value:.2f}', rotation=90, verticalalignment='bottom')

        # index = np.where(np.array(largest_gaps) == gap_value)[0][0]
        # alpha_index = 1-(index+1)/(len(largest_gaps)+1)
        # plt.axvspan(left_value, right_value, color='green', alpha=alpha_index, label='Gap area')

index = 0.1
for left_value, right_value in o_shutter_value.final_list_tof_frames:
    left_value_micros = left_value * 1e6
    right_value_micros = right_value * 1e6
    
    axs3.axvspan(left_value_micros, right_value_micros, color='blue', alpha=index, label='Shutter value')
    index += 0.1

axs3.axvspan(1/60 * 1e6, combine_list_tof[-1], color='red', hatch="/", alpha=0.5, label='Not measurable area')

# create new temporary file for step3 (create the shutter value file)
# save the parameters defined by the user to be used in the next step
json_dict = {'detector_offset': detector_offset,
            'detector_sample_distance': detector_sample_distance,
            'minimum_lambda_measurable': minimum_lambda_measurable,
            'time_bin': time_bin,
            'list_lambda_requested': list_lambda_requested,
            'combine_list_tof': combine_list_tof,
            'combine_list': combine_list,
            'largest_gaps': largest_gaps,
            'largest_gaps_lambda': largest_gaps_lambda,
            'mid_values': mid_values,
            'mid_values_lambda': mid_values_lambda,
            'dead_time_values': dead_time_values,
            }

home_dir = os.path.expanduser("~")
json_file = os.path.join(home_dir, ".shutter_value_parameters.json")
with open(json_file, 'w') as f:
    json.dump(json_dict, f, indent=4)
print(f"Parameters saved in {json_file}")

plt.draw()
plt.show(block=True)
