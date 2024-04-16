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
                        'Tuning': 0.0,
                        'Optimal': 0.0
                    }
                    for file in os.listdir(path):
                        if file.endswith('_default_output.txt'):
                            bw_values['Default'] = process_file(os.path.join(path, file))
                        elif file.endswith('_tuning_output.txt'):
                            bw_values['Tuning'] = process_file(os.path.join(path, file))
                        elif file.endswith('_optimal_output.txt'):
                            bw_values['Optimal'] = process_file(os.path.join(path, file))
                    results.append(bw_values)
    return results

def write_csv(results, output_file):
    # Sort the results by "Workload Name" and then by "Iteration"
    sorted_results = sorted(results, key=lambda x: (x['Workload Name'], x['Iteration']))
    
    with open(output_file, 'w', newline='') as file:
        # Include "Iteration" in the fieldnames
        writer = csv.DictWriter(file, fieldnames=["Workload Name", "Iteration", "Default", "Tuning", "Optimal"])
        writer.writeheader()
        for row in sorted_results:
            # Ensure the row dictionary includes the "Iteration" key-value pair
            writer.writerow(row)

def modify_workload_names(data):
    """
    Modifies the workload names in the DataFrame based on specified replacement rules.

    Parameters:
    - data: DataFrame containing the results data, including a 'Workload Name' column.

    Returns:
    - DataFrame with modified workload names.
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

    return data

def transform_workload_name(name):
    # Define the pattern and the replacement using named groups for clarity
    pattern = r'(?P<stream>singlestream|fivestream)(?P<op>read|write)(?P<rnd>rnd|)(?P<io>_io_)(?P<size>8k|1m|16m)'
    replacement = lambda m: f"{'s' if m.group('stream') == 'singlestream' else 'f'}_" \
                             f"{'rd' if m.group('op') == 'read' else 'wr'}_" \
                             f"{'sq' if m.group('rnd') == '' else 'rn'}_" \
                             f"{m.group('size')}"

    # Use the sub function from the re module to perform the replacement
    return re.sub(pattern, replacement, name)

def visualize_and_save_results_single(results, output_filepath):
    """
    Generates and saves a plot with subplots for both singlestream and fivestream workloads together,
    using one set of legends for the entire figure.

    Parameters:
    - results: List of dictionaries containing the results data.
    - output_filepath: File path for the output plot.
    """
    # Define workload categories
    workload_categories = ['s_', 'f_']

    # Color pool assignment
    color_pool = ['tomato', 'dodgerblue', 'darkseagreen', 'darkorange', 'slategray', 'crimson']
    hatches = ['++','///', '|||', '\\\\\\', 'xx','...' ]

    # Plot setup
    fig, axs = plt.subplots(len(workload_categories), len(results), figsize=(12, 12), squeeze=False)  # Ensure axs is always a 2D array

    bar_width = 0.25
    error_config = {'ecolor': '0.3', 'capsize': 2}

    # Keep track of the plot objects for the legend
    plots = []

    subplot_labels = ['(a) READ Workloads, TRAINED', '(b) READ Workloads, UNTRAINED', '(c) WRITE Workloads, TRAINED', '(d) WRITE Workloads, UNTRAINED']  # Extend this list if you have more subplots

    for i, result in enumerate(results):
        # Convert results to a DataFrame and modify workload names
        data = pd.DataFrame(result)
        data = modify_workload_names(data)
        data['Workload Name'] = data['Workload Name'].apply(transform_workload_name)

        for j, category in enumerate(workload_categories):
            ax = axs[i][j]
            # Filter data for the current category
            category_data = data[data['Workload Name'].str.contains(category)]

            if not category_data.empty:
                # Group by 'Workload Name' to calculate mean and std deviation
                grouped = category_data.groupby('Workload Name').agg(['mean', 'std'])
                grouped.columns = [' '.join(col).strip() for col in grouped.columns.values]

                # Identify where 'Optimal mean' is less than 'Default mean' and update those rows in 'Optimal mean'
                grouped.loc[grouped['Optimal mean'] < grouped['Default mean'], 'Optimal mean'] = grouped['Default mean']

                n_groups = len(grouped)
                index = np.arange(n_groups)

                # Plotting
                p1 = ax.barh(index + 2 * bar_width, grouped['Default mean'], bar_width, xerr=grouped['Default std'], color=color_pool[0], error_kw=error_config)
                p2 = ax.barh(index + bar_width, grouped['Tuning mean'], bar_width, xerr=grouped['Tuning std'], color=color_pool[1], error_kw=error_config)
                p3 = ax.barh(index, grouped['Optimal mean'], bar_width, xerr=grouped['Optimal std'], color=color_pool[2], error_kw=error_config)
                if not plots:  # Add only once
                    plots.extend([p1, p2, p3])

                ax.set_yticks(index + bar_width)
                ax.set_yticklabels(grouped.index)

                # Add subplot label
                ax.text(0.5, 1, subplot_labels[i*len(workload_categories) + j], transform=ax.transAxes, fontsize=15, fontweight='bold', ha='center', va='bottom')

    axs[0][0].set_ylabel('Workload Name')
    axs[1][0].set_xlabel('Bandwidths (MB/s)')
    axs[1][1].set_xlabel('Bandwidths (MB/s)')

    labels = ['Default', 'Our Framework', 'Optimal']
    fig.legend(plots, labels, loc='upper center', ncol=3, fontsize=14)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(output_filepath)
    plt.close()

def visualize_and_save_results(results, output_filepath_template):
    """
    Generates and saves horizontal bar plots for singlestream and fivestream workloads separately.

    Parameters:
    - results: List of dictionaries containing the results data.
    - output_filepath_template: Template for the output file path, expecting a placeholder for the plot type.
    """
    # Convert results to a DataFrame and modify workload names
    data = pd.DataFrame(results)
    data = modify_workload_names(data)

    # Define workload categories to plot separately
    workload_categories = ['singlestream', 'fivestream']
    training_status = ['trained', 'untrained']

    for category, status in zip(workload_categories, training_status):
        # Filter data for the current category
        category_data = data[data['Workload Name'].str.contains(category)]

        # Continue only if there is data for the current category
        if not category_data.empty:
            # Group by 'Workload Name' to calculate mean and std deviation
            grouped = category_data.groupby('Workload Name').agg(['mean', 'std'])
            grouped.columns = [' '.join(col).strip() for col in grouped.columns.values]

            # Extract means and standard deviations
            means_default = grouped['Default mean']
            stds_default = grouped['Default std']
            means_tuning = grouped['Tuning mean']
            stds_tuning = grouped['Tuning std']
            means_optimal = grouped['Optimal mean']
            stds_optimal = grouped['Optimal std']

            # Plot setup
            n_groups = len(grouped)
            index = np.arange(n_groups)
            bar_width = 0.25
            opacity = 0.8
            error_config = {'ecolor': '0.3', 'capsize': 2}
            fig, ax = plt.subplots(figsize=(10, 6))

            # Get the current color cycle
            colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

            # Define the shift you want, for example, shift by 1
            shift = -3
            shifted_colors = colors[shift:shift+1] + colors[:shift]  # Rotate the color list

            # Set the new shifted color cycle for the axes
            ax.set_prop_cycle(color=shifted_colors)

            # Plotting horizontally
            ax.barh(index + 2 * bar_width, means_default, bar_width, xerr=stds_default, label='Default', alpha=opacity, error_kw=error_config)
            ax.barh(index + bar_width, means_tuning, bar_width, xerr=stds_tuning, label='Tuning', alpha=opacity, error_kw=error_config)
            ax.barh(index, means_optimal, bar_width, xerr=stds_optimal, label='Optimal', alpha=opacity, error_kw=error_config)

            ax.set_ylabel('Workload Name')
            ax.set_xlabel('Bandwidths (MB/s)')
            ax.set_title(f'{status.capitalize()} Workloads I/O Performance Comparison')
            ax.set_yticks(index + bar_width)
            ax.set_yticklabels(grouped.index)
            ax.legend()

            plt.tight_layout()

            # Save the plot for the current category
            plt.savefig(output_filepath_template.format(status))
            plt.close()

def main():
    root_dir = '/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/'
    operation_types = ['read', 'write']
    results = []
    for operation_type in operation_types:
        tmp_dir = root_dir + f'{operation_type}-only/standalone_tests/model_k_1'
        output_file = f'standalone_excn_summary_{operation_type}.csv'
        results.append(process_directory(tmp_dir))
        write_csv(results[-1], os.path.join(tmp_dir, output_file))

    trained_wlds_img = 'standalone_test_results.jpeg'
    visualize_and_save_results_single(results, os.path.join(root_dir, trained_wlds_img))

if __name__ == "__main__":
    main()
