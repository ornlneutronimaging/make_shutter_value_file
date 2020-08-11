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
from shutter_value_generator.make_shutter_value_file import MIN_TOF_BETWEEN_FRAMES
from shutter_value_generator.make_shutter_value_file import TOF_FRAMES
from shutter_value_generator.make_shutter_value_file import COEFF

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

# def test_calculate_minimum_measurable_lambda():
# 	output_folder = "/tmp/"
# 	detector_offset = 6000  # micros
# 	detector_sample_distance = 2100   # cm
# 	epics_chopper_wavelength_range = [.1, 10]  # Angstroms
# 	o_make = MakeShutterValueFile(detector_offset=detector_offset,
# 	                              output_folder=output_folder,
# 	                              detector_sample_distance=detector_sample_distance,
# 	                              epics_chopper_wavelength_range=epics_chopper_wavelength_range)
# 	print(o_make.minimum_measurable_lambda)

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

# def test_calculate_min_tof_peak_value_from_edge_of_frame():
# 	output_folder = "/tmp/"
# 	detector_offset = 6500  # micros
# 	detector_sample_distance = 2100  # cm
# 	epics_chopper_wavelength_range = [MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME, 20]  # Angstroms
# 	o_make = MakeShutterValueFile(detector_offset=detector_offset,
# 	                             output_folder=output_folder,
# 	                             detector_sample_distance=detector_sample_distance,
# 	                             epics_chopper_wavelength_range=epics_chopper_wavelength_range)
# 	min_tof_peak_value_from_edge_of_frame_calculated = o_make.min_tof_peak_value_from_edge_of_frame
# 	min_tof_peak_value_from_edge_of_frame_expected = convert_lambda_to_tof(list_lambda=epics_chopper_wavelength_range,
# 	                                                                       detector_offset=detector_offset,
# 	                                                                       detector_sample_distance=detector_sample_distance)
# 	assert np.abs(min_tof_peak_value_from_edge_of_frame_expected[0] - min_tof_peak_value_from_edge_of_frame_calculated) \
# 	       < TOLERANCE

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

# @pytest.mark.parametrize('list_wavelength_requested, epics_chopper_wavelength_range',
#                          [([10, 20], [9.8, 30]),
#                           ([12, 29.9], [9.8, 30])])
# def test_lambda_to_close_to_edge_of_epics_chopper_raise_error(list_wavelength_requested, epics_chopper_wavelength_range):
# 	with pytest.raises(ValueError):
# 		MakeShutterValueFile.check_overlap_wavelength_requested_with_chopper_settings(list_wavelength_requested=list_wavelength_requested,
# 								                                                     epics_chopper_wavelength_range=epics_chopper_wavelength_range)

# def test_initialize_dictionary_of_list_of_wavelength_requested():
# 	list_of_wavelength_requested = [2, 5, 10, 20]
# 	dict_list_wavelength_requested = MakeShutterValueFile.initialize_list_of_wavelength_requested_dictionary(
# 			list_wavelength_requested=list_of_wavelength_requested)
# 	dict_list_wavelength_expected = OrderedDict()
# 	for _request in list_of_wavelength_requested:
# 		_left = np.max([0, _request - MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME])
# 		_right = np.max([0, _request + MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME])
# 		dict_list_wavelength_expected[_request] = [_left, _right]
#
# 	for _key in dict_list_wavelength_requested.keys():
# 		assert dict_list_wavelength_expected[_key] == dict_list_wavelength_requested[_key]

# def test_sort_dictionary_by_keys():
# 	dict1 = OrderedDict()
# 	dict1[1] = [10, 20]
# 	dict1[2] = [30, 40]
# 	dict1[0.5] = [50, 60]
#
# 	new_dict = MakeShutterValueFile.sort_dictionary_by_keys(dictionary=dict1)
# 	assert [0.5, 1, 2] == list(new_dict.keys())

def test_create_default_shutter_value_file_when_no_lambda_provided():
	temp_dir = gettempdir()
	o_make = MakeShutterValueFile(output_folder=temp_dir,
	                              default_mode=True)
	o_make.run()

	file_created_expected = Path(temp_dir) / "ShutterValues.txt"
	with open(file_created_expected, 'r') as f:
		file_contain_created = f.readlines()
	file_contain_created = "".join(file_contain_created)

	file_contain_expected = DEFAULT_SHUTTER_VALUES
	assert file_contain_created == file_contain_expected

def test_create_default_shutter_value_file_when_no_list_lambda_dead_time_provided():
	temp_dir = gettempdir()
	detector_offset = 6000  # micros
	detector_sample_distance = 2100   # cm
	epics_chopper_wavelength_range = [2, 10]  # Angstroms
	o_make = MakeShutterValueFile(detector_offset=detector_offset,
	                             output_folder=temp_dir,
	                             detector_sample_distance=detector_sample_distance,
	                             epics_chopper_wavelength_range=epics_chopper_wavelength_range)
	o_make.run()
	file_created_expected = Path(temp_dir) / "ShutterValues.txt"
	with open(file_created_expected, 'r') as f:
		file_contain_created = f.readlines()
	file_contain_created = "".join(file_contain_created)

	file_contain_expected = DEFAULT_SHUTTER_VALUES
	assert file_contain_created == file_contain_expected

def test_list_lambda_dead_time_should_have_at_least_2_elements():
	output_folder = "/tmp/"
	detector_offset = 6000  # micros
	detector_sample_distance = 2100   # cm
	epics_chopper_wavelength_range = [2, 10]  # Angstroms
	o_make = MakeShutterValueFile(detector_offset=detector_offset,
	                             output_folder=output_folder,
	                             detector_sample_distance=detector_sample_distance,
	                             epics_chopper_wavelength_range=epics_chopper_wavelength_range)
	with pytest.raises(ValueError):
		o_make.run(list_lambda_dead_time=10)

	with pytest.raises(ValueError):
		o_make.run(list_lambda_dead_time=[10])

def test_list_lambda_dead_time_too_close_to_each_other():
	output_folder = "/tmp/"
	detector_offset = 6000  # micros
	detector_sample_distance = 2100   # cm
	epics_chopper_wavelength_range = [2, 10]  # Angstroms
	o_make = MakeShutterValueFile(detector_offset=detector_offset,
	                             output_folder=output_folder,
	                             detector_sample_distance=detector_sample_distance,
	                             epics_chopper_wavelength_range=epics_chopper_wavelength_range)
	list_lambda_dead_time = [3, 3.3]
	with pytest.raises(ValueError):
		o_make.run(list_lambda_dead_time=list_lambda_dead_time)

def test_list_lambda_dead_time_3_elements():
	output_folder = "/tmp/"
	detector_offset = 6000  # micros
	detector_sample_distance = 2100   # cm
	epics_chopper_wavelength_range = [2, 10]  # Angstroms
	o_make = MakeShutterValueFile(detector_offset=detector_offset,
	                             output_folder=output_folder,
	                             detector_sample_distance=detector_sample_distance,
	                             epics_chopper_wavelength_range=epics_chopper_wavelength_range)
	list_lambda_dead_time = [3, 5, 8]
	o_make.run(list_lambda_dead_time=list_lambda_dead_time)

	final_list_tof_frames_calculated = o_make.final_list_tof_frames
	list_tof_dead_time = o_make.list_tof_dead_time
	final_list_tof_frames_expected = []
	final_list_tof_frames_expected.append([TOF_FRAMES[0][0],
	                                       list_tof_dead_time[0] - MIN_TOF_BETWEEN_FRAMES])
	final_list_tof_frames_expected.append([list_tof_dead_time[0] + MIN_TOF_BETWEEN_FRAMES,
	                                       list_tof_dead_time[1] - MIN_TOF_BETWEEN_FRAMES])
	final_list_tof_frames_expected.append([list_tof_dead_time[1] + MIN_TOF_BETWEEN_FRAMES,
	                                       list_tof_dead_time[2] - MIN_TOF_BETWEEN_FRAMES])
	final_list_tof_frames_expected.append([list_tof_dead_time[2] + MIN_TOF_BETWEEN_FRAMES,
	                                       TOF_FRAMES[-1][1]])
	for _calculated_range, _expected_range in zip(final_list_tof_frames_calculated, final_list_tof_frames_expected):
		assert _calculated_range == _expected_range

@pytest.mark.parametrize('delta_tof, above_closest_expected',
                         [(2.5e-3, 5),
                          (0.1e-3, 9),
                          (25e-3, 2)])
def test_getting_right_above_closest_divided(delta_tof, above_closest_expected):
	above_closest_divided = MakeShutterValueFile.get_above_closest_divided(delta_tof=delta_tof)
	assert above_closest_divided == above_closest_expected

def test_make_shutter_value_string():
	output_folder = "/tmp/"
	detector_offset = 6000  # micros
	detector_sample_distance = 2100   # cm
	epics_chopper_wavelength_range = [2, 10]  # Angstroms
	o_make = MakeShutterValueFile(detector_offset=detector_offset,
	                             output_folder=output_folder,
	                             detector_sample_distance=detector_sample_distance,
	                             epics_chopper_wavelength_range=epics_chopper_wavelength_range)
	list_lambda_dead_time = [3, 5, 8]
	list_tof_dead_time = MakeShutterValueFile.convert_lambda_to_tof(list_wavelength=list_lambda_dead_time,
	                                                                detector_offset=detector_offset,
	                                                                detector_sample_distance=detector_sample_distance,
	                                                                output_units='s')
	list_tof_frames = o_make.make_list_tof_frames(list_tof_dead_time=list_tof_dead_time)
	shutter_value_string = o_make.make_shutter_values_string(list_tof_frames=list_tof_frames)
	shutter_values_string_expected = "1e-06\t0.009525040036703266\t3\t10.24\n0.010325040036703264\t" + \
		"0.02014173339450544\t3\t10.24\n0.020941733394505443\t0.036066773431208704\t2\t10.24\n" + \
		                             "0.0368667734312087\t0.0159\t19\t10.24"
