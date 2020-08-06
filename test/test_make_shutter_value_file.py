import numpy as np
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from collections import OrderedDict
import copy

TOLERANCE = 1e-3

from shutter_value_generator.make_shutter_value_file import MakeShutterValueFile
from shutter_value_generator.make_shutter_value_file import RESONANCE_SHUTTER_VALUES
from shutter_value_generator.make_shutter_value_file import DEFAULT_SHUTTER_VALUES
from shutter_value_generator.make_shutter_value_file import MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME
from shutter_value_generator.make_shutter_value_file import TOF_FRAMES
from shutter_value_generator.make_shutter_value_file import COEFF
from shutter_value_generator.make_shutter_value_file import MIN_TOF_BETWEEN_FRAMES

def make_tmp_ascii_filename():
	ascii_filename = NamedTemporaryFile(prefix='TestingShutterValue', suffix='.txt').name
	ascii_filename = Path(ascii_filename)
	if Path(ascii_filename).exists():
		Path.unlink(ascii_filename)
	return ascii_filename

def make_test_clock_array():
	clock_array = [100]
	for _ in np.arange(1, 20):
		clock_array.append(clock_array[-1] / 2.)
	return clock_array

def make_test_timebin_array():
	timebin_array = [0.01]
	for _ in np.arange(1, 20):
		timebin_array.append(timebin_array[-1] * 2.)
	return timebin_array

def make_test_range_array():
	range_array = [0.118]
	for _ in np.arange(1, 20):
		range_array.append(range_array[-1] * 2.)
	return range_array

def convert_lambda_to_tof(list_lambda, detector_offset, detector_sample_distance):
	list_tof = [_lambda * detector_sample_distance / COEFF - detector_offset for _lambda in list_lambda]
	return list_tof

def convert_tof_to_lambda(list_tof, detector_offset, detector_sample_distance):
	list_lambda = [(detector_offset + _tof) * COEFF / detector_sample_distance for _tof in list_tof]
	return list_lambda

def test_get_clock_cycle_table():
	clock_cycle_data_returned = MakeShutterValueFile.get_clock_cycle_table()

	clock_array = make_test_clock_array()
	for _expected, _returned in zip(clock_array, clock_cycle_data_returned['Clock']):
		assert np.abs(_expected - _returned) < TOLERANCE

	divided_array = np.arange(20)
	for _expected, _returned in zip(divided_array, clock_cycle_data_returned['Divided']):
		assert _expected == _returned

	timebin_array = make_test_timebin_array()
	for _expected, _returned in zip(timebin_array, clock_cycle_data_returned['TimeBin(micros)']):
		assert np.abs(_expected - _returned) < TOLERANCE

	range_array = make_test_range_array()
	for _expected, _returned in zip(range_array, clock_cycle_data_returned['Range(ms)']):
		assert np.abs(_expected - _returned) < 0.01

def test_make_sure_minimum_parameters_passed_in_for_no_resonance_mode():
	with pytest.raises(AttributeError):
		MakeShutterValueFile()
	with pytest.raises(AttributeError):
		MakeShutterValueFile(output_folder="./")
	with pytest.raises(AttributeError):
		MakeShutterValueFile(output_folder="./", detector_sample_distance=1)
	with pytest.raises(AttributeError):
		MakeShutterValueFile(output_folder="./", detector_sample_distance=10, detector_offset=20)

@pytest.mark.parametrize('detector_offset, output_folder, detector_sample_distance, resonance_mode, '
                         'epics_chopper_wavelength_range',
	                      [(10, "/me/tmp/", 20, True, [10, 20]),
	                       (10, "/me/tmp/2", 20, False, [10, 20])])
def test_parameters_are_saved(detector_offset, output_folder, detector_sample_distance, resonance_mode,
                              epics_chopper_wavelength_range):
	o_make = MakeShutterValueFile(detector_offset=detector_offset,
	                             output_folder=output_folder,
	                             detector_sample_distance=detector_sample_distance,
	                             resonance_mode=resonance_mode,
	                             epics_chopper_wavelength_range=epics_chopper_wavelength_range)
	assert o_make.output_folder == output_folder
	assert o_make.detector_offset == detector_offset
	assert o_make.detector_sample_distance == detector_sample_distance
	assert o_make.epics_chopper_wavelength_range == epics_chopper_wavelength_range

def test_convert_lambda_to_tof():
	# output in micros
	detector_offset = 6500  # micros
	detector_sample_distance = 2100  # cm
	list_lambda = [4, 5, 6]
	list_tof = MakeShutterValueFile.convert_lambda_to_tof(list_wavelength=list_lambda,
	                                                     detector_offset=detector_offset,
	                                                     detector_sample_distance=detector_sample_distance)

	list_tof_expected = convert_lambda_to_tof(list_lambda, detector_offset, detector_sample_distance)
	assert list_tof == list_tof_expected

	# output in seconds
	list_lambda = [4, 5, 6]
	list_tof = MakeShutterValueFile.convert_lambda_to_tof(list_wavelength=list_lambda,
	                                                     detector_offset=detector_offset,
	                                                     detector_sample_distance=detector_sample_distance,
	                                                     output_units='s')
	list_tof_expected = convert_lambda_to_tof(list_lambda, detector_offset, detector_sample_distance)
	list_tof_expected = [_tof * 1e-6 for _tof in list_tof_expected]
	assert list_tof == list_tof_expected

def test_convert_tof_to_lambda():
	detector_offset = 6500  # micros
	detector_sample_distance = 2100  # cm
	tof = 21000     # micros
	lambda_returned = MakeShutterValueFile.convert_tof_to_lambda(tof=tof,
	                                                            detector_offset=detector_offset,
	                                                            detector_sample_distance=detector_sample_distance)
	lambda_expected = convert_tof_to_lambda(list_tof=[tof],
	                                        detector_offset=detector_offset,
	                                        detector_sample_distance=detector_sample_distance)
	assert np.abs(lambda_expected[0] - lambda_returned) < TOLERANCE

def test_calculate_min_tof_peak_value_from_edge_of_frame():
	output_folder = "/tmp/"
	detector_offset = 6500  # micros
	detector_sample_distance = 2100  # cm
	epics_chopper_wavelength_range = [MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME]  # Angstroms
	o_make = MakeShutterValueFile(detector_offset=detector_offset,
	                             output_folder=output_folder,
	                             detector_sample_distance=detector_sample_distance,
	                             epics_chopper_wavelength_range=epics_chopper_wavelength_range)
	min_tof_peak_value_from_edge_of_frame_calculated = o_make.min_tof_peak_value_from_edge_of_frame
	min_tof_peak_value_from_edge_of_frame_expected = convert_lambda_to_tof(list_lambda=epics_chopper_wavelength_range,
	                                                                       detector_offset=detector_offset,
	                                                                       detector_sample_distance=detector_sample_distance)
	assert np.abs(min_tof_peak_value_from_edge_of_frame_expected[0] - min_tof_peak_value_from_edge_of_frame_calculated) \
	       < TOLERANCE

@pytest.mark.parametrize('file_contain', [("entry1, entry2, entry3"),
                                          "entry1, entry2, entry3\nentry4, entry5, entry6"])
def test_make_ascii_file_from_string_single_entry(file_contain):
	ascii_filename = make_tmp_ascii_filename()
	MakeShutterValueFile.make_ascii_file_from_string(text=file_contain,
	                                                filename=ascii_filename)
	with open(ascii_filename, 'r') as f:
		file_created = f.readlines()

	file_expected = file_contain.split("\n")
	assert len(file_expected) == len(file_created)

	for _line_expected, _line_created in zip(file_expected, file_created):
		assert _line_created.strip() == _line_expected

def test_create_shutter_value_for_resonance_mode():
	temp_dir = gettempdir()
	o_make = MakeShutterValueFile(output_folder=temp_dir,
	                             resonance_mode=True)
	o_make.run()

	file_created_expected = Path(temp_dir) / "ShutterValues.txt"
	with open(file_created_expected, 'r') as f:
		file_contain_created = f.readline()

	file_contain_expected = RESONANCE_SHUTTER_VALUES
	assert file_contain_created == file_contain_expected

@pytest.mark.parametrize('list_wavelength_requested, epics_chopper_wavelength_range',
                         [([10, 20], [9.8, 30]),
                          ([12, 29.9], [9.8, 30])])
def test_lambda_to_close_to_edge_of_epics_chopper_raise_error(list_wavelength_requested, epics_chopper_wavelength_range):
	with pytest.raises(ValueError):
		MakeShutterValueFile.check_overlap_wavelength_requested_with_chopper_settings(list_wavelength_requested=list_wavelength_requested,
								                                                     epics_chopper_wavelength_range=epics_chopper_wavelength_range)

def test_initialize_dictionary_of_list_of_wavelength_requested():
	list_of_wavelength_requested = [1, 2, 5, 10, 20]
	dict_list_wavelength_requested = MakeShutterValueFile.initialize_list_of_wavelength_requested_dictionary(
			list_wavelength_requested=list_of_wavelength_requested)
	dict_list_wavelength_expected = OrderedDict()
	dict_list_wavelength_expected[1] = [1 - MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME,
	                                    1 + MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME]

	assert dict_list_wavelength_requested[1] == dict_list_wavelength_expected[1]

def test_combine_wavelength_requested_too_close_to_each_other():
	# case 1 - only 1 lambda
	list_wavelength_requested = [5]
	dict_list_wavelength_requested = MakeShutterValueFile.initialize_list_of_wavelength_requested_dictionary(
			list_wavelength_requested=list_wavelength_requested)
	before_cleaning = copy.deepcopy(dict_list_wavelength_requested)
	dict_list_wavelength_returned = MakeShutterValueFile.combine_wavelength_requested_too_close_to_each_other(
			dict_list_wavelength_requested=dict_list_wavelength_requested)
	assert dict_list_wavelength_returned == before_cleaning

	# case 2 - 2 lambda that do not need any combine
	list_wavelength_requested = [5, 6]
	dict_list_wavelength_requested = MakeShutterValueFile.initialize_list_of_wavelength_requested_dictionary(
			list_wavelength_requested=list_wavelength_requested)
	dict_list_wavelength_returned = MakeShutterValueFile.combine_wavelength_requested_too_close_to_each_other(
			dict_list_wavelength_requested=dict_list_wavelength_requested)
	assert dict_list_wavelength_requested == dict_list_wavelength_returned

	# case 3 - 2 lambda need to be combined
	list_wavelength_requested = [5, 5.1, 6]
	dict_list_wavelength_requested = MakeShutterValueFile.initialize_list_of_wavelength_requested_dictionary(
			list_wavelength_requested=list_wavelength_requested)
	dict_list_wavelength_returned = MakeShutterValueFile.combine_wavelength_requested_too_close_to_each_other(
			dict_list_wavelength_requested=dict_list_wavelength_requested)
	dict_list_wavelength_expected = OrderedDict()
	dict_list_wavelength_expected[5.05] = [5 - MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME,
	                                       5.1 + MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME]
	dict_list_wavelength_expected[6] = [6 - MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME,
	                                    6 + MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME]
	assert dict_list_wavelength_returned.keys() == dict_list_wavelength_expected.keys()
	for _key in dict_list_wavelength_expected.keys():
		_array_expected = dict_list_wavelength_expected[_key]
		_array_returned = dict_list_wavelength_returned[_key]
		for _exp, _ret in zip(_array_expected, _array_returned):
			assert np.abs(_exp - _ret) < TOLERANCE

	# case 4 - 3 lambda to combine
	list_wavelength_requested = [5, 5.1, 5.2, 6]
	dict_list_wavelength_requested = MakeShutterValueFile.initialize_list_of_wavelength_requested_dictionary(
			list_wavelength_requested=list_wavelength_requested)
	dict_list_wavelength_returned = MakeShutterValueFile.combine_wavelength_requested_too_close_to_each_other(
			dict_list_wavelength_requested=dict_list_wavelength_requested)
	dict_list_wavelength_expected = OrderedDict()
	dict_list_wavelength_expected[5.125] = [5 - MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME,
	                                        5.2 + MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME]
	dict_list_wavelength_expected[6] = [6 - MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME,
	                                    6 + MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME]
	assert dict_list_wavelength_returned.keys() == dict_list_wavelength_expected.keys()
	for _key in dict_list_wavelength_expected.keys():
		_array_expected = dict_list_wavelength_expected[_key]
		_array_returned = dict_list_wavelength_returned[_key]
		for _exp, _ret in zip(_array_expected, _array_returned):
			assert np.abs(_exp - _ret) < TOLERANCE

	# case 5 - 2 lambda to combine as too close because of safety wavelength_offset
	list_wavelength_requested = [5, 6]
	safety_wavelength_offset = 1
	dict_list_wavelength_requested = MakeShutterValueFile.initialize_list_of_wavelength_requested_dictionary(
			list_wavelength_requested=list_wavelength_requested)
	dict_list_wavelength_returned = MakeShutterValueFile.combine_wavelength_requested_too_close_to_each_other(
			dict_list_wavelength_requested=dict_list_wavelength_requested,
			safety_wavelength_offset=safety_wavelength_offset)
	dict_list_wavelength_expected = OrderedDict()
	dict_list_wavelength_expected[5.5] = [5 - MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME,
	                                      6 + MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME]
	assert dict_list_wavelength_returned.keys() == dict_list_wavelength_expected.keys()
	for _key in dict_list_wavelength_expected.keys():
		_array_expected = dict_list_wavelength_expected[_key]
		_array_returned = dict_list_wavelength_returned[_key]
		for _exp, _ret in zip(_array_expected, _array_returned):
			assert np.abs(_exp - _ret) < TOLERANCE

def test_sort_dictionary_by_keys():
	dict1 = OrderedDict()
	dict1[1] = [10, 20]
	dict1[2] = [30, 40]
	dict1[0.5] = [50, 60]

	new_dict = MakeShutterValueFile.sort_dictionary_by_keys(dictionary=dict1)
	assert [0.5, 1, 2] == list(new_dict.keys())

def test_create_default_shutter_value_file_when_no_lambda_provided():
	temp_dir = gettempdir()
	o_make = MakeShutterValueFile(output_folder=temp_dir,
	                             default_values=True)
	o_make.run()

	file_created_expected = Path(temp_dir) / "ShutterValues.txt"
	with open(file_created_expected, 'r') as f:
		file_contain_created = f.readlines()
	file_contain_created = "".join(file_contain_created)

	file_contain_expected = DEFAULT_SHUTTER_VALUES
	assert file_contain_created == file_contain_expected

def test_convert_lambda_dict_to_tof():
	output_folder = "/tmp/"
	detector_offset = 6000  # micros
	detector_sample_distance = 2100   # cm
	epics_chopper_wavelength_range = [2, 10]  # Angstroms
	o_make = MakeShutterValueFile(detector_offset=detector_offset,
	                             output_folder=output_folder,
	                             detector_sample_distance=detector_sample_distance,
	                             epics_chopper_wavelength_range=epics_chopper_wavelength_range)
	list_wavelength_requested = [3, 5, 8]
	dict_list_wavelength = MakeShutterValueFile.initialize_list_of_wavelength_requested_dictionary(
			list_wavelength_requested=list_wavelength_requested)
	dict_clean_list_wavelength_requested = MakeShutterValueFile.combine_wavelength_requested_too_close_to_each_other(
			dict_list_wavelength_requested=dict_list_wavelength)
	dict_list_tof = o_make.convert_lambda_dict_to_tof(dict_list_lambda_requested=dict_clean_list_wavelength_requested,
	                                                  output_units='s')
	dict_list_tof_expected = OrderedDict()
	for _lambda in dict_clean_list_wavelength_requested.keys():
		_tof = MakeShutterValueFile.convert_lambda_to_tof(list_wavelength=[_lambda],
		                                                 detector_offset=detector_offset,
		                                                 detector_sample_distance=detector_sample_distance,
		                                                 output_units='s')
		print(f"_tof: {_tof}")
		_range = MakeShutterValueFile.convert_lambda_to_tof(list_wavelength=dict_clean_list_wavelength_requested[
			_lambda],
		                                                   detector_offset=detector_offset,
		                                                   detector_sample_distance=detector_sample_distance,
		                                                   output_units='s')
		dict_list_tof_expected[_tof[0]] = _range

	assert dict_list_tof_expected.keys() == dict_list_tof.keys()
	for _key in dict_list_tof_expected.keys():
		list_tof_expected = dict_list_tof_expected[_key]
		list_tof_returned = dict_list_tof[_key]
		assert np.abs(list_tof_expected[0] - list_tof_returned[0]) < TOLERANCE
		assert np.abs(list_tof_expected[1] - list_tof_returned[1]) < TOLERANCE

def test_set_tof_frames_to_cover_lambda_requested():
	output_folder = "/tmp/"
	detector_offset = 6000  # micros
	detector_sample_distance = 2100   # cm
	epics_chopper_wavelength_range = [.1, 10]  # Angstroms
	o_make = MakeShutterValueFile(detector_offset=detector_offset,
	                              output_folder=output_folder,
	                              detector_sample_distance=detector_sample_distance,
	                              epics_chopper_wavelength_range=epics_chopper_wavelength_range)

	# test error raised if no dict passed
	with pytest.raises(ValueError):
		o_make.set_final_tof_frames()

	# test 1 wavelength within the first range does not change the default TOF frame
	list_wavelength_requested = [1.3]
	o_make.run(list_wavelength_requested=list_wavelength_requested)
	final_tof_frames_calculated = o_make.final_tof_frames

	dict_clean_list_wavelength_requested = o_make.dict_clean_list_wavelength_requested
	list_tof_expected = MakeShutterValueFile.convert_lambda_to_tof(
			list_wavelength=dict_clean_list_wavelength_requested[list_wavelength_requested[0]],
			detector_offset=detector_offset,
			detector_sample_distance=detector_sample_distance,
			output_units='s')

	final_tof_frames_expected = TOF_FRAMES

	print("final_tof_frames_calculated")
	print(f"->> {final_tof_frames_calculated}")
	print(f"->> {final_tof_frames_expected}")

	assert len(final_tof_frames_calculated) == len(final_tof_frames_expected)
	for _range_calculated, _range_expected in zip(final_tof_frames_calculated, final_tof_frames_expected):
		assert _range_calculated[0] == _range_expected[0]
		assert _range_calculated[1] == _range_expected[1]

	# test 1 wavelength across the first edge add 1 frame to final TOF_FRAMES
	list_wavelength_requested = [1.8]
	o_make.run(list_wavelength_requested=list_wavelength_requested)
	final_tof_frames_calculated = o_make.final_tof_frames

	dict_clean_list_wavelength_requested = o_make.dict_clean_list_wavelength_requested
	list_tof_expected = MakeShutterValueFile.convert_lambda_to_tof(
			list_wavelength=dict_clean_list_wavelength_requested[list_wavelength_requested[0]],
            detector_offset=detector_offset,
            detector_sample_distance=detector_sample_distance,
            output_units='s')

	final_tof_frames_expected = [[TOF_FRAMES[0][0], list_tof_expected[0] - MIN_TOF_BETWEEN_FRAMES],
	                             list_tof_expected,
	                             [list_tof_expected[1] + MIN_TOF_BETWEEN_FRAMES, TOF_FRAMES[1][1]],
	                             TOF_FRAMES[-1]]

	print("final_tof_frames_calculated")
	print(f"->> {final_tof_frames_calculated}")
	print(f"->> {final_tof_frames_expected}")

	assert len(final_tof_frames_calculated) == len(final_tof_frames_expected)
	for _range_calculated, _range_expected in zip(final_tof_frames_calculated, final_tof_frames_expected):
		assert _range_calculated[0] == _range_expected[0]
		assert _range_calculated[1] == _range_expected[1]

	# # test 2 wavelengths
	# list_wavelength_requested = [3, 4]
	# o_make.run(list_wavelength_requested=list_wavelength_requested)
	# final_tof_frames_calculated = o_make.final_tof_frames
	# final_tof_frames_expected = TOF_FRAMES
	#
	# assert len(final_tof_frames_calculated) == len(final_tof_frames_expected)
	# for _range_calculated, _range_expected in zip(final_tof_frames_calculated, final_tof_frames_expected):
	# 	assert _range_calculated[0] == _range_expected[0]
	# 	assert _range_calculated[1] == _range_expected[1]


# @pytest.mark.parametrize('list_wavelength_requested, epics_chopper_wavelength_range',
#                          [([1, 2, 3], [1, 5]),
#                           ([1, 10], [0.5, 8]),
#                           ([1, 10], [1, 11]),
#                           ([2, 10], [0.5, 10])])
# def test_lambda_outside_epics_chopper_range_raise_error(list_wavelength_requested,
#                                                         epics_chopper_wavelength_range):
# 	detector_sample_distance = 1300
# 	detector_offset = 6300
# 	with pytest.raises(ValueError):
# 		MakeShutterValueFile.realign_frames_with_tof_requested(
# 			list_wavelength_requested=list_wavelength_requested,
# 			detector_sample_distance=detector_sample_distance,
# 			detector_offset=detector_offset,
# 			epics_chopper_wavelength_range=epics_chopper_wavelength_range)