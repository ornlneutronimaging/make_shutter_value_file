import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from collections import OrderedDict

CLOCK_CYCLE_FILE = 'clock_cycle.txt'
SHUTTER_VALUE_FILENAME = "ShutterValues.txt"

MN = 1.674927471e-27  # kg - neutron mass
H = 6.62607004e-34  # J s - Planck constant
COEFF = (H / MN) * 1e6

TOF_FRAMES = [[1e-6, 2.5e-3],
              [2.9e-3, 5.8e-3],
              [6.2e-3, 15.9e-3]]
DEFAULT_list_lambda_dead_time = [np.mean([TOF_FRAMES[0][1], TOF_FRAMES[1][0]]),
                                  np.mean([TOF_FRAMES[1][1], TOF_FRAMES[2][0]])]
MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME = 0.3  # Angstroms
MIN_LAMBDA_PEAK_VALUE_INTERVAL = 0.3  # Angstroms
MIN_TOF_BETWEEN_FRAMES = TOF_FRAMES[1][0] - TOF_FRAMES[0][1]

RESONANCE_SHUTTER_VALUES = "1e-6\t320e-6\t3\t0.16"
DEFAULT_SHUTTER_VALUES = "1e-6\t2.5e-3\t5\t10.24\n2.9e-3\t5.8e-3\t6\t10.24\n6.2e-3\t15.9e-3\t7\t10.24"
TIME_BIN_MICROS = 10.24

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
			if not type(epics_chopper_wavelength_range) is list:
				raise AttributeError(
						"Provides the maximum range of wavelength in Angstroms the chopper are set up for! ["
						"min_value, max_value]")
			if len(epics_chopper_wavelength_range) != 2:
				raise AttributeError(
						"Provides the maximum range of wavelength in Angstroms the chopper are set up for! ["
						"min_value, max_value]")

			# _min_tof_peak_value_from_edge_of_frame = MakeShutterValueFile.convert_lambda_to_tof(
			# 		list_wavelength=[MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME],
			# 		detector_offset=detector_offset,
			# 		detector_sample_distance=self.detector_sample_distance)
			# self.min_tof_peak_value_from_edge_of_frame = _min_tof_peak_value_from_edge_of_frame[0]

		self.resonance_mode = resonance_mode
		self.default_values = default_values
		self.output_folder = output_folder
		self.detector_sample_distance = detector_sample_distance
		self.detector_offset = detector_offset
		self.epics_chopper_wavelength_range = epics_chopper_wavelength_range
		# self.minimum_measurable_lambda = self.calculate_minimum_measurable_lambda()

	def run(self, list_lambda_dead_time=None):
		"""
		
		:param list_lambda_dead_time: Ideally the user will provide a minimum of 2 or 3 equally spaced in the
		full range lambda. Those lambda will corresponds to the dead time of the MCP. if 2 lambda are not at
		least MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME (0.3 Angstroms) from each other, error is raised.
		:return:
		"""
		filename = Path(self.output_folder) / SHUTTER_VALUE_FILENAME
		if self.resonance_mode:
			resonance_shutter_value_ascii = RESONANCE_SHUTTER_VALUES
			MakeShutterValueFile.make_ascii_file_from_string(text=resonance_shutter_value_ascii,
			                                                filename=filename)
		elif self.default_values or (list_lambda_dead_time is None):
			default_shutter_value_ascii = DEFAULT_SHUTTER_VALUES
			MakeShutterValueFile.make_ascii_file_from_string(text=default_shutter_value_ascii,
			                                                filename=filename)
		else:
			# user needs to provide at least 2 dead_time_lambda
			if not type(list_lambda_dead_time) is list:
				raise ValueError("list_lambda_dead_time must be a list of at least 2 elements!")

			if len(list_lambda_dead_time) < 2:
				raise ValueError("list_lambda_dead_time should contain at least 2 dead lambda values!")


			if MakeShutterValueFile.list_lambda_dead_time_too_close(list_lambda_dead_time=list_lambda_dead_time):
				raise ValueError("Make sure the list of lambda dead time are at least {}Angstroms from each "
				                 "other".format(MIN_LAMBDA_PEAK_VALUE_INTERVAL))

			list_tof_dead_time = MakeShutterValueFile.convert_lambda_to_tof(list_wavelength=list_lambda_dead_time,
			                                                                detector_offset=self.detector_offset,
			                                                                detector_sample_distance=self.detector_sample_distance,
			                                                                output_units='s')
			self.list_tof_dead_time = list_tof_dead_time
			list_tof_frames = self.make_list_tof_frames(list_tof_dead_time)

			# shutter_values_string = self.make_shutter_values_string(list_tof_frames=list_tof_frames)

			self.final_list_tof_frames = list_tof_frames

	def make_list_tof_frames(self, list_tof_dead_time):
		list_tof_frames = []
		for _index, _tof_dead_time in enumerate(list_tof_dead_time):

			if _index == 0:
				left_tof = TOF_FRAMES[0][0]
				right_tof = _tof_dead_time - MIN_TOF_BETWEEN_FRAMES
				list_tof_frames.append([left_tof, right_tof])

			if _index == (len(list_tof_dead_time) - 1):
				left_tof = _tof_dead_time + MIN_TOF_BETWEEN_FRAMES
				right_tof = TOF_FRAMES[-1][1]
				list_tof_frames.append([left_tof, right_tof])
				break

			left_tof = _tof_dead_time + MIN_TOF_BETWEEN_FRAMES
			right_tof = list_tof_dead_time[_index + 1] - MIN_TOF_BETWEEN_FRAMES
			list_tof_frames.append([left_tof, right_tof])
		return list_tof_frames

	def make_shutter_values_string(self, list_tof_frames=None):
		shutter_value_array = []
		for _tof_frame in list_tof_frames:
			_col_1 = _tof_frame[0]
			_col_2 = _tof_frame[1]
			_col_4 = TIME_BIN_MICROS
			_col_3 = self.get_above_closest_divided(delta_tof=_tof_frame[1] - _tof_frame[0])
			shutter_value_array.append("{}\t{}\t{}\t{}".format(_col_1, _col_2, _col_3, _col_4))
		return "\n".join(shutter_value_array)

	@staticmethod
	def get_above_closest_divided(delta_tof=0):
		"""
		:param delta_tof: in s
		:param clock_cycle_data:
		:return:
		"""
		delta_tof_ms = delta_tof * 1e3    # ms
		clock_cycle_data = MakeShutterValueFile.get_clock_cycle_table()
		clock_array = np.array(clock_cycle_data['Clock'])
		where_delta_is_less_or_equal_than = np.where(delta_tof_ms <= clock_array)
		if where_delta_is_less_or_equal_than:
			index = where_delta_is_less_or_equal_than[0][-1]
			return np.array(clock_cycle_data['Divided'])[index]
		return -1

	@staticmethod
	def list_lambda_dead_time_too_close(list_lambda_dead_time=None):
		lambda_offset = np.array(list_lambda_dead_time[1:]) - np.array(list_lambda_dead_time[0:-1])
		for _offset in lambda_offset:
			if _offset <= MIN_LAMBDA_PEAK_VALUE_INTERVAL:
				return True
		return False

	def make_sure_list_wavelength_requested_can_be_measure(self, list_wavelength_requested=None):
		"""
		This routine makes sure that any of the lambda the user wants to measure are not outside the
		default time spectra file, and are above the minimum measurable lambda (calculated using detector offset and
		distance detector sample provided)

		:param list_wavelength_requested:
		:return:
		"""

		min_tof_from_default_time_spectra = TOF_FRAMES[0][0]
		max_tof_from_default_time_spectra = TOF_FRAMES[-1][1]

		min_lambda = self.convert_tof_to_lambda(tof=min_tof_from_default_time_spectra,
		                                        detector_offset=self.detector_offset,
		                                        detector_sample_distance=self.detector_sample_distance)
		max_lambda = self.convert_tof_to_lambda(tof=max_tof_from_default_time_spectra,
		                                        detector_offset=self.detector_offset,
		                                        detector_sample_distance=self.detector_sample_distance)

		for _lambda in list_wavelength_requested:

			# make sure lambda is above minimum lambda we can measure with the detector offset defined
			if _lambda - MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME < self.minimum_measurable_lambda:
				raise ValueError("Lambda too small to too close to start to be measurable")

			# make sure lambda is within min and max tof defined in default shutter value
			if _lambda < min_lambda:
				raise ValueError("Time spectra minimum value does not allow to get this lambda: {}".format(_lambda))

			if _lambda > max_lambda:
				raise ValueError("Time spectra maximum value does not allow to get this lambda: {}".format(_lambda))

	def calculate_minimum_measurable_lambda(self):
		if self.detector_sample_distance and self.detector_offset:
			return self.detector_offset * COEFF / self.detector_sample_distance

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
			_left = _wave - MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME
			_right = _wave + MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME
			dict_list_wavelength_requested[_wave] = [_left, _right]
		return dict_list_wavelength_requested

	# @staticmethod
	# def combine_wavelength_requested_too_close_to_each_other(dict_list_wavelength_requested=None,
	#                                                          safety_wavelength_offset=0):
	# 	"""
	# 	This method clean up the dict_list_wavelength_requested dictionary by merging lambda requested
	# 	that are close to each other (less then MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME). The final lambda
	# 	requested will be the average value of those lambda and the left and right lambda range will be the extreme
	# 	values
	#
	# 	ex: {5: [5-0.3, 5+0.3], 5.1: [5.1-0.3, 5.1+0.3]}
	# 	will produce
	# 	{5.05: [5-0.3, 5.1+0.3]}
	#
	# 	:param dict_list_wavelength_requested:
	# 	:param safety_wavelength_offset: this parameter makes sure that two successive lambda range are far enough
	# 			appart that a dead time of the detector can be inserted between them
	# 	:return: dictionary of the merged wavelength
	# 	"""
	# 	_dict_list_wavelength_requested = copy.deepcopy(dict_list_wavelength_requested)
	#
	# 	list_wavelength_requested = list(_dict_list_wavelength_requested.keys())
	# 	if len(list_wavelength_requested) == 1:
	# 		return _dict_list_wavelength_requested
	#
	# 	dict_clean_list_wavelength_requested = OrderedDict()
	# 	while len(_dict_list_wavelength_requested.keys()) > 1:
	#
	# 		list_keys = list(_dict_list_wavelength_requested.keys())[:2]
	# 		list_keys.sort()
	# 		first_wavelength, second_wavelength = list_keys
	#
	# 		first_wavelength_right_range = _dict_list_wavelength_requested[first_wavelength][1]
	# 		second_wavelength_left_range = _dict_list_wavelength_requested[second_wavelength][0]
	#
	# 		if second_wavelength_left_range - first_wavelength_right_range <= safety_wavelength_offset:
	# 			# they are too close to each other, we need to merge them
	#
	# 			new_merge_key = np.mean([first_wavelength, second_wavelength])
	# 			new_merge_left_range = _dict_list_wavelength_requested[first_wavelength][0]
	# 			new_merge_right_range = _dict_list_wavelength_requested[second_wavelength][1]
	#
	# 			del _dict_list_wavelength_requested[first_wavelength]
	# 			del _dict_list_wavelength_requested[second_wavelength]
	# 			_dict_list_wavelength_requested[new_merge_key] = [new_merge_left_range, new_merge_right_range]
	# 			_dict_list_wavelength_requested = \
	# 				MakeShutterValueFile.sort_dictionary_by_keys(dictionary=_dict_list_wavelength_requested)
	#
	# 		else:
	# 			dict_clean_list_wavelength_requested[first_wavelength] = copy.deepcopy(_dict_list_wavelength_requested[
	# 				                                                                       first_wavelength])
	# 			del _dict_list_wavelength_requested[first_wavelength]
	#
	# 	last_key = list(_dict_list_wavelength_requested.keys())[0]
	# 	dict_clean_list_wavelength_requested[last_key] = copy.deepcopy((_dict_list_wavelength_requested[last_key]))
	#
	# 	return dict_clean_list_wavelength_requested
	#
	# @staticmethod
	# def sort_dictionary_by_keys(dictionary=None):
	# 	"""
	# 	sort the dictionary by keys to make sure they are in increasing order
	#
	# 	:param dictionary:
	# 	:return:
	# 	"""
	# 	new_dictionary = OrderedDict()
	# 	list_key = list(dictionary.keys())
	# 	list_key.sort()
	#
	# 	for _key in list_key:
	# 		new_dictionary[_key] = dictionary[_key]
	# 	return new_dictionary

	# def set_final_tof_frames(self, dict_list_lambda_requested=None):
	# 	if dict_list_lambda_requested is None:
	# 		raise ValueError("Empty dict list lambda requested")
	#
	# 	dict_list_tof_requested = self.convert_lambda_dict_to_tof(
	# 			dict_list_lambda_requested=dict_list_lambda_requested,
	# 			output_units='s')
	# 	final_tof_frames = copy.deepcopy(TOF_FRAMES)
	#
	# 	index_tof_requested = 0
	# 	list_tof_requested_keys = list(dict_list_tof_requested.keys())
	# 	while index_tof_requested < len(list_tof_requested_keys):
	#
	# 		[_left_tof_requested, _right_tof_requested] = dict_list_tof_requested[list_tof_requested_keys[
	# 			index_tof_requested]]
	#
	# 		for index_final_tof_frames, [_left_final_tof, _right_final_tof] in enumerate(final_tof_frames):
	#
	# 			if (_left_tof_requested >= _left_final_tof) and (_right_tof_requested <= _right_final_tof):
	# 				# tof range requested full fit inside one of the final tof frame, let's move on
	# 				# to the next tof range requested
	# 				break
	#
	# 			elif (_left_tof_requested < _left_final_tof):
	# 				# tof requested is overlapping with the left gap of the final tof range
	# 				print("-> tof requested is overlapping on the left!")
	# 				break
	#
	# 			else:
	# 				print("-> tof requested is overlapping on the right!")
	# 				# delta_offset = _right_tof_requested - _right_final_tof
	# 				final_tof_frames[index_final_tof_frames] = [_left_final_tof, _left_tof_requested - MIN_TOF_BETWEEN_FRAMES]
	# 				final_tof_frames.insert(index_final_tof_frames+1, [_left_tof_requested, _right_tof_requested])
	# 				if index_final_tof_frames < (len(final_tof_frames) - 2):
	# 					# if it's not the last final tof frame, we need to shift the left range of the next frame
	# 					# by the same offset we pushed the current right range
	# 					[_, _next_right_final_tof] = final_tof_frames[index_final_tof_frames + 2]
	# 					final_tof_frames[index_final_tof_frames+2] = [_right_tof_requested + MIN_TOF_BETWEEN_FRAMES,
	# 					                                            _next_right_final_tof]
	# 				break
	#
	# 		index_tof_requested += 1
