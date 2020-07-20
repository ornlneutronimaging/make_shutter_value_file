import argparse
import pandas as pd
from pathlib import Path

DELTA_TIME_BETWEEN_FRAMES = 0.32   # micros
CLOCK_CYCLE_FILE = 'clock_cycle.txt'

parser = argparse.ArgumentParser(description="Generate ShutterValue.txt file used by the MCP detector")
parser.add_argument('--output', default='./', help='output folder where the ShutterValue.txt file will be created')

args = parser.parse_args()

def get_clock_cycle_table():
	full_file_name = Path(__file__).parent / CLOCK_CYCLE_FILE
	assert Path(full_file_name).exists()

	clock_cycle_data = pd.read_csv(full_file_name,
	                               names=['Clock', 'Divided', 'TimeBin(micros)', 'Range(ms)'],
	                               skiprows=1)
	return clock_cycle_data














