'''

EMG analysis workflow
Script #3 - Data computation
Dorothee Morand-Grondin
Sept 2026

'''

# Import libraries

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

# Settings

script_folder = Path(__file__).parent # identify where this script is located
input_folder = script_folder/'clean_data' # the data made by script #2
results_folder = script_folder/'results' # where the results will be exported
session_graphs_folder = results_folder/'session_graphs'
criteria_file = script_folder/'criteria.txt' # the biofeedback ranges (can be modified)

parts = ['left', 'right', 'both'] # 3 parts of the biofeedback session
hands = ['left', 'right']

hand_colors = {'left': '#2a78d6', 'right': '#eb6834'} # blue, orange
all_sessions = range(1, 11) # the metrics files always contain sessions 1 to 10 (NA if no data)
metric_columns = ['avg_uV', 'sd_uV', 'rms_uV', 'pct_time_bfb'] # the metrics of each hand in each part

# read the criteria from criteria.txt

def read_criteria(path): 
    criteria = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line == '' or line.startswith('#'): # skip empty lines and explanations
            continue
        name, value = line.split('=') # value is after the '='
        value = value.strip().replace(',', '.') # decimals with a comma or a dot both work
        if '-' in value: # range
            low, high = value.split('-')
            criteria[name.strip()] = (float(low), float(high))
        else:
            try: # single number
                criteria[name.strip()] = float(value)
            except ValueError: # a word, e.g. smoothed (quotes are ignored)
                criteria[name.strip()] = value.strip('\'"')
    return criteria

criteria = read_criteria(criteria_file)
trained_range = criteria['trained_range'] # uV: target range for the hand being trained
other_range = criteria['other_range'] # uV: target range for the other hand

# session information from the file name

def metadata(file_path):
    found = re.search(r'(P\d+)_session(\d+)_?(\d{4}-\d{2}-\d{2})?', file_path.stem)
    if not found:
        raise ValueError('file name must look like P06_session05_2026-03-19')

    participant = found.group(1)
    session = int(found.group(2))
    date = found.group(3) or 'no-date' # the date is optional in the name

    return participant, session, date

# metrics of one hand in one part

def target_range(hand, part): # which target range applies to this hand in this part

    if part == hand or part == 'both': # the hand being trained
        return trained_range
    return other_range # if not, the other hand

def compute_metrics(values, hand, part):

    low, high = target_range(hand, part)
    in_range = (values >= low) & (values <= high) # true when value is in the range

    return {'avg_uV': round(values.mean(), 3), # moyenne
            'sd_uV': round(values.std(), 3), # ecart type
            'rms_uV': round(np.sqrt((values ** 2).mean()), 3), # root mean square
            'target_range_uV': f'{low:g}-{high:g}', # just a reminder here
            'pct_time_bfb': round(100 * in_range.mean(), 1)} # % time in biofeedback

# graph of one session: 3 panels (left, right, both parts)

def plot_session(data, session_rows, name, save_as):

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    top = data[['left_clean', 'right_clean']].max().max() * 1.1 # same scale for all panels

    for ax, part in zip(axes, parts):
        part_data = data[data['biofeedback'] == part]
        text = [] # mean and % time in biofeedback of each hand, written above the panel
        for hand in hands:
            ax.plot(part_data['time_s'], part_data[f'{hand}_clean'], color=hand_colors[hand],
                    linewidth=0.5, label=f'{hand.capitalize()} hand')
            m = session_rows[(session_rows['hand'] == hand) & (session_rows['biofeedback'] == part)].iloc[0]
            text.append(f"{hand.capitalize()}: {m['avg_uV']:.2f} µV, "
                        f"{m['pct_time_bfb']:.1f}% in {m['target_range_uV']} µV")

        ax.set_title(f'{part.capitalize()} biofeedback', loc='left', fontweight='bold')
        ax.set_title('    '.join(text), loc='right', fontsize=10)
        ax.set_ylim(0, top)
        ax.set_ylabel('EMG (µV)')
        ax.set_xlabel('Time (s)')

    axes[0].legend(loc='lower right', bbox_to_anchor=(1, 1.12), ncol=2, frameon=False)
    fig.suptitle(name, x=0.01, ha='left', fontsize=14, fontweight='bold')
    fig.tight_layout()
    fig.savefig(save_as, dpi=150)
    plt.close(fig) 

# run everything for each file

for folder in [results_folder, session_graphs_folder]:
    folder.mkdir(exist_ok=True) # create the folders if they don't exist yet

files = sorted(input_folder.glob('P*_session*.csv'))
print('\nScript #3 - Data computation is running...\n')
print(f'{len(files)} sessions found in the clean_data folder') # pour le suivi 

rows = [] # one row per session, hand and part

for file_path in files:
    try:
        participant, session, date = metadata(file_path)
        data = pd.read_csv(file_path, sep=';', decimal=',') # same format as saved by script #2

        session_rows = [] # the 6 rows of this session (2 hands x 3 parts)
        for part in parts:
            part_data = data[data['biofeedback'] == part] # only this part ('outside' is never used)
            for hand in hands:
                metrics = compute_metrics(part_data[f'{hand}_clean'], hand, part)
                session_rows.append({'participant': participant, 'session': session, 'date': date,
                                     'hand': hand, 'biofeedback': part, **metrics})
        rows.extend(session_rows)

        plot_session(data, pd.DataFrame(session_rows), file_path.stem,
                     session_graphs_folder/f'{file_path.stem}.png')

        print(f'COMPUTED METRICS {file_path.stem}')

    except Exception as error: # if one file has a problem, say why and go to the next one
        print(f'SKIPPED {file_path.name}: {type(error).__name__}: {error}')

# metrics_long: one row per participant, session, part and hand (as before)
# every participant gets sessions 1 to 10: the sessions without data are filled with NA for now

metrics_long = pd.DataFrame(rows)
participants = sorted(metrics_long['participant'].unique())
sessions = sorted(set(all_sessions) | set(metrics_long['session'])) # 1 to 10 (+ any session above 10)

all_rows = pd.MultiIndex.from_product([participants, sessions, parts, hands],
                                      names=['participant', 'session', 'biofeedback', 'hand']).to_frame(index=False)
metrics_long = all_rows.merge(metrics_long, on=['participant', 'session', 'biofeedback', 'hand'], how='left')

for i, row in metrics_long.iterrows(): 
    low, high = target_range(row['hand'], row['biofeedback'])
    metrics_long.loc[i, 'target_range_uV'] = f'{low:g}-{high:g}'

metrics_long = metrics_long[['participant', 'session', 'date', 'hand', 'biofeedback',
                             'avg_uV', 'sd_uV', 'rms_uV', 'target_range_uV', 'pct_time_bfb']]
metrics_long.to_csv(results_folder/'metrics_long.csv', sep=';', decimal=',', index=False, na_rep='NA')

# metrics_wide: one row per participant
# columns: s01_date, then s01_left_bfb_left_hand_avg_uV, s01_left_bfb_left_hand_sd_uV, ... up to s10

values = metrics_long.set_index(['participant', 'session', 'biofeedback', 'hand'])
wide_columns = {'participant': participants}

for session in sessions:

    wide_columns[f's{session:02d}_date'] = [values.loc[(p, session, 'left', 'left'), 'date'] for p in participants]
    for part in parts:
        for hand in hands:
            for metric in metric_columns:
                column = f's{session:02d}_{part}_bfb_{hand}_hand_{metric}'
                wide_columns[column] = [values.loc[(p, session, part, hand), metric] for p in participants]

metrics_wide = pd.DataFrame(wide_columns)
metrics_wide.to_csv(results_folder/'metrics_wide.csv', sep=';', decimal=',', index=False, na_rep='NA')

print(f'Done! results/metrics_long.csv ({len(metrics_long)} rows) and '
      f'results/metrics_wide.csv ({len(metrics_wide)} participants)')
