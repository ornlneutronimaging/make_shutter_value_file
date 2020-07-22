import argparse
import pandas as pd
from pathlib import Path

DELTA_TIME_BETWEEN_FRAMES = 0.32e-6   # s
CLOCK_CYCLE_FILE = 'clock_cycle.txt'

MN = 1.674927471e-27  #kg - neutron mass
H = 6.62607004e-34 #J s - Planck constant

TOF_FRAMES = [[1e-6, 2.5e-3],
              [2.9e-3, 5.8e-3],
              [6.2e-3, 15.9e-3]]
MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME = 0.3  # Angstroms

RESONANCE_SHUTTER_VALUES = "1e-6\t320e-6\t3\t0.16"

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
	             resonance_mode=False):
		"""
		:param output_folder:
		:param detector_sample_distance: in m
		:param detector_offset:  in micros
		:param resonance_mode: boolean
		"""
		if output_folder is None:
			raise AttributeError("output folder needs to be an existing output folder!")
		self.output_folder = output_folder

		if resonance_mode:
			pass
		else:
			if detector_sample_distance is None:
				raise AttributeError("define a detector sample distance in meters!")
			self.detector_sample_distance = detector_sample_distance

			if detector_offset is None:
				raise AttributeError("define a detector offset in micros!")
			self.detector_offset = detector_offset

			self.min_tof_peak_value_from_edge_of_frame = MakeShuterValueFile.convert_lambda_to_tof(
					list_wavelength=[MIN_LAMBDA_PEAK_VALUE_FROM_EDGE_OF_FRAME],
					detector_offset=0,
					detector_sample_distance=self.detector_sample_distance)

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

	# @staticmethod
	# def realign_frames_with_tof_requestd(list_tof=None, min_frame_threshold=0):
	# 	min_tof_peak_value_from_edge_of_frame = MakeShuterValueFile.convert_lambda_to_tof()
	#
	# 	for _tof in list_tof:





