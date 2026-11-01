
'''

EMG analysis
Script #2 - Data cleaning
Dorothee Morand-Grondin
Sept 2026

'''

# Import libraries

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Settings

script_folder = Path(__file__).parent # identify where this script is located
input_folder = script_folder/'organised_data' # the data made by script #1
clean_data_folder = script_folder/'clean_data' # where the clean datafiles will be exported
check_folder = script_folder/'cleaning_check' # graphs and table to track the cleaning
criteria_file = script_folder/'criteria.txt' # the cleaning criteria (can be modified)

left_color = '#2a78d6' # color for left hand signal
right_color = '#eb6834' # color for right hand signal
replaced_color = '#ff0000' # bright red: discarded values
not_task_color = "#817575" # gray: time not taken into account (not in the task)

parts = ['left', 'right', 'both'] # 3 parts of the biofeedback session, always in this order

def read_criteria(path): # Read the criteria from criteria.txt

    criteria = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line == '' or line.startswith('#'): # skip empty lines and explanations
            continue
        name, value = line.split('=')
        value = value.strip().replace(',', '.') # decimals with a comma or a dot, both work
        if '-' in value: # a range, e.g. 20-30
            low, high = value.split('-') # split high and low values
            criteria[name.strip()] = (float(low), float(high))
        else:
            try: # a single number, e.g. 50
                criteria[name.strip()] = float(value)
            except ValueError: # a word, e.g. smoothed
                criteria[name.strip()] = value.strip('\'"')
    return criteria

criteria = read_criteria(criteria_file)
min_uv = criteria['min_uv'] # values below this are discarded
max_uv = criteria['max_uv'] # values above this are discarded
max_sd = criteria['max_sd'] # values further than this many SD from the rolling mean are discarded
rolling_secs = criteria['rolling_secs'] # the rolling window: the 20 s around each value
min_part_secs = criteria['min_part_secs'] # each part (left, right, both) lasts at least this long
skip_start_secs = criteria['secondes_rejetees_debut'] # seconds removed at the start of every recording
skip_end_secs = criteria['secondes_rejetees_fin'] # seconds removed at the end of every recording
signal = criteria['signal'] # the signal to clean: 'smoothed' or 'raw' (columns left_smoothed / left_raw)
if signal not in ['smoothed', 'raw']: # prevent error
    raise ValueError(f'In criteria.txt, "signal" must be either "smoothed" or "raw", not {signal}')

# Find the task and its 3 parts

def find_parts(data, sampling_rate):

    time = data['time_s'].to_numpy()
    left = data[f'left_{signal}'].to_numpy()
    right = data[f'right_{signal}'].to_numpy()

    # find start and end of the task (sample numbers 0, 1, 2, ...)
    first = np.flatnonzero((left > 0) & (right > 0))[0] # first sample with a signal
    last = np.flatnonzero((np.diff(left) != 0) | (np.diff(right) != 0))[-1] + 1 # while signal still moves

    # remove the seconds chosen in criteria.txt at the start and at the end of the recording
    # (with 0 seconds, nothing changes)
    first = max(first, np.searchsorted(time, time[0] + skip_start_secs))
    last = min(last, np.searchsorted(time, time[-1] - skip_end_secs, side='right') - 1)

    # prepare the values between the start and the end
    values = np.log(np.clip(np.column_stack([left, right])[first:last + 1], 0.01, None)) # log so that all changes count as much
    values = (values - values.mean(axis=0)) / values.std(axis=0) # standardise (mean 0, SD 1)
    n = len(values)
    min_len = int(min_part_secs * sampling_rate) 

    # running totals
    total = np.vstack([np.zeros(2), np.cumsum(values, axis=0)])
    total_sq = np.vstack([np.zeros(2), np.cumsum(values ** 2, axis=0)])

    def variation(a, b): # sum of squared differences from the mean, samples a to b
        count = np.reshape(b - a, (-1, 1))
        s = total[b] - total[a]
        s2 = total_sq[b] - total_sq[a]
        return (s2 - s ** 2 / count).sum(axis=1)

    def best_change(a, b): # best single change between samples a and b
        candidates = np.arange(a + min_len, b - min_len + 1)
        if len(candidates) == 0: # too short to be split into 2 parts
            return None, -np.inf
        score = variation(a, candidates) + variation(candidates, b)
        i = np.argmin(score)
        improvement = variation(a, b)[0] - score[i] # how much this change helps
        return candidates[i], improvement

    # find the biggest change in the task
    change, _ = best_change(0, n)
    if change is None: # prevent error
        raise ValueError(f'The task is shorter than 3 x {min_part_secs:g} s (cannot identify the 3 sections of left/right/both hands biofeedback)')

    # find the next biggest change, before or after the first one
    change_before, improvement_before = best_change(0, change)
    change_after, improvement_after = best_change(change, n)
    if change_before is None and change_after is None: # prevent error
        raise ValueError(f'The task is shorter than 3 x {min_part_secs:g} s (cannot identify the 3 sections of left/right/both hands biofeedback)')
    if improvement_before > improvement_after:
        change1, change2 = change_before, change
    else:
        change1, change2 = change, change_after

    return [time[first], time[first + change1], time[first + change2], time[last]]

def label_parts(data, times): # add a 'part' column: left, right, both, or outside (= not task)

    data['part'] = 'outside' # before the start / after the end of the task
    for part, start, end in zip(parts, times[:-1], times[1:]):
        inside = (data['time_s'] >= start) & (data['time_s'] < end)
        data.loc[inside, 'part'] = part
    return data

# Discard and replace the 'bad' values

def clean_signal(values, sampling_rate): # values = the signal of ONE hand in ONE part

    window = int(rolling_secs * sampling_rate) 

    # values outside 0-50 uV (or missing) are discarded
    bad = values.isna() | (values < min_uv) | (values > max_uv)

    # values more than 3 SD from the mean are discarded
    good = values.where(~bad) # discarded values become empty (NaN)
    rolling_mean = good.rolling(window, center=True, min_periods=1).mean()
    rolling_sd = good.rolling(window, center=True, min_periods=1).std()
    bad = bad | ((values - rolling_mean).abs() > max_sd * rolling_sd)

    # replace the discarded values by the mean of the GOOD values in the 20 s around them
    good = values.where(~bad)
    replacement = good.rolling(window, center=True, min_periods=1).mean()
    clean = good.fillna(replacement)

    return clean, bad

# graph: cleaning check

def plot_cleaning(data, times, name, save_as): # replaced values in red, not task in gray

    in_task = data['part'] != 'outside'
    fig, axes = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

    for ax, side, color in zip(axes, ['left', 'right'], [left_color, right_color]):
        original = data[f'{side}_{signal}'] # the signal before cleaning
        replaced = data[f'{side}_replaced']
        pct = 100 * replaced[in_task].mean()

        # not in the task
        ax.axvspan(data['time_s'].iloc[0], times[0], color=not_task_color, zorder=0,
                   label='not in the task (not used)')
        ax.axvspan(times[-1], data['time_s'].iloc[-1], color=not_task_color, zorder=0)
        ax.plot(data['time_s'], original.where(~in_task), color='dimgray', linewidth=0.5)

        # in the task
        ax.plot(data['time_s'], original.where(in_task), color=color, linewidth=0.5,
                label='signal before cleaning')
        ax.plot(data['time_s'], original.where(replaced), color=replaced_color, linewidth=1,
                marker='.', markersize=2, label=f'discarded (> {max_uv:g} µV or > {max_sd:g} SD), replaced by the {rolling_secs:g} s mean')
        ax.axhline(max_uv, color=replaced_color, linestyle=':', linewidth=1) # the 50 uV limit

        for t in times: # dashed lines at the start + 2 changes 
            ax.axvline(t, color='black', linestyle='--', linewidth=2.5)
        for part, start, end in zip(parts, times[:-1], times[1:]): # name + seconds of each part
            ax.text((start + end) / 2, 0.97, f'{part.upper()} ({end - start:.0f} s)',
                    transform=ax.get_xaxis_transform(), ha='center', va='top', fontweight='bold',
                    bbox=dict(facecolor='white', edgecolor='none', alpha=0.8)) # white box: readable over the signal

        ax.set_ylim(0, 70)
        ax.set_ylabel('EMG (µV)')
        ax.set_title(f'{side.upper()} hand: {pct:.1f}% of the task replaced', loc='left', fontweight='bold')

    axes[0].legend(loc='lower right', bbox_to_anchor=(1, 1.08), ncol=3, frameon=False, fontsize=9)
    axes[-1].set_xlabel('Time (s)')
    axes[-1].set_xlim(data['time_s'].iloc[0], data['time_s'].iloc[-1])
    fig.suptitle(f'{name}: data cleaning check ({signal} signal)', x=0.01, ha='left', fontsize=13)
    fig.tight_layout()
    fig.savefig(save_as, dpi=150)
    plt.close(fig) 

# run everything for each file

for folder in [clean_data_folder, check_folder]:
    folder.mkdir(exist_ok=True) # create the folders if they don't exist yet

files = sorted(input_folder.glob('P*_session*.csv')) # the sessions (not sessions.csv)
print('\nScript #2 - Data cleaning is running...\n')
print(f'{len(files)} files found in the organised_data folder')

summary = [] # one row per session and part
durations = [] # one row per session

for file_path in files:
    try:
        name = file_path.stem 
        data = pd.read_csv(file_path, sep=';', decimal=',') # same format as saved by script #1
        sampling_rate = (len(data) - 1) / (data['time_s'].iloc[-1] - data['time_s'].iloc[0]) # 256
        

        # find the task and its 3 parts
        times = find_parts(data, sampling_rate)
        data = label_parts(data, times)

        # clean each hand, each part separately
        for side in ['left', 'right']:
            data[f'{side}_clean'] = np.nan # empty to start, stays empty outside the task
            data[f'{side}_replaced'] = False # True where the value was discarded and replaced
            for part in parts:
                rows = data['part'] == part
                clean, bad = clean_signal(data.loc[rows, f'{side}_{signal}'], sampling_rate)
                data.loc[rows, f'{side}_clean'] = clean
                data.loc[rows, f'{side}_replaced'] = bad

        # save the clean data and the graph
        columns = ['time_s', 'part', 'left_clean', 'right_clean', 'left_replaced', 'right_replaced']
        clean_table = data[columns].rename(columns={'part': 'biofeedback'}) # change name
        clean_table.to_csv(clean_data_folder/f'{name}.csv', sep=';', decimal=',', index=False)
        plot_cleaning(data, times, name, check_folder/f'{name}_cleaning.png') # graph to check the cleaning

        for part in parts: # % of values replaced, per part and hand
            rows = data['part'] == part
            summary.append({'session': name, 'biofeedback': part,
                            'pct_left_replaced': round(100 * data.loc[rows, 'left_replaced'].mean(), 2),
                            'pct_right_replaced': round(100 * data.loc[rows, 'right_replaced'].mean(), 2)})
        durations.append({'session': name, # duration (s) of each part found in this session
                          'left_s': round(times[1] - times[0], 1),
                          'right_s': round(times[2] - times[1], 1),
                          'both_s': round(times[3] - times[2], 1)})
        print(f'CLEANED DATA {name}')

    except Exception as error: # if one file has a problem, say why and go to the next one
        print(f'SKIPPED {file_path.name}: {type(error).__name__}: {error}')

# the % replaced, for all sessions
pd.DataFrame(summary).to_csv(check_folder/'cleaning_summary.csv', sep=';', decimal=',', index=False)

# the duration of the 3 parts, for all sessions
pd.DataFrame(durations).to_csv(check_folder/'section_durations.csv', sep=';', decimal=',', index=False)
