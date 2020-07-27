import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from collections import OrderedDict

DELTA_TIME_BETWEEN_FRAMES = 0.32e-6   # s
CLOCK_CYCLE_FILE = 'clock_cycle.txt'
SHUTTER_VALUE_FILENAME = "ShutterValues.txt"

MN = 1.674927471e-27  #kg - neutron mass
H = 6.62607004e-34 #J s - Planck constant

TOF_FRAMES = [[1e-6, 2.5e-3],
              [2.9e-3, 5.8e-3],
              [6.2e-3, 15.9e-3]]
MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME = 0.3  # Angstroms

RESONANCE_SHUTTER_VALUES = "1e-6\t320e-6\t3\t0.16"
DEFAULT_SHUTTER_VALUES = "1e-6\t2.5e-3\t5\t10.24\n2.9e-3\t5.8e-3\t6\t10.24\n6.2e-3\t15.9e-3\t7\t10.24"

# parser = argparse.ArgumentParser(description="Generate ShutterValue.txt file used by the MCP detector")
# parser.add_argument('--output', default='./', help='output folder where the ShutterValue.txt file will be created')
# parser.add_argument('--detector_sample_distance', default=13,
#                     help='Distance detector to sample in meters',
#                     type=float)
# parser.add_argument('--detector_offset', default=6500,
#                     help='Detector offset in micro seconds',
#                     type=float)
# parser.add_argument('--list_wavelength', help='Comma separated list of wavelength you want to measure (no white '
#                                               'spaces)')
#
# args = parser.parse_args()


class MakeShuterValueFile:

	def __init__(self, output_folder=None,
	             detector_sample_distance=None,
	             detector_offset=None,
	             resonance_mode=False,
	             default_values=False,
	             epics_chopper_wavelength_range=None):
		"""
		:param output_folder:
		:param detector_sample_distance: in m
		:param detector_offset:  in micros
		:param resonance_mode: boolean
		"""
		if output_folder is None:
			raise AttributeError("Output folder needs to be an existing output folder!")

		if resonance_mode or default_values:
			pass
		else:
			if detector_sample_distance is None:
				raise AttributeError("define a detector sample distance in meters!")
			self.detector_sample_distance = detector_sample_distance

			if detector_offset is None:
				raise AttributeError("define a detector offset in micros!")

			if epics_chopper_wavelength_range is None:
				raise AttributeError(
					"Provides the maximum range of wavelength in Angstroms the chopper are set up for! ["
					"min_value, max_value]")

			self.min_tof_peak_value_from_edge_of_frame = MakeShuterValueFile.convert_lambda_to_tof(
					list_wavelength=[MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME],
					detector_offset=0,
					detector_sample_distance=self.detector_sample_distance)

		self.resonance_mode = resonance_mode
		self.default_values = default_values
		self.output_folder = output_folder
		self.detector_sample_distance = detector_sample_distance
		self.detector_offset = detector_offset
		self.epics_chopper_wavelength_range = epics_chopper_wavelength_range

	def run(self, list_wavelength_requested=None):
		filename = Path(self.output_folder) / SHUTTER_VALUE_FILENAME
		if self.resonance_mode:
			resonance_shutter_value_ascii = RESONANCE_SHUTTER_VALUES
			MakeShuterValueFile.make_ascii_file_from_string(text=resonance_shutter_value_ascii,
			                                                filename=filename)
		elif self.default_values:
			default_shutter_value_ascii = DEFAULT_SHUTTER_VALUES
			MakeShuterValueFile.make_ascii_file_from_string(text=default_shutter_value_ascii,
			                                                filename=filename)
		else:
			MakeShuterValueFile.check_overlap_wavelength_requested_with_chopper_settings(
					list_wavelength_requested=list_wavelength_requested,
					epics_chopper_wavelength_range=self.epics_chopper_wavelength_range)

	@staticmethod
	def get_clock_cycle_table():
		full_file_name = Path(__file__).parent / CLOCK_CYCLE_FILE
		assert Path(full_file_name).exists()

		clock_cycle_data = pd.read_csv(full_file_name,
		                               names=['Clock', 'Divided', 'TimeBin(micros)', 'Range(ms)'],
		                               skiprows=1)
		return clock_cycle_data

	@staticmethod
	def convert_lambda_to_tof(list_wavelength=None,
	                          detector_offset=None,
	                          detector_sample_distance=None):
		"""
		convert the list of lambda (wavelength) into TOF(micros) units

		:param list_wavelength: in units of Angstroms
		:param detector_offset: in micros
		:param detector_sample_distance: in cm
		:return: the list of lambda in micros
		"""
		list_tof = []
		coeff = 0.3956
		for _lambda in list_wavelength:
			_tof = _lambda * detector_sample_distance / coeff - detector_offset
			list_tof.append(_tof)
		return list_tof

	@staticmethod
	def make_ascii_file_from_string(text="", filename=''):
	    with open(filename, 'w') as f:
	        f.write(text)

	@staticmethod
	def check_overlap_wavelength_requested_with_chopper_settings(list_wavelength_requested=None,
	                                                             epics_chopper_wavelength_range=None):
		for _wavelength_requested in list_wavelength_requested:
			if ((_wavelength_requested - MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME) < epics_chopper_wavelength_range[
				0]) or ((_wavelength_requested + MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME) >
					epics_chopper_wavelength_range[1]):
				raise ValueError(
					"One or more of the wavelength you defined won't allow to fully measure the Bragg Edge!")

	@staticmethod
	def initialize_list_of_wavelength_requested_dictionary(list_wavelength_requested=None):
		dict_list_wavelength_requested = OrderedDict()
		for _wave in list_wavelength_requested:
			dict_list_wavelength_requested[_wave] = [_wave - MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME,
			                                         _wave + MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME]
		return dict_list_wavelength_requested

	@staticmethod
	def combine_wavelength_requested_too_close_to_each_other(dict_list_wavelength_requested=None):
		list_wavelength_requested = dict_list_wavelength_requested.keys()
		if len(list_wavelength_requested) == 1:
			return









	# @staticmethod
	# def merge_wavelength_requested_if_within_min_lambda_value_threshold(list_wavelength_requested=None):
	# 	if len(list_wavelength_requested == 1):
	# 		return
	# 	list_wavelength_requested = np.array(list_wavelength_requested)
	# 	delta_list_wavelength_requested = list_wavelength_requested[1:-1] - list_wavelength_requested[0:-2]
	# 	delta_list_wavelength_requested_below_threshold = np.where(delta_list_wavelength_requested < MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME)
	#
	# 	# none of the wavelength requested overlap
	# 	if delta_list_wavelength_requested_below_threshold[0].size == 0:
	# 		return
	#
	# 	first_overlap = delta_list_wavelength_requested_below_threshold[0][0]
	# 	list_wavelength_requested = list(list_wavelength_requested)
	# 	list_wavelength_requested[first_overlap] = np.mean([list_wavelength_requested[first_overlap],
	# 	                                                    list_wavelength_requested[first_overlap+1]])
	# 	list_wavelength_requested.pop(first_overlap+1)
	# 	MakeShuterValueFile.merge_wavelength_requested_if_within_min_lambda_value_threshold(
	# 			list_wavelength_requested=list_wavelength_requested)



	# list_tof_requested = MakeShuterValueFile.convert_lambda_to_tof(list_wavelength=list_wavelength_requested,
		#                                                                detector_sample_distance=detector_sample_distance,
		#                                                                detector_offset=detector_offset)
		# list_tof_requested.sort()
		# epics_tof_range = MakeShuterValueFile.convert_lambda_to_tof(list_wavelength=epics_chopper_wavelength_range,
		#                                                             detector_offset=detector_offset,
		#                                                             detector_sample_distance=detector_sample_distance)
		# epics_tof_range.sort()
		#
		# if (list_tof_requested[0] <= epics_tof_range[0]) or (list_tof_requested[-1] >= epics_tof_range[-1]):
		# 	raise ValueError("One or more of the wavelength you defined is outside the range defined by the choppers!")
		#
		# min_tof_peak_value_from_edge_of_frame = MakeShuterValueFile.convert_lambda_to_tof(
		# 		list_wavelength=[MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME],
		# 		detector_sample_distance=detector_sample_distance,
		# 		detector_offset=detector_offset)
		#
		# raw_list_of_tof_ranges_requested = []
		# for _tof in list_tof_requested:
		# 	raw_list_of_tof_ranges_requested.append([_tof - min_tof_peak_value_from_edge_of_frame[0],
		# 	                                         _tof + min_tof_peak_value_from_edge_of_frame[0]])


