import numpy as np
import pytest

TOLERANCE = 1e-6
MN = 1.674927471e-27  #kg - neutron mass
H = 6.62607004e-34 #J s - Planck constant

from shutter_value_generator.make_shutter_value_file import MakeShuterValueFile


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
	coeff = 0.3956
	list_tof = [_lambda * detector_sample_distance / coeff - detector_offset for _lambda in list_lambda]
	return list_tof

def test_get_clock_cycle_table():
	clock_cycle_data_returned = MakeShuterValueFile.get_clock_cycle_table()

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

def test_make_sure_minimum_parameters_passed_in():
	with pytest.raises(AttributeError):
		MakeShuterValueFile()
	with pytest.raises(AttributeError):
		MakeShuterValueFile(output_folder="./")
	with pytest.raises(AttributeError):
		MakeShuterValueFile(output_folder="./", detector_sample_distance=1)

def test_parameters_are_saved():
	detector_offset = 10
	output_folder = "/me/tmp"
	detector_sample_distance = 20

	o_make = MakeShuterValueFile(detector_offset=detector_offset,
	                             output_folder=output_folder,
	                             detector_sample_distance=detector_sample_distance)

	assert o_make.output_folder == output_folder
	assert o_make.detector_offset == detector_offset
	assert o_make.detector_sample_distance == detector_sample_distance

def test_convert_lambda_to_tof():
	detector_offset = 5000  # micros
	detector_sample_distance = 1300  # cm
	list_lambda = [4, 5, 6]
	list_tof = MakeShuterValueFile.convert_lambda_to_tof(list_wavelength=list_lambda,
	                                                     detector_offset=detector_offset,
	                                                     detector_sample_distance=detector_sample_distance)

	list_tof_expected = convert_lambda_to_tof(list_lambda, detector_offset, detector_sample_distance)
	assert list_tof == list_tof_expected

def test_min_tof_peak_value_from_edge_of_frame():
	output_folder = "/tmp/"
	detector_offset = 0  # micros
	detector_sample_distance = 1300  # cm
	o_make = MakeShuterValueFile(detector_offset=detector_offset,
	                             output_folder=output_folder,
	                             detector_sample_distance=detector_sample_distance)
	min_tof_peak_value_from_edge_of_frame_calculated = o_make.min_tof_peak_value_from_edge_of_frame
	min_tof_peak_value_from_edge_of_frame_expected = 985.8442871587462
	assert np.abs(min_tof_peak_value_from_edge_of_frame_expected - min_tof_peak_value_from_edge_of_frame_calculated[
		0]) \
	       < 1e-3