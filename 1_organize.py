
'''

EMG analysis
Script #1 - Data organization
Dorothee Morand-Grondin
Sept 2026

'''

# Import libraries

from pathlib import Path
import re
import io
import pandas as pd

# Settings

script_folder = Path(__file__).parent # identify where this script is located
input_folder = script_folder/'input' # identify where the data files are located
organised_data_folder = script_folder/'organised_data' # where the new datafiles will be exported

left_channel = '1C' # identify the left EMG channel
right_channel = '1D' # identify the right EMG channel

# find the data in the files (among other information)

def metadata(file_path): # find participant and session id
    
    found = re.search(r'client\s*(\d+)\s*session\s*(\d+)', 
                      file_path.stem, re.IGNORECASE)
    
    if not found: # indicate if the file does not contain the expected information
        raise ValueError('file must contain client XX session YY info')
    
    participant = 'P' + found.group(1) # identify the participant id
    session = int(found.group(2)) # identify the session id
    
    return participant, session

def data_columns(data, channel): # find each hand's columns
    
    for column in data.columns: 
        if channel in column: 
            return column # return the EMG data through time only
    raise ValueError('One of the column was not found (1C or 1D)')
    
def read_file(file_path): # extract data info
    try: 
        lines = file_path.read_text(encoding='utf-8').splitlines()
    except UnicodeDecodeError: # deal with French accents
        lines = file_path.read_text(encoding='latin-1').splitlines()
        
    date = 'no-date' # starts empty
    header_row = None # starts empty
    
    for i, line in enumerate(lines): 
        if line.startswith('Date'):
            found = re.search(r'\d{4}-\d{2}-\d{2}', line) # session date YYYY-MM-DD
            if found: 
                date = found.group()
                
        if line.startswith('Heure\t') or line.startswith('Heure;'): # data headers row
            header_row = i
            separator = line[5] # ;
            break
        
    if header_row is None: 
        raise ValueError('No line starts with [Heure] as expected')
    
    data_text = '\n'.join(lines[header_row:])
    data = pd.read_csv(io.StringIO(data_text), sep=separator, dtype=str)
    data.columns = [name.strip() for name in data.columns] # remove spaces around names
    
    for column in data.columns: # French to English decimals
        data[column] = pd.to_numeric(data[column].str.replace(',', '.'), errors='coerce')
        
    data = data.dropna(axis='columns', how='all') # isolate the actual data
    data = data.dropna(subset=['Heure'])
    data = data.reset_index(drop=True)
    
    smoothed = [column for column in data.columns if column.startswith("Smoothing")] # smoothed data columns
    if len(smoothed) != 2: # give the columns clear names
        raise ValueError(f"The script expected two 'Smoothing Average' columns, it found {len(smoothed)}")
    data = data.rename(columns={
        "Heure": "time_s",
        data_columns(data, left_channel): "left_raw",
        data_columns(data, right_channel): "right_raw",
        smoothed[0]: "left_smoothed", # find the 2 smoothed columns and identify left-right
        smoothed[1]: "right_smoothed"})
    return date, data

# run all of the above for each file

organised_data_folder.mkdir(exist_ok=True) # create the folder if doesn't exist yet

files = sorted(input_folder.glob('*.txt')) # use only the .txt files
print('\nScript #1 - Data organization is running... \n')
print(f'{len(files)} .txt files found in the input folder')

for file_path in files:
    try:
        participant, session = metadata(file_path)
        date, data = read_file(file_path)
        name = f'{participant}_session{session:02d}'
        
        data.to_csv(organised_data_folder/f'{name}_{date}.csv', sep=';', decimal=',', index=False)
        
        print(f'ORGANIZED FILE  {name}')
        
    except Exception as error: # if one file has a problem, say why and go to the next one
        print(f'SKIPPED {file_path.name}: {type(error).__name__}: {error}')