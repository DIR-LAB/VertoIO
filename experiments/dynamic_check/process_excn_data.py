import os
import re
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def get_operation_type():
    while True:
        operation_type = input("Enter the operation type (read/write/rw): ").strip().lower()
        if operation_type in ['read', 'write', 'rw']:
            return operation_type
        print("Invalid input. Please enter 'read' or 'write'.")

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

def read_workload_sequence(operation_type, root_dir, seq):
    sequence_file = f"{operation_type}_sequence_{seq}.txt"
    with open(os.path.join(root_dir, sequence_file), 'r') as file:
        return [line.strip() for line in file if line.strip()]

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

            # Include all suffixes in the bw_values dictionary
            suffixes = ['Default', 'Tuning'] + [f'{workload_name}_Optimal' for workload_name in workloads]
            for suffix in suffixes:
                bw_values[suffix] = 0.0

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
                        else:
                            for workload_name in workloads:
                                if file.endswith(f'{workload_name}_optimal_output.txt'):
                                    suffix = f'{workload_name}_Optimal'
                                    update_results(results, dir_workload_name, iteration, suffix, process_file(file_path))
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

        for key in ['Default', 'Tuning'] + [f'{workload}_Optimal' for workload in workloads]:
            if relevant_results:
                aggregate_bw[key] = sum(result.get(key, 0) for result in relevant_results)

        aggregated_results.append(aggregate_bw)

    for result in aggregated_results:
        for key in ['Tuning'] + [f'{workload}_Optimal' for workload in workloads]:
            default_bw = result.get('Default', 0)
            if default_bw > 0:  # To avoid division by zero
                #improvement_percentage = ((result.get(key, 0) - default_bw) / default_bw) * 100
                improvement_factor = (result.get(key, 0)/ default_bw)
                result[f'{key} Improvement Factor'] = round(improvement_factor, 2)
            else:
                result[f'{key} Improvement Factor'] = 'N/A'  # Handle division by zero or no default improvement

    # Define fieldnames for the CSV file
    fieldnames = ['Workload Name', 'Iteration', 'Default', 'Tuning'] + \
                 [f'{workload}_Optimal' for workload in workloads] + \
                 ['Tuning Improvement Factor'] + \
                 [f'{workload}_Optimal Improvement Factor' for workload in workloads]

    # Writing to the CSV file
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

def plot_improvement_percentage(workloads_seqs, filenames, output_filepath):

    # Color pool assignment
    color_pool = ['tomato', 'dodgerblue', 'darkseagreen', 'darkorange', 'slategray', 'crimson']
    hatches = ['++','///', '|||', '\\\\\\', 'xx','...' ]

    # Plot setup
    fig, axs = plt.subplots(1, len(filenames), figsize=(24, 6), squeeze=False)  # Ensure axs is always a 2D array

    bar_width = 0.10
    error_config = {'ecolor': '0.3', 'capsize': 2}

    # Keep track of the plot objects for the legend
    subplot_labels = ['(a) Read-only Workload Sequence', '(b) Write-only Workload Sequence', '(c) Read-write Workload Sequence']  # Extend this list if you have more subplots

    for j, filename in enumerate(filenames):
        ax = axs[0][j]

        # Read the CSV file
        data = pd.read_csv(filename)
        data, workloads = modify_workload_names(data, workloads_seqs[j])
        data['Workload Name'] = data['Workload Name'].apply(transform_workload_name)
        workloads = [transform_workload_name(name) for name in workloads]

        # Filter columns for Improvement % and exclude 'Iteration'
        improvement_columns = [col for col in data.columns if "Improvement Factor" in col and col != 'Iteration']

        # Group by 'Workload Name' and calculate mean and std for each improvement metric
        grouped_data = data.groupby('Workload Name')[improvement_columns].agg(['mean', 'std'])
        grouped_data = grouped_data.reindex(workloads)

        # Preparing data for plotting
        n_groups = len(grouped_data)
        index = np.arange(n_groups)

        # Plot each improvement percentage as a separate group
        for i, column in enumerate(improvement_columns):
            means = grouped_data[column]['mean']
            stds = grouped_data[column]['std']

            if i == 0:
                custom_label = "Our Framework"
            else:
                custom_label = "Optimal of " + str(workloads[i-1])

            # Use ax.bar for vertical bars
            ax.bar(index + i*bar_width, means, bar_width, yerr=stds, color=color_pool[i+1], label=custom_label, error_kw=error_config)

        # Add a horizontal line at y=1.0
        ax.axhline(y=1.0, color='black', linewidth=1, linestyle='--', label='Default Performance')

        ax.set_xlabel('Workload Name')
        # Add subplot label
        ax.text(0.5, 1, subplot_labels[j], transform=ax.transAxes, fontsize=15, fontweight='bold', ha='center', va='bottom')
        ax.set_xticks(index + bar_width * len(improvement_columns) / 2)
        ax.set_xticklabels(grouped_data.index, rotation=45)
        ax.legend(fontsize=14)

    axs[0][0].set_ylabel('Factors of Improvement over Default Performance')

    plt.tight_layout()
    plt.savefig(output_filepath)
    plt.close()

def main():
    excn_seqs = {'read':3, 'write':2, 'rw':3}
    # operation_type = get_operation_type()
    # no_of_seq = int(input("How many sequence: "))
    workloads_seqs = []
    file_paths = []

    for operation_type, seq in excn_seqs.items():
        if operation_type == "rw":
            root_dir = f'/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/read-write/adaptivity_tests/model_k_{seq}'
        else:
            root_dir = f'/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/{operation_type}-only/adaptivity_tests/model_k_{seq}'
        workloads = read_workload_sequence(operation_type, root_dir, seq)
        workloads_seqs.append(workloads)
        print("Workloads: ", workloads)

        output_file = f'adaptivity_{operation_type}_sequence_{seq}_excn_summary.csv'
        results = process_directory(root_dir, workloads)
        write_csv(workloads, results, os.path.join(root_dir, output_file))
        file_paths.append(os.path.join(root_dir, output_file))

    plot_improvement_percentage(workloads_seqs, file_paths, '/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/dynamic_test_results.jpeg')

if __name__ == "__main__":
    main()