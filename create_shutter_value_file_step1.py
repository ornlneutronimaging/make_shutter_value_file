import click
import numpy as np
import matplotlib.pyplot as plt
import os
import json

minimum_lambda_measurable = click.prompt("Enter the minimum lambda measurable (in Angstroms) - default", type=float, default=1.9)
detector_sample_distance = click.prompt("Enter the detector sample distance (in m) - default ", type=float, default=25)
source_frequency = click.prompt("Enter the source frequency (30 or 60 Hz) - default ", type=float, default=60)
time_bin = click.prompt("Enter the time bin (10.24 or 5.12) - default ", type=float, default=5.12)
list_lambda_requested = click.prompt("Enter the list of lambda requested (in Angstroms) (ex: 1.9 2.0 3.5) - default ", type=str, default="4.07 3.36 6.73 2.62 2.49 2.22 3.28 3.84 6.23 ")
list_lambda_requested = list_lambda_requested.strip()
if "," in list_lambda_requested:
    list_lambda_requested = list_lambda_requested.replace(",", " ")
list_lambda_requested = list_lambda_requested.split(" ") 
list_lambda_requested = [float(x) for x in list_lambda_requested]
list_lambda_requested.sort()

## global variables
number_of_gaps_to_display = 5

# determine the red zone of the plots
max_time_measurable = 1/source_frequency * 1e6  # in microseconds

## utilities functions

def from_lambda_to_tof(lambda_value, detector_offset, detector_sample_distance):
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

def convert_lambda_into_offset(lambda_value, detector_sample_distance):
    distance_source_detector = detector_sample_distance * 100  # Distance from source to detector (cm)
    coeff = (distance_source_detector) / 0.3956
    tof = lambda_value * coeff
    return tof

def from_tof_to_lambda(tof_value, detector_offset, detector_sample_distance):
    """
    Convert time of flight to lambda
    :param tof_value: time of flight in microseconds
    :return: lambda in Angstrom
    """
    # Constants
    distance_source_detector = detector_sample_distance * 100  # Distance from source to detector (cm)
    coeff = (distance_source_detector) / 0.3956
    lambda_value = (tof_value + detector_offset) / coeff
    return lambda_value


def find_largest_gaps(data, number_of_gaps_to_display=5):
    gap_list = np.diff(data)
    largest_gaps = sorted(gap_list, reverse=True)[:number_of_gaps_to_display]
    return largest_gaps

def calculate_mid_value(gap):
    return gap / 2

## Main function

detector_offset = convert_lambda_into_offset(minimum_lambda_measurable, detector_sample_distance)
print(f"##########################################")
print(f"detector_offset = {detector_offset:.0f} microseconds")
print(f"##########################################")

combine_list_tof = [from_lambda_to_tof(x, detector_offset, detector_sample_distance) for x in list_lambda_requested]

list_tof_below_zero = np.where(np.array(combine_list_tof) < 0)[0]
if len(list_tof_below_zero) > 0:
    combine_list_tof = np.delete(combine_list_tof, list_tof_below_zero)
    list_lambda_requested = np.delete(list_lambda_requested, list_tof_below_zero)

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
axs2[0].set_xlim(from_lambda_to_tof(minimum_lambda_measurable, detector_offset, detector_sample_distance), xmax)
axs2[0].set_xlabel('TOF (microseconds)')
axs2[0].set_title('TOF with largest gaps highlighted (gap center position value displayed)')

label = True
for left_value, right_value in zip(combine_list_tof[:-1], combine_list_tof[1:]):
    gap_value = (right_value - left_value)
    if gap_value in largest_gaps:
        mid_value = calculate_mid_value(gap_value)
        index = np.where(np.array(largest_gaps) == gap_value)[0][0]
        alpha_index = 1-(index+1)/(len(largest_gaps)+1)
        axs2[0].text(mid_value+left_value, len(combine_list_tof)-2, f'{mid_value+left_value:.0f}', rotation=45, verticalalignment='bottom')
        if label:
            axs2[0].axvline(x=mid_value+left_value, color='b', linestyle='--', label='Mid value of gap')
            axs2[0].axvspan(left_value, right_value, color='green', alpha=alpha_index, label='Gap area (darkness % to size)')
            label = False
        else:
            axs2[0].axvline(x=mid_value+left_value, color='b', linestyle='--')
            axs2[0].axvspan(left_value, right_value, color='green', alpha=alpha_index)

# show that everything behind max_time_measurable (s) + offset can not be measured
axs2[0].axvspan(max_time_measurable, xmax, color='red', hatch="/", alpha=0.5, label='Not measurable area')
# axs2[0].set_xlim(xmin, xmax)
axs2[0].legend()

# do the same but in Angstrom scale
axs2[1].plot(combine_list, np.arange(len(combine_list)), 'ro', label='list_shutter_requested1')
xmin, xmax = axs2[1].get_xlim()
axs2[1].set_xlim(minimum_lambda_measurable, xmax)
axs2[1].set_xlabel('Bragg peaks (Angstrom)')
axs2[1].set_ylabel('Index')

label = True
for left_value, right_value in zip(combine_list[:-1], combine_list[1:]):
    gap_value = (right_value - left_value)
    if gap_value in largest_gaps_lambda:
        mid_value = calculate_mid_value(gap_value)
        axs2[1].text(mid_value+left_value, len(combine_list)-2, f'{mid_value+left_value:.2f}', rotation=45, verticalalignment='bottom')
        index = np.where(np.array(largest_gaps_lambda) == gap_value)[0][0]
        alpha_index = 1-(index+1)/(len(largest_gaps_lambda)+1)
        if label:
            axs2[1].axvline(x=mid_value+left_value, color='b', linestyle='--', label='Mid value of gap')
            axs2[1].axvspan(left_value, right_value, color='green', alpha=alpha_index, label='Gap area (darkness % to size)')
            label = False
        else:
            axs2[1].axvline(x=mid_value+left_value, color='b', linestyle='--')
            axs2[1].axvspan(left_value, right_value, color='green', alpha=alpha_index)

last_value_measurable = from_tof_to_lambda(max_time_measurable, detector_offset, detector_sample_distance)
axs2[1].axvspan(last_value_measurable, xmax, color='red', hatch="/", alpha=0.5, label='Not measurable area')
axs2[1].legend()

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
            'source_frequency': source_frequency,
            }

home_dir = os.path.expanduser("~")
json_file = os.path.join(home_dir, ".shutter_value_parameters.json")
with open(json_file, 'w') as f:
    json.dump(json_dict, f, indent=4)
print(f"Parameters saved in {json_file}")

plt.draw()
plt.pause(0.1)
plt.tight_layout()
plt.show()
