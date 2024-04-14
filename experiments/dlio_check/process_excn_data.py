import os
import re
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def get_operation_type():
    while True:
        operation_type = input("Enter the operation type (all_ost/single_ost): ").strip().lower()
        if operation_type in ['all_ost', 'single_ost']:
            return operation_type
        print("Invalid input. Please enter 'all_ost' or 'single_ost'.")

def process_training_io_throughput(line_list):
    bw_val = 0.0
    for line in line_list:
        # Adjusted regex to match the new line format
        io_search = re.search(r'\[METRIC\] Training I/O Throughput \(MB/second\):\s+(\d+\.\d+)', line, re.IGNORECASE)
        if io_search:
            bw_val = float(io_search.group(1))  # Extract the first (and only) capture group
            break  # Assuming you want to stop after the first match
    return bw_val


def process_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return process_training_io_throughput(lines)

def update_results(results, workload_name, iteration, key, value):
    # Look for an existing entry
    for result in results:
        if result['Workload Name'] == workload_name and result['Iteration'] == iteration:
            result[key] = value
            return  # Exit the function after updating

    # If no existing entry is found, create a new one
    new_entry = {
        'Workload Name': workload_name,
        'Iteration': iteration,
        key: value
    }
    results.append(new_entry)

def process_directory(root_dir):
    results = []
    for filename in os.listdir(root_dir):
        workload_match = re.match(r'^(.+?)_itern_(\d+)', filename)
        if workload_match:
            workload_name, iteration = workload_match.groups()
            if filename.endswith('_default_output.txt'):
                update_results(results, workload_name, iteration, 'Default', process_file(os.path.join(root_dir, filename)))
            elif filename.endswith('_tuning_output.txt'):
                update_results(results, workload_name, iteration, 'Tuning', process_file(os.path.join(root_dir, filename)))
    return results

def write_csv(results, output_file):
    # Sort the results by "Workload Name" and then by "Iteration"
    sorted_results = sorted(results, key=lambda x: (x['Workload Name'], x['Iteration']))

    with open(output_file, 'w', newline='') as file:
        # Include "Iteration" in the fieldnames
        writer = csv.DictWriter(file, fieldnames=["Workload Name", "Iteration", "Default", "Tuning"])
        writer.writeheader()
        for row in sorted_results:
            # Ensure the row dictionary includes the "Iteration" key-value pair
            writer.writerow(row)

def visualize_and_save_results(results, output_filepath, operation_types):
    """
    Generates and saves horizontal bar plots.

    Parameters:
    - results: List of dictionaries containing the results data.
    - output_filepath: Output file path.
    """
    # Color pool assignment
    color_pool = ['tomato', 'dodgerblue', 'darkkhaki', 'darkorange', 'slategray', 'darkseagreen']
    hatches = ['++','///', '|||', '\\\\\\', 'xx','...' ]

    # Plot setup
    fig, ax = plt.subplots(1, 1, figsize=(8, 4))

    bar_width = 0.30
    error_config = {'ecolor': '0.3', 'capsize': 2}
    concatenated_data = []

    for i, result in enumerate(results):
        # Convert results to a DataFrame and modify workload names
        data = pd.DataFrame(result)# Define a mapping based on your operation_type condition
        operation_type = operation_types[i]

        if operation_type == "single_ost":
            name_mapping = {
                "bert_v100_custom": "Bert\n(1 OST, 1 Thread)",
                "megatron_deepspeed_custom": "Megatron-Deepspeed\n(1 OST, 1 Thread)"
            }
        elif operation_type == "all_ost":
            name_mapping = {
                "bert_v100_custom": "Bert\n(All OST, 4 Threads)",
                "megatron_deepspeed_custom": "Megatron-Deepspeed\n(All OST, 4 Threads)"
            }

        # Replace 'Workload Name' in the DataFrame according to the mapping
        data['Workload Name'] = data['Workload Name'].map(name_mapping)
        concatenated_data.append(data)

    data = pd.concat(concatenated_data, ignore_index=True)

    # Filter columns to exclude 'Improvement %' & 'Iteration'
    perf_columns = ["Default", "Tuning"]

    # Group by 'Workload Name' to calculate mean and std deviation
    grouped = data.groupby('Workload Name')[perf_columns].agg(['mean', 'std'])
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
    ax.barh(index, means_default, bar_width, xerr=stds_default, label='Default', color=color_pool[0], error_kw=error_config)
    ax.barh(index + bar_width, means_tuning, bar_width, xerr=stds_tuning, label='Our Framework', color=color_pool[1], error_kw=error_config)

    # Invert the y-axis to have the first element at the top and the last at the bottom
    ax.invert_yaxis()

    ax.set_ylabel('Workload Name')
    ax.set_xlabel('Bandwidths (MB/s)')
    ax.set_yticks(index + bar_width)
    ax.set_yticklabels(grouped.index)
    ax.legend(loc='upper right', ncol=2, fontsize=10)

    plt.tight_layout()
    plt.savefig(output_filepath)
    plt.close()

def main():
    root_dir = '/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/'
    # operation_type = get_operation_type()
    operation_types = ['all_ost', 'single_ost']
    results = []

    for operation_type in operation_types:
        tmp_dir = root_dir + f'dlio_tests/{operation_type}/results'
        output_file = f'dlio_excn_summary_{operation_type}.csv'
        results.append(process_directory(tmp_dir))
        write_csv(results[-1], os.path.join(tmp_dir, output_file))

    trained_wlds_img = 'dlio_test_results.jpeg'
    visualize_and_save_results(results, os.path.join(root_dir, trained_wlds_img), operation_types)

if __name__ == "__main__":
    main()
