import os
import re
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def get_operation_type():
    while True:
        operation_type = input("Enter the operation type (read/write): ").strip().lower()
        if operation_type in ['read', 'write']:
            return operation_type
        print("Invalid input. Please enter 'read' or 'write'.")

def process_raw_rate(csv_filepath):
    bw_val = 0.0
    with open(csv_filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)  # Default delimiter is comma
        for row in reader:
            # Checking if the row matches the expected pattern
            if row and row[0].strip().lower() == 'raw rate' and row[2].strip().lower() == 'mb/s':
                try:
                    bw_val = float(row[1].strip())
                    break  # Assuming you only need the first matching row
                except ValueError:
                    # In case the conversion fails, continue to the next line
                    continue
    return bw_val

def process_directory(root_dir):
    results = []
    for dirname in os.listdir(root_dir):
        if dirname.startswith('dir_'):
            # Extract workload name and iteration number
            workload_match = re.match(r'^dir_(.+?)_itern_(\d+)$', dirname)
            if workload_match:
                workload_name, iteration = workload_match.groups()
                path = os.path.join(root_dir, dirname)
                if os.path.isdir(path):
                    bw_values = {
                        'Workload Name': workload_name,
                        'Iteration': int(iteration),
                        'Default': 0.0,
                        'Tuning': 0.0
                    }
                    for file in os.listdir(path):
                        if file.endswith('-dflt-output.csv'):
                            bw_values['Default'] = process_raw_rate(os.path.join(path, file))
                        elif file.endswith('-tuned-output.csv'):
                            bw_values['Tuning'] = process_raw_rate(os.path.join(path, file))
                    results.append(bw_values)
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

def visualize_and_save_results(results, output_filepath):
    """
    Generates and saves horizontal bar plots.

    Parameters:
    - results: List of dictionaries containing the results data.
    - output_filepath: Output file path.
    """

    # Color pool assignment
    color_pool = ['tomato', 'dodgerblue', 'darkkhaki', 'darkorange', 'dimgray', 'darkcyan']
    hatches = ['++','///', '|||', '\\\\\\', 'xx','...' ]

    # Plot setup
    fig, axs = plt.subplots(1, len(results), figsize=(20, 5), squeeze=False)  # Ensure axs is always a 2D array

    bar_width = 0.25
    error_config = {'ecolor': '0.3', 'capsize': 2}

    # Keep track of the plot objects for the legend
    plots = []

    subplot_labels = ['(a)', '(b)']  # Extend this list if you have more subplots

    for i, result in enumerate(results):
        ax = axs[0][i]
        # Convert results to a DataFrame and modify workload names
        data = pd.DataFrame(result)

        # Filter columns to exclude 'Improvement %' & 'Iteration'
        perf_columns = ["Default", "Tuning"]

        # Group by 'Workload Name' to calculate mean and std deviation
        grouped = data.groupby('Workload Name')[perf_columns].agg(['mean', 'std'])
        print(grouped)
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
        ax.text(0.5, 1, subplot_labels[i], transform=ax.transAxes, fontsize=10, fontweight='bold', ha='center', va='bottom')
        ax.set_xlabel('Bandwidths (MB/s)')

    axs[0][0].set_ylabel('Workload Name')

    labels = ['Default', 'Our Framework']
    fig.legend(plots, labels, loc='upper center', ncol=2, fontsize=14)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(output_filepath)
    plt.close()

def main():
    root_dir = '/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/'
    operation_types = ['read', 'write']
    # operation_type = get_operation_type()
    results = []
    for operation_type in operation_types:
        tmp_dir = root_dir + f'h5bench_tests/{operation_type}-only/model_k_1'
        output_file = f'h5bench_excn_summary_{operation_type}.csv'
        results.append(process_directory(tmp_dir))
        write_csv(results[-1], os.path.join(tmp_dir, output_file))

    trained_wlds_img = 'h5bench_test_results.jpeg'
    visualize_and_save_results(results, os.path.join(root_dir, trained_wlds_img))

if __name__ == "__main__":
    main()
