import pandas as pd


# set input/output paths
path_raw = '/Users/alee35/land-wars-devel-data/02speeches_dates/'
path_input = '/Users/alee35/land-wars-devel-data/04stemmed_bills/'
path_output = '/Users/alee35/land-wars-devel-data/05seed2/'

# read debates metadata file
with open(path_input + 'long_bills_stemmed_metadata.tsv', 'r') as f:
    metadata = pd.read_csv(f, sep='\t', header=None)

# read raw hansard
with open(path_raw + 'membercontributions-20161026.tsv', 'r') as f:
    text = pd.read_csv(f, sep='\t', header=None)
