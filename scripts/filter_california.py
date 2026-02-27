import pandas as pd
from tqdm import tqdm
import gc
import os
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Filter FMUCD data by country')
parser.add_argument('countries', nargs='+',
                   help='One or more countries to filter. Available: Canada, USA')
parser.add_argument('--input', default='/home/sradmin/ai-predictive-maintenance-capstone/FMUCD.csv',
                   help='Input CSV file path')
parser.add_argument('--output', help='Output CSV file path (default: data/fmucd_{countries}.csv)')
parser.add_argument('--chunk-size', type=int, default=10000,
                   help='Chunk size for processing (default: 10000)')

args = parser.parse_args()

# Set up paths
input_path = args.input
countries = args.countries
countries_str = '_'.join(c.lower() for c in countries)

if args.output:
    output_path = args.output
else:
    output_dir = "/home/sradmin/ai-predictive-maintenance-capstone/data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/fmucd_{countries_str}.csv"

chunk_size = args.chunk_size
first_chunk = True
total_rows = 0

# Estimate chunks from file size (avoids reading entire file)
file_size = os.path.getsize(input_path)
estimated_chunks = max(1, file_size // (chunk_size * 500))  # rough estimate

print(f"Processing file ({file_size / (1024**3):.2f} GB) in ~{estimated_chunks} chunks...")
print(f"Filtering for countries: {', '.join(countries)}")

reader = pd.read_csv(input_path, chunksize=chunk_size, low_memory=False)

for chunk in tqdm(reader, total=estimated_chunks, desc="Filtering"):
    # Filter for specified countries
    filtered = chunk[chunk['Country'].isin(countries)]

    if len(filtered) > 0:
        filtered.to_csv(output_path, mode='a' if not first_chunk else 'w',
                       header=first_chunk, index=False)
        first_chunk = False
        total_rows += len(filtered)

    # Free memory
    del chunk
    del filtered
    gc.collect()

print(f"\nDone! Exported {total_rows:,} records to: {output_path}")
