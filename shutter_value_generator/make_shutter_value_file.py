import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from collections import OrderedDict
import copy

DELTA_TIME_BETWEEN_FRAMES = 0.32e-6  # s
CLOCK_CYCLE_FILE = 'clock_cycle.txt'
SHUTTER_VALUE_FILENAME = "ShutterValues.txt"

MN = 1.674927471e-27  # kg - neutron mass
H = 6.62607004e-34  # J s - Planck constant
COEFF = (H / MN) * 1e6

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


class MakeShutterValueFile:

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

			_min_tof_peak_value_from_edge_of_frame = MakeShutterValueFile.convert_lambda_to_tof(
					list_wavelength=[MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME],
					detector_offset=detector_offset,
					detector_sample_distance=self.detector_sample_distance)
			self.min_tof_peak_value_from_edge_of_frame = _min_tof_peak_value_from_edge_of_frame[0]

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
			MakeShutterValueFile.make_ascii_file_from_string(text=resonance_shutter_value_ascii,
			                                                filename=filename)
		elif self.default_values:
			default_shutter_value_ascii = DEFAULT_SHUTTER_VALUES
			MakeShutterValueFile.make_ascii_file_from_string(text=default_shutter_value_ascii,
			                                                filename=filename)
		else:
			MakeShutterValueFile.check_overlap_wavelength_requested_with_chopper_settings(
					list_wavelength_requested=list_wavelength_requested,
					epics_chopper_wavelength_range=self.epics_chopper_wavelength_range)
			dict_list_wavelength_requested = MakeShutterValueFile.initialize_list_of_wavelength_requested_dictionary(
					list_wavelength_requested=list_wavelength_requested)
			dict_clean_list_wavelength_requested = \
				MakeShutterValueFile.combine_wavelength_requested_too_close_to_each_other(
						dict_list_wavelength_requested=dict_list_wavelength_requested)
			self.final_tof_frames = self.set_final_tof_frames(
					dict_list_lambda_requested=dict_clean_list_wavelength_requested)

	def convert_lambda_dict_to_tof(self, dict_list_lambda_requested=None, output_units='micros'):
		dict_list_tof_requested = OrderedDict()
		for _lambda in dict_list_lambda_requested.keys():
			_tof = MakeShutterValueFile.convert_lambda_to_tof(list_wavelength=[_lambda],
			                                                 detector_offset=self.detector_offset,
			                                                 detector_sample_distance=self.detector_sample_distance,
			                                                 output_units=output_units)
			_tof_range = MakeShutterValueFile.convert_lambda_to_tof(list_wavelength=dict_list_lambda_requested[_lambda],
			                                                       detector_offset=self.detector_offset,
			                                                       detector_sample_distance=
			                                                       self.detector_sample_distance,
			                                                       output_units=output_units)
			dict_list_tof_requested[_tof[0]] = _tof_range
		return dict_list_tof_requested

	@staticmethod
	def convert_tof_to_lambda(tof=None,
	                          detector_offset=None,
	                          detector_sample_distance=None):
		"""

		:param tof: in micros
		:param detector_offset: micros
		:param detector_sample_distance: in cm
		:return:
		lambda in Angstroms
		"""
		return (detector_offset + tof) * COEFF / detector_sample_distance

	@staticmethod
	def get_clock_cycle_table():
		full_file_name = Path(__file__).parent / CLOCK_CYCLE_FILE
		print(f"full file name is: {full_file_name}")
		assert Path(full_file_name).exists()

		clock_cycle_data = pd.read_csv(full_file_name,
		                               names=['Clock', 'Divided', 'TimeBin(micros)', 'Range(ms)'],
		                               skiprows=1)
		return clock_cycle_data

	@staticmethod
	def convert_lambda_to_tof(list_wavelength=None,
	                          detector_offset=None,
	                          detector_sample_distance=None,
	                          output_units='micros'):
		"""
		convert the list of lambda (wavelength) into TOF(micros) units

		:param list_wavelength: in units of Angstroms
		:param detector_offset: in micros
		:param detector_sample_distance: in cm
		:param output_units: default in seconds but micros can be used
		:return: the list of lambda in micros
		"""
		list_tof = []
		for _lambda in list_wavelength:
			_tof = _lambda * detector_sample_distance / COEFF - detector_offset
			if output_units == 's':
				_tof *= 1e-6
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
	def combine_wavelength_requested_too_close_to_each_other(dict_list_wavelength_requested=None,
	                                                         safety_wavelength_offset=0):
		"""
		This method clean up the dict_list_wavelength_requested dictionary by merging lambda requested
		that are close to each other (less then MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME). The final lambda
		requested will be the average value of those lambda and the left and right lambda range will be the extreme
		values

		ex: {5: [5-0.3, 5+0.3], 5.1: [5.1-0.3, 5.1+0.3]}
		will produce
		{5.05: [5-0.3, 5.1+0.3]}

		:param dict_list_wavelength_requested:
		:param safety_wavelength_offset: this parameter makes sure that two successive lambda range are far enough
				appart that a dead time of the detector can be inserted between them
		:return: dictionary of the merged wavelength
		"""
		_dict_list_wavelength_requested = copy.deepcopy(dict_list_wavelength_requested)

		list_wavelength_requested = list(_dict_list_wavelength_requested.keys())
		if len(list_wavelength_requested) == 1:
			return _dict_list_wavelength_requested

		dict_clean_list_wavelength_requested = OrderedDict()
		while len(_dict_list_wavelength_requested.keys()) > 1:

			list_keys = list(_dict_list_wavelength_requested.keys())[:2]
			list_keys.sort()
			first_wavelength, second_wavelength = list_keys

			first_wavelength_right_range = _dict_list_wavelength_requested[first_wavelength][1]
			second_wavelength_left_range = _dict_list_wavelength_requested[second_wavelength][0]

			if second_wavelength_left_range - first_wavelength_right_range <= safety_wavelength_offset:
				# they are too close to each other, we need to merge them

				new_merge_key = np.mean([first_wavelength, second_wavelength])
				new_merge_left_range = _dict_list_wavelength_requested[first_wavelength][0]
				new_merge_right_range = _dict_list_wavelength_requested[second_wavelength][1]

				del _dict_list_wavelength_requested[first_wavelength]
				del _dict_list_wavelength_requested[second_wavelength]
				_dict_list_wavelength_requested[new_merge_key] = [new_merge_left_range, new_merge_right_range]
				_dict_list_wavelength_requested = \
					MakeShutterValueFile.sort_dictionary_by_keys(dictionary=_dict_list_wavelength_requested)

			else:
				dict_clean_list_wavelength_requested[first_wavelength] = copy.deepcopy(_dict_list_wavelength_requested[
					                                                                       first_wavelength])
				del _dict_list_wavelength_requested[first_wavelength]

		last_key = list(_dict_list_wavelength_requested.keys())[0]
		dict_clean_list_wavelength_requested[last_key] = copy.deepcopy((_dict_list_wavelength_requested[last_key]))

		return dict_clean_list_wavelength_requested

	@staticmethod
	def sort_dictionary_by_keys(dictionary=None):
		"""
		sort the dictionary by keys to make sure they are in increasing order

		:param dictionary:
		:return:
		"""
		new_dictionary = OrderedDict()
		list_key = list(dictionary.keys())
		list_key.sort()

		for _key in list_key:
			new_dictionary[_key] = dictionary[_key]
		return new_dictionary

	def set_final_tof_frames(self, dict_list_lambda_requested=None):
		if dict_list_lambda_requested is None:
			raise ValueError("Empty dict list lambda requested")

		dict_list_tof_requested = self.convert_lambda_dict_to_tof(
				dict_list_lambda_requested=dict_list_lambda_requested,
				output_units='s')
		final_tof_frames = copy.deepcopy(TOF_FRAMES)

		index_tof_requested = 0
		list_tof_requested_keys = list(dict_list_tof_requested.keys())
		while index_tof_requested < len(list_tof_requested_keys):

			[_left_tof_requested, _right_tof_requested] = dict_list_tof_requested[list_tof_requested_keys[
				index_tof_requested]]

			index_tof_requested += 1




		# for _tof_requested in dict_list_tof_requested.keys():
		# 	[_left_tof_requested, _right_tof_requested] = dict_list_tof_requested[_tof_requested]
		# 	for _final_tof in final_tof_frames:
		# 		_left_tof_final, _right_tof_final = _final_tof
		# 		if (_left_tof_requested > _left_tof_final) and (_right_tof_requested < _right_tof_final):
		# 			# nothing to do, we ended up inside a time range already defined
		# 			continue
		# 		elif _left_tof_requested > _left_tof_final:
		# 			# tof requested is overlapping with the right edge
		#
		# 			# current _right_tof_final is now _right_tof_requested
		# 			# next _left_tof_final must be pushed to the right by (old_right_tof_final - new_right_tof_final)
		# 			# restart looping from beginning
		# 			pass
		#
		# 		elif _right_tof_requested < _right_tof_final:
		# 			# tof requested is overlapping with the left edge
		# 			pass
		#
		# 			# we should never end up here !!!!!
		#
		# 		else:
		# 			# full tof range requested is outside this final tof range proposed
		# 			continue

		return final_tof_frames