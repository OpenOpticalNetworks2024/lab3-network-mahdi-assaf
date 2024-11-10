import json
import numpy as np
import pandas as pd
from pathlib import Path
from core.elements import Signal_information, Node, Line, Network
from core.math_utils import lin2db, db2lin

# Constants
ROOT = Path(__file__).parent.parent
INPUT_FOLDER = ROOT / 'resources'
file_input = INPUT_FOLDER / 'nodes.json'
SIGNAL_POWER = 1e-3  # Signal power in Watts (1 mW)

# Load JSON data
with open(file_input, 'r') as file:
    data = json.load(file)

# Initialize Network
network = Network(file_input)
network.connect()

# Initialize an empty DataFrame to store results
columns = ['Path', 'Total Latency (s)', 'Total Noise (W)', 'SNR (dB)']
df = pd.DataFrame(columns=columns)

# Iterate over all node pairs and calculate paths, latency, noise, and SNR
for start_node in network.nodes:
    for end_node in network.nodes:
        if start_node != end_node:
            paths = network.find_paths(start_node, end_node)
            for path in paths:
                signal_info = Signal_information(signal_power=SIGNAL_POWER, path=path.copy())
                network.propagate(signal_info)

                # Calculate SNR in dB
                total_noise = signal_info.noise_power
                snr_db = lin2db(signal_info.signal_power / total_noise) if total_noise > 0 else float('inf')

                # Append results to DataFrame
                path_str = '->'.join(path)
                df = df._append({
                    'Path': path_str,
                    'Total Latency (s)': signal_info.latency,
                    'Total Noise (W)': total_noise,
                    'SNR (dB)': snr_db
                }, ignore_index=True)

OUTPUT_FOLDER = ROOT / 'resources' / 'output'
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

file_output = OUTPUT_FOLDER / 'weighted_paths.csv'
df.to_csv(file_output, index=False)
# Display the DataFrame
df.reset_index(drop=True, inplace=True)
print(df)
