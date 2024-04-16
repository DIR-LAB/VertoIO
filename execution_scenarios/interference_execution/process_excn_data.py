import os
import re
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def get_run_no():
    # Prompt user to input run_no
    run_no = input("Enter inference run_no: ")

    return run_no

def get_inf_types(inf_run_dir):
    # Modified to exclude directories ending with "w_dd_10g" as well as those starting with "node"
    inf_types = [dir_name for dir_name in os.listdir(inf_run_dir)
                 if os.path.isdir(os.path.join(inf_run_dir, dir_name))
                 and not dir_name.startswith('node')
                 and not dir_name.endswith('w_dd_10g')]
    print(f"Discovered inference types: {inf_types}")

    return inf_types

def read_inf_sequence(root_dir, inf_type):
    inf_wld_file = f"{inf_type}.txt"
    with open(os.path.join(root_dir, inf_wld_file), 'r') as file:
        return [line.strip() for line in file if line.strip()]

def process_final_io_ops(line_list):
    bw_val = 0.0
    for line in line_list:
        io_search = re.search(r'(\d+)\.(\d+):\s+IO Summary:\s+(\d+)\s+ops\s+(\d+)\.(\d+)\s+ops/s\s+(\d+)/(\d+)\s+rd/wr\s+(\d+)\.(\d+)mb/s\s+(\d+)\.(\d+)ms/op', line, re.IGNORECASE)
        if io_search:
            bw_val = float(io_search.group(8) + '.' + io_search.group(9))
    return bw_val

def process_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return process_final_io_ops(lines)

def update_results(results, workload_name, iteration, key, value):
    for result in results:
        if result['Workload Name'] == workload_name and result['Iteration'] == iteration:
            result[key] = value
            return

def process_directory(root_dir, workloads):
    results = []
    # Initialize results with placeholders for each iteration
    for iteration in range(1, 6):  # Iterations 1 through 5
        for workload_name in workloads:
            # Initialize a single bw_values dictionary for each workload and iteration
            bw_values = {'Workload Name': workload_name, 'Iteration': iteration}
            for suffix in ['Default', 'Tuning']:
                bw_values[suffix] = 0.0  # Initialize all values to 0.0
            results.append(bw_values)

    for dirname in os.listdir(root_dir):
        if dirname.startswith('dir_'):
            # Extract both workload name and iteration number
            match = re.match(r'^dir_(.+?)_itern_(\d+)$', dirname)
            if match:
                dir_workload_name, iteration_str = match.groups()
                iteration = int(iteration_str)
                path = os.path.join(root_dir, dirname)
                if os.path.isdir(path):
                    for file in os.listdir(path):
                        file_path = os.path.join(path, file)
                        if file.endswith('_default_output.txt'):
                            update_results(results, dir_workload_name, iteration, 'Default', process_file(file_path))
                        elif file.endswith('_tuning_output.txt'):
                            update_results(results, dir_workload_name, iteration, 'Tuning', process_file(file_path))
    return results

def write_csv(workloads, results, output_file):
    # Create a new list to store aggregated results separately
    aggregated_results = []

    # Aggregate results by workload name, keeping iteration details
    for iteration in range(1, 6):
        relevant_results = []

        for workload in workloads:
            relevant_result = [result for result in results if result['Workload Name'] == workload and result['Iteration'] == iteration]
            relevant_results.extend(relevant_result)

        aggregated_results.extend(relevant_results)
        aggregate_bw = {'Workload Name': 'Aggregate BW', 'Iteration': iteration}

        for key in ['Default', 'Tuning']:
            if relevant_results:
                aggregate_bw[key] = sum(result.get(key, 0) for result in relevant_results)

        aggregated_results.append(aggregate_bw)

    for result in aggregated_results:
        for key in ['Tuning']:
            default_bw = result.get('Default', 0)
            if default_bw > 0:  # To avoid division by zero
                improvement_percentage = ((result.get(key, 0) - default_bw) / default_bw) * 100
                result[f'{key} Improvement %'] = round(improvement_percentage, 2)
            else:
                result[f'{key} Improvement %'] = 'N/A'  # Handle division by zero or no default improvement

    # Assuming the fieldnames list needs to be updated to include the improvement percentage columns
    fieldnames = ["Workload Name", 'Iteration'] + ["Default", "Tuning"] + ["Tuning Improvement %"]

    with open(output_file, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in aggregated_results:
            writer.writerow(row)

def modify_workload_names(data, workloads):
    """
    Modifies the workload names in the DataFrame and the workloads list based on specified replacement rules.

    Parameters:
    - data: DataFrame containing the results data, including a 'Workload Name' column.
    - workloads: List containing workload names.

    Returns:
    - DataFrame with modified workload names.
    - List with modified workload names.
    """
    def replace_workload_name(name):
        # Define replacement rules
        rules = {
            'seq_r_1': 'singlestreamread',
            'seq_w_1': 'singlestreamwrite',
            'rnd_r_1': 'singlestreamreadrnd',
            'rnd_w_1': 'singlestreamwriternd'
        }

        # Apply rules
        for pattern, replacement in rules.items():
            if pattern in name:
                return name.replace(pattern, replacement)
        return name  # Return the original name if no pattern matches

    # Apply the replace_workload_name function to the 'Workload Name' column
    data['Workload Name'] = data['Workload Name'].apply(replace_workload_name)

    # Apply the replace_workload_name function to each element in the workloads list
    workloads = [replace_workload_name(name) for name in workloads]

    return data, workloads

def transform_workload_name(name):
    # Define the pattern and the replacement using named groups for clarity
    pattern = r'(?P<stream>singlestream|fivestream)(?P<op>read|write)(?P<rnd>rnd|)(?P<io>_io_)(?P<size>8k|1m|16m)'
    replacement = lambda m: f"{'s' if m.group('stream') == 'singlestream' else 'f'}_" \
                             f"{'rd' if m.group('op') == 'read' else 'wr'}_" \
                             f"{'sq' if m.group('rnd') == '' else 'rn'}_" \
                             f"{m.group('size')}"

    # Use the sub function from the re module to perform the replacement
    return re.sub(pattern, replacement, name)

def visualize_and_save_results(workloads_seqs, inf_type, file_dfs, output_filepath):

    # Color pool assignment
    color_pool = ['tomato', 'dodgerblue', 'darkkhaki', 'darkorange', 'slategray', 'darkseagreen']
    hatches = ['++','///', '|||', '\\\\\\', 'xx','...' ]

    # Plot setup
    fig, axs = plt.subplots(1, len(file_dfs), figsize=(18, 6), squeeze=False)  # Ensure axs is always a 2D array

    bar_width = 0.30
    error_config = {'ecolor': '0.3', 'capsize': 2}

    # Keep track of the plot objects for the legend
    plots = []
    subplot_labels = ['(a) Write-only Interference', '(b) Read-only Interference', '(c) Read-Write Interference']  # Extend this list if you have more subplots

    for i, file_df in enumerate(file_dfs):
        ax = axs[0][i]
        data, workloads = modify_workload_names(file_df, workloads_seqs[i])
        data['Workload Name'] = data['Workload Name'].apply(transform_workload_name)
        workloads = [transform_workload_name(name) for name in workloads]

        # Filter columns to exclude 'Improvement %' & 'Iteration'
        perf_columns = ["Default", "Tuning"]

        # Group by 'Workload Name' to calculate mean and std deviation
        grouped = data.groupby('Workload Name')[perf_columns].agg(['mean', 'std'])
        grouped = grouped.reindex(workloads)
        grouped.columns = [' '.join(col).strip() for col in grouped.columns.values]

        # Extract means and standard deviations
        means_default = grouped['Default mean']
        stds_default = grouped['Default std']
        means_tuning = grouped['Tuning mean']
        stds_tuning = grouped['Tuning std']

        # Plot setup
        n_groups = len(grouped)
        index = np.arange(n_groups)

        # Plotting horizontally
        p1 = ax.barh(index, means_default, bar_width, xerr=stds_default, label='Default', color=color_pool[0], error_kw=error_config)
        p2 = ax.barh(index + bar_width, means_tuning, bar_width, xerr=stds_tuning, label='Tuning', color=color_pool[1], error_kw=error_config)
        if not plots:  # Add only once
            plots.extend([p1, p2])

        # Invert the y-axis to have the first element at the top and the last at the bottom
        ax.invert_yaxis()
        ax.set_yticks(index + bar_width)
        ax.set_yticklabels(grouped.index)

        # Add subplot label
        ax.text(0.5, 1, subplot_labels[i], transform=ax.transAxes, fontsize=15, fontweight='bold', ha='center', va='bottom')
        ax.set_xlabel('Bandwidths (MB/s)')

    axs[0][0].set_ylabel('Workload Name')

    labels = ['Default', 'Our Framework']
    fig.legend(plots, labels, loc='upper center', ncol=2, fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(output_filepath)
    plt.close()

def visualize_data(workloads_seqs, inf_type, filenames, output_filepath):
    file_dfs = []

    for filename in filenames:
        file_df =  pd.read_csv(filename)
        file_dfs.append(file_df)

    visualize_and_save_results(workloads_seqs, inf_type, file_dfs, output_filepath)

def main():
    run_no = get_run_no()
    root_dir = f'/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/inference_tests/inf_run_{run_no}'

    inf_types = get_inf_types(root_dir)
    workloads_seqs = []
    file_paths = []
    for inf_type in inf_types:
        workloads = read_inf_sequence(root_dir, inf_type)
        workloads_seqs.append(workloads)
        print("Workloads: ", workloads)

        results = process_directory(os.path.join(root_dir, inf_type), workloads)

        output_file = f'{inf_type}_inf_{run_no}_excn_summary.csv'
        csv_file_path = os.path.join(root_dir, output_file)
        file_paths.append(csv_file_path)

        write_csv(workloads, results, csv_file_path)

    visualize_data(workloads_seqs, inf_type, file_paths, '/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/inference_test_results.jpeg')

if __name__ == "__main__":
    main()
