import numpy as np
from pytest import approx

TOLERANCE = 1e-6


from shutter_value_generator import make_shutter_value_file

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

def test_get_clock_cycle_table():
	clock_cycle_data_returned = make_shutter_value_file.get_clock_cycle_table()

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
