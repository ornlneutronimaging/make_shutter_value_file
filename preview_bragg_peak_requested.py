import argparse
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
# sys.path.append(os.path.join('.', 'shutter_value_generator'))
# from make_shutter_value_file import MakeShutterValueFile
from shutter_value_generator import make_shutter_value_file


parser = argparse.ArgumentParser(description="Display lambda requested with gaps")
parser.add_argument('--verbose', '-v', default=0, action='count',
                    help='Display lambda requested with gaps')
parser.add_argument('--detector_sample_distance',
                    default=25,
                    help='Distance detector to sample in m',
                    type=float)
parser.add_argument('--detector_offset',
                    default=0,
                    help='Detector offset in micro seconds',
                    type=float)
parser.add_argument('--list_lambda_requested',
                    help='List of lambda requested',
                    type=float,
                    nargs='+')
parser.add_argument('--minimum_lambda_measurable',
                    type=float,
                    default=1.9,
                    help='Minimum lambda measurable in Angstrom')
parser.add_argument('--number_of_gaps_to_display',
                    type=int,
                    default=6,
                    help='Number of gaps to display')
parser.add_argument('--time_bin',
                    type=float,
                    default=10.24,
                    help='Time bin in microseconds')
parser.add_argument('--output_folder',
                    default='./',
                    help='Output folder where the ShutterValue.txt file will be created')

args = parser.parse_args()

detector_sample_distance = args.detector_sample_distance  # Distance detector to sample in m
detector_offset = args.detector_offset # Detector offset in micro seconds
list_lambda_requested = args.list_lambda_requested
minimum_lambda_measurable = args.minimum_lambda_measurable  # Minimum lambda measurable in Angstrom
number_of_gaps_to_display = args.number_of_gaps_to_display  # Number of gaps to display
time_bin = args.time_bin  # Time bin in microseconds (either 10.24 or 5.12)
output_folder = args.output_folder  # Output folder where the ShutterValue.txt file will be created

list_lambda_requested.sort()

def from_lambda_to_tof(lambda_value):
    """
    Convert lambda to time of flight
    :param lambda_value: lambda in Angstrom
    :return: time of flight in microseconds
    """
    # Constants
    distance_source_detector = detector_sample_distance * 100  # Distance from source to detector (cm)
    coeff = (distance_source_detector) / 0.3956
    tof = lambda_value * coeff - detector_offset
    return tof 

def from_tof_to_lambda(tof_value):
    """
    Convert time of flight to lambda
    :param tof_value: time of flight in microseconds
    :return: lambda in Angstrom
    """
    # Constants
    distance_source_detector = 25.0 * 100  # Distance from source to detector (cm)
    coeff = (distance_source_detector) / 0.3956
    lambda_value = (tof_value + detector_offset) / coeff
    return lambda_value


def find_largest_gaps(data):
    gap_list = np.diff(data)
    largest_gaps = sorted(gap_list, reverse=True)[:number_of_gaps_to_display]
    return largest_gaps


def calculate_mid_value(gap):
    return gap / 2

# # display in angstroms
# fig1, axs = plt.subplots(2, 1, figsize=(10, 8), num='lambda_requested')
# axs[0].set_title("list lambda_requested")
# axs[0].plot(list_lambda_requested, 
#             np.arange(len(list_lambda_requested)), 
#             'ro', 
#             label='list_lambda requested')
# axs[0].set_xlabel('Bragg peaks (Angstrom)')
# axs[0].set_ylabel('Index')
# axs[0].grid()

# # display in microseconds
combine_list_tof = [from_lambda_to_tof(x) for x in list_lambda_requested]
# axs[1].plot(combine_list_tof, np.arange(len(combine_list_tof)), 'ro', label='list_shutter_requested1')
# axs[1].set_xlabel('TOF (microseconds)')
# axs[1].grid()

# plt.draw()
# plt.show(block=False)
# plt.pause(0.1)
# plt.tight_layout()

# display gaps

data = combine_list_tof
largest_gaps = find_largest_gaps(data)
mid_values = [calculate_mid_value(gap) for gap in largest_gaps]

combine_list = list_lambda_requested
data_lambda = list_lambda_requested
largest_gaps_lambda = find_largest_gaps(data_lambda)
mid_values_lambda = [calculate_mid_value(gap) for gap in largest_gaps_lambda]

fig2, axs2 = plt.subplots(2, 1, figsize=(10, 8), num='Display gaps')
axs2[0].plot(combine_list_tof, np.arange(len(combine_list_tof)), 'ro', label='list_shutter_requested1')
xmin, xmax = axs2[0].get_xlim()
axs2[0].set_xlim(from_lambda_to_tof(minimum_lambda_measurable), xmax)
axs2[0].set_xlabel('TOF (microseconds)')
axs2[0].set_title('TOF with largest gaps highlighted (gap center position value displayed)')

for left_value, right_value in zip(combine_list_tof[:-1], combine_list_tof[1:]):
    gap_value = (right_value - left_value)
    if gap_value in largest_gaps:
        mid_value = calculate_mid_value(gap_value)
        axs2[0].axvline(x=mid_value+left_value, color='b', linestyle='--', label='Mid value of gap')
        axs2[0].text(mid_value+left_value, len(combine_list_tof)-2, f'{mid_value+left_value:.0f}', rotation=45, verticalalignment='bottom')
        # plt.text(mid_value, 0, f'{mid_value:.2f}', rotation=90, verticalalignment='bottom')

        index = np.where(np.array(largest_gaps) == gap_value)[0][0]
        alpha_index = 1-(index+1)/(len(largest_gaps)+1)
        axs2[0].axvspan(left_value, right_value, color='green', alpha=alpha_index, label='Gap area')

# show that everything behind 1/60 (s) + offset can not be measured
axs2[0].axvspan(1/60 * 1e6, combine_list_tof[-1], color='red', hatch="/", alpha=0.5, label='Not measurable area')
# axs2[0].set_xlim(xmin, xmax)


# do the same but in Angstrom scale
axs2[1].plot(combine_list, np.arange(len(combine_list)), 'ro', label='list_shutter_requested1')
xmin, xmax = axs2[1].get_xlim()
axs2[1].set_xlim(minimum_lambda_measurable, xmax)
axs2[1].set_xlabel('Bragg peaks (Angstrom)')
axs2[1].set_ylabel('Index')

for left_value, right_value in zip(combine_list[:-1], combine_list[1:]):
    gap_value = (right_value - left_value)
    if gap_value in largest_gaps_lambda:
        mid_value = calculate_mid_value(gap_value)
        axs2[1].axvline(x=mid_value+left_value, color='b', linestyle='--', label='Mid value of gap')
        axs2[1].text(mid_value+left_value, len(combine_list)-2, f'{mid_value+left_value:.2f}', rotation=45, verticalalignment='bottom')
        # plt.text(mid_value, 0, f'{mid_value:.2f}', rotation=90, verticalalignment='bottom')

        index = np.where(np.array(largest_gaps_lambda) == gap_value)[0][0]
        alpha_index = 1-(index+1)/(len(largest_gaps_lambda)+1)
        axs2[1].axvspan(left_value, right_value, color='green', alpha=alpha_index, label='Gap area')

last_value_measurable = from_tof_to_lambda(1/60 * 1e6)
axs2[1].axvspan(last_value_measurable, combine_list[-1], color='red', hatch="/", alpha=0.5, label='Not measurable area')

plt.draw()
plt.pause(0.1)
plt.tight_layout()
plt.show(block=False)

# ask for dead time values
dead_time_values = input("Enter center of dead time values in lambda (space separated): ")
dead_time_values = dead_time_values.split(" ")
dead_time_values = [float(value) for value in dead_time_values]

o_shutter_value = make_shutter_value_file.MakeShutterValueFile(detector_sample_distance=25.0,
                                                                detector_offset=detector_offset,
                                                                output_folder=output_folder,
                                                                verbose=True,
                                                                time_bin=time_bin,
                                                                no_output_file=False,
                                                                epics_chopper_wavelength_range=[minimum_lambda_measurable, 
                                                                                                np.array(list_lambda_requested).max()],
                                                                )

print(f"Shutter value file will be created in {output_folder} and named ShutterValues.txt")

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

plt.draw()
plt.show(block=True)
