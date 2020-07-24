import numpy as np
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir

TOLERANCE = 1e-6
MN = 1.674927471e-27  #kg - neutron mass
H = 6.62607004e-34 #J s - Planck constant

from shutter_value_generator.make_shutter_value_file import MakeShuterValueFile
from shutter_value_generator.make_shutter_value_file import RESONANCE_SHUTTER_VALUES


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

def test_make_sure_minimum_parameters_passed_in_for_no_resonance_mode():
	with pytest.raises(AttributeError):
		MakeShuterValueFile()
	with pytest.raises(AttributeError):
		MakeShuterValueFile(output_folder="./")
	with pytest.raises(AttributeError):
		MakeShuterValueFile(output_folder="./", detector_sample_distance=1)
	with pytest.raises(AttributeError):
		MakeShuterValueFile(output_folder="./", detector_sample_distance=10, detector_offset=20)

@pytest.mark.parametrize('detector_offset, output_folder, detector_sample_distance, resonance_mode, '
                         'epics_chopper_wavelength_range',
	                      [(10, "/me/tmp/", 20, True, [10, 20]),
	                       (10, "/me/tmp/2", 20, False, [10, 20])])
def test_parameters_are_saved(detector_offset, output_folder, detector_sample_distance, resonance_mode,
                              epics_chopper_wavelength_range):
	o_make = MakeShuterValueFile(detector_offset=detector_offset,
	                             output_folder=output_folder,
	                             detector_sample_distance=detector_sample_distance,
	                             resonance_mode=resonance_mode,
	                             epics_chopper_wavelength_range=epics_chopper_wavelength_range)
	assert o_make.output_folder == output_folder
	assert o_make.detector_offset == detector_offset
	assert o_make.detector_sample_distance == detector_sample_distance
	assert o_make.epics_chopper_wavelength_range == epics_chopper_wavelength_range

def test_convert_lambda_to_tof():
	detector_offset = 5000  # micros
	detector_sample_distance = 1300  # cm
	list_lambda = [4, 5, 6]
	list_tof = MakeShuterValueFile.convert_lambda_to_tof(list_wavelength=list_lambda,
	                                                     detector_offset=detector_offset,
	                                                     detector_sample_distance=detector_sample_distance)

	list_tof_expected = convert_lambda_to_tof(list_lambda, detector_offset, detector_sample_distance)
	assert list_tof == list_tof_expected

def test_calculate_min_tof_peak_value_from_edge_of_frame():
	output_folder = "/tmp/"
	detector_offset = 0  # micros
	detector_sample_distance = 1300  # cm
	epics_chopper_wavelength_range = [10, 20] # Angstroms
	o_make = MakeShuterValueFile(detector_offset=detector_offset,
	                             output_folder=output_folder,
	                             detector_sample_distance=detector_sample_distance,
	                             epics_chopper_wavelength_range=epics_chopper_wavelength_range)
	min_tof_peak_value_from_edge_of_frame_calculated = o_make.min_tof_peak_value_from_edge_of_frame
	min_tof_peak_value_from_edge_of_frame_expected = 985.8442871587462
	assert np.abs(min_tof_peak_value_from_edge_of_frame_expected - min_tof_peak_value_from_edge_of_frame_calculated[
		0]) \
	       < 1e-3

@pytest.mark.parametrize('file_contain', [("entry1, entry2, entry3"),
                                          "entry1, entry2, entry3\nentry4, entry5, entry6"])
def test_make_ascii_file_from_string_single_entry(file_contain):
	ascii_filename = make_tmp_ascii_filename()
	MakeShuterValueFile.make_ascii_file_from_string(text=file_contain,
	                                                filename=ascii_filename)
	with open(ascii_filename, 'r') as f:
		file_created = f.readlines()

	file_expected = file_contain.split("\n")
	assert len(file_expected) == len(file_created)

	for _line_expected, _line_created in zip(file_expected, file_created):
		assert _line_created.strip() == _line_expected

def test_create_shutter_value_for_resonance_mode():
	temp_dir = gettempdir()
	o_make = MakeShuterValueFile(output_folder=temp_dir,
	                             resonance_mode=True)
	o_make.run()

	file_created_expected = Path(temp_dir) / "ShutterValues.txt"
	with open(file_created_expected, 'r') as f:
		file_contain_created = f.readline()

	file_contain_expected = RESONANCE_SHUTTER_VALUES
	assert file_contain_created == file_contain_expected

@pytest.mark.parametrize('list_wavelength_requested, epics_chopper_wavelength_range',
                         [([1, 2, 3], [1, 5]),
                          ([1, 10], [0.5, 8]),
                          ([1, 10], [1, 11]),
                          ([2, 10], [0.5, 10])])
def test_lambda_outside_epics_chopper_range_raise_error(list_wavelength_requested, epics_chopper_wavelength_range):
	detector_sample_distance = 1300
	detector_offset = 6300
	with pytest.raises(ValueError):
		MakeShuterValueFile.realign_frames_with_tof_requested(list_wavelength_requested=list_wavelength_requested,
		                                                      detector_sample_distance=detector_sample_distance,
		                                                      detector_offset=detector_offset,
		                                                      epics_chopper_wavelength_range=epics_chopper_wavelength_range)

@pytest.mark.parametrize('list_wavelength_requested, epics_chopper_wavelength_range',
                         [([10, 20], [9.8, 30]),
                          ([12, 29.9], [9.8, 30])])
def test_lambda_to_close_to_edge_of_epics_chopper_raise_error(list_wavelength_requested, epics_chopper_wavelength_range):
	detector_sample_distance = 1300
	detector_offset = 6300
	with pytest.raises(ValueError):
		MakeShuterValueFile.realign_frames_with_tof_requested(list_wavelength_requested=list_wavelength_requested,
		                                                      detector_sample_distance=detector_sample_distance,
		                                                      detector_offset=detector_offset,
		                                                      epics_chopper_wavelength_range=epics_chopper_wavelength_range)