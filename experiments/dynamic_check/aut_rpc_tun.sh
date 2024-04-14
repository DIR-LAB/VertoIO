#!/bin/bash

# Other script parameters
k_val=$1
operation_type=$2
excn_durn=360
py_excn_durn=1450

# Require creating rpc_tuning_tests directory beforehand.
mkdir rpc_tuning_tests/model_k_"$k_val"
mkdir rpc_tuning_tests/model_k_"$k_val"/all_wld_csvs_with_system_stats_and_features

# File containing the sequence of workloads
sequence_file="${operation_type}_sequence_${k_val}.txt"
cp "$sequence_file" rpc_tuning_tests/model_k_"$k_val"

# Read the workload names from the file
while read -r workload; do
    workload_sequence+=("$workload")
done < "$sequence_file"

# Will take care of the directory creation
for itr in {1..5}; do
    for workload in "${workload_sequence[@]}"; do
        wld="${workload}_itern_${itr}"
        wd_dir="dir_${wld}"
        mkdir -p rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"
    done
done

# Function to process each workload
process_workload() {
    local workload=$1
    local itr=$2
    local excn_type=$3

    echo "Workload File: ${workload}.f"
    local wld="${workload}_itern_${itr}"
    local wd_dir="dir_${wld}"

    if [[ "$workload" == *"read"* ]] || [[ "$workload" == *"_r_"* ]]; then
        lctl set_param 'llite.*.max_cached_mb=1g'
    elif [[ "$workload" == *"write"* ]] || [[ "$workload" == *"_w_"* ]]; then
        lctl set_param 'llite.*.max_cached_mb=90g'
    fi

    echo "${excn_type} execution started for ${wld}.f"
    { timeout "${excn_durn}"s ./filebench -f "${workload}.f" |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_${excn_type}_output.txt"; } &
    local WLD_PID=$!
    wait $WLD_PID
    echo "${excn_type} execution started for ${wld}.f"
}

echo "<<<<<<< RPC Tuning Data Collection Started for Sequential Execution >>>>>>>>"
for itr in {1..5}; do
    # Initial default values are set, will be overwritten later by tuning scripts
    lctl set_param osc.*.max_pages_per_rpc=1024 osc.*.max_rpcs_in_flight=8 osc.*.max_dirty_mb=2000 |& tee -a rpc_tuning_tests/model_k_"$k_val"/"all_wld_itern_${itr}_rpc_tuning_module_output.txt"
    lfs df -h |& tee -a rpc_tuning_tests/model_k_"$k_val"/"all_wld_itern_${itr}_rpc_tuning_module_output.txt"
    lctl get_param osc.*.max_pages_per_rpc osc.*.max_rpcs_in_flight osc.*.max_dirty_mb |& tee -a rpc_tuning_tests/model_k_"$k_val"/"all_wld_itern_${itr}_rpc_tuning_module_output.txt"

    # The value 1 for Greedy Strategy
    mkdir -p rpc_tuning_tests/model_k_"$k_val"/all_wld_excn_dir
    { timeout "${py_excn_durn}"s python3 -u "tuning_rpc_param.py" rpc_tuning_tests/model_k_"$k_val"/all_wld_excn_dir all_wld_filebench 1 1 |& tee -a rpc_tuning_tests/model_k_"$k_val"/all_wld_excn_dir/"all_wld_itern_${itr}_rpc_tuning_module_output.txt"; } &
    RPC_PID=$!

    # Loop through the workload sequence for each module
    echo "<<<<<<< [itr:"$itr"] RPC Tuning Workload Data Collection Started >>>>>>>>"
    for workload in "${workload_sequence[@]}"; do
        excn_type=tuning
        process_workload "$workload" "$itr" "$excn_type"
    done
    wait $RPC_PID
    echo "<<<<<<< [itr:"$itr"] RPC Tuning Workload Data Collection Finished >>>>>>>>"
done
echo "<<<<<<< RPC Tuning Data Collection Finished for Sequential Execution >>>>>>>>"

echo "<<<<<<< Default Data Collection Started for Sequential Execution >>>>>>>>"
for itr in {1..5}; do
    # Initial default values are set, will be overwritten later by tuning scripts
    lctl set_param osc.*.max_pages_per_rpc=1024 osc.*.max_rpcs_in_flight=8 osc.*.max_dirty_mb=2000 |& tee -a rpc_tuning_tests/model_k_"$k_val"/"all_wld_itern_${itr}_default_module_output.txt"
    lfs df -h |& tee -a rpc_tuning_tests/model_k_"$k_val"/"all_wld_itern_${itr}_default_module_output.txt"
    lctl get_param osc.*.max_pages_per_rpc osc.*.max_rpcs_in_flight osc.*.max_dirty_mb |& tee -a rpc_tuning_tests/model_k_"$k_val"/"all_wld_itern_${itr}_default_module_output.txt"

    # Loop through the workload sequence for each module
    echo "<<<<<<< [itr:"$itr"] Default Workload Data Collection Started >>>>>>>>"
    excn_type=default
    for workload in "${workload_sequence[@]}"; do
        wld="${workload}_itern_${itr}"
        wd_dir="dir_${wld}"

        bash clear_stats.sh rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_${excn_type}_stats_output.txt"
        process_workload "$workload" "$itr" "$excn_type"
        bash collect_data.sh rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_${excn_type}_stats_output.txt"
    done
    echo "<<<<<<< [itr:"$itr"] Default Workload Data Collection Finished >>>>>>>>"
done
echo "<<<<<<< Default Data Collection Finished for Sequential Execution >>>>>>>>"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
csv_file="${script_dir}/wld_optml_config.csv"  # CSV file in the current working directory

# Function to process each workload
prepare_workload_optimal() {
    local workload=$1
    local itr=$2
    local excn_type=$3

    # Extracting optimal configuration values from CSV file based on workload
    while IFS=, read -r wld optml_mppr optml_mrif; do
        if [[ "$wld" == "$workload" ]]; then
            max_pages_per_rpc=$(echo "$optml_mppr" | tr -d '[:space:]')
            max_rpcs_in_flight=$(echo "$optml_mrif" | tr -d '[:space:]')
            break
        fi
    done < "$csv_file"

    lctl set_param osc.*.max_pages_per_rpc="$max_pages_per_rpc" osc.*.max_rpcs_in_flight="$max_rpcs_in_flight" |& tee -a rpc_tuning_tests/model_k_"$k_val"/"all_wld_itern_${itr}_${excn_type}_module_output.txt"
    lfs df -h |& tee -a rpc_tuning_tests/model_k_"$k_val"/"all_wld_itern_${itr}_${excn_type}_module_output.txt"
    lctl get_param osc.*.max_pages_per_rpc osc.*.max_rpcs_in_flight osc.*.max_dirty_mb |& tee -a rpc_tuning_tests/model_k_"$k_val"/"all_wld_itern_${itr}_${excn_type}_module_output.txt"
}

echo "<<<<<<< Optimal Data Collection Started for Sequential Execution >>>>>>>>"
# Optimal Data Collection - repeat for each workload in the sequence
for itr in {1..5}; do
    echo "<<<<<<< [itr:"$itr"] Optimal for ALL Workload Sequence Execution Data Collection Started >>>>>>>>"
    for ((i = 0; i < ${#workload_sequence[@]}; i++)); do
        current_workload="${workload_sequence[i]}"
        excn_type="${current_workload}_optimal"
        prepare_workload_optimal "$current_workload" "$itr" "$excn_type"

        echo "<<<<<<< Optimal for "${current_workload}" Workload Sequence Execution Data Collection Started >>>>>>>>"
        for workload in "${workload_sequence[@]}"; do
            wld="${workload}_itern_${itr}"
            wd_dir="dir_${wld}"

            bash clear_stats.sh rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_${excn_type}_stats_output.txt"
            process_workload "$workload" "$itr" "$excn_type"
            bash collect_data.sh rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_${excn_type}_stats_output.txt"
        done
        echo "<<<<<<< Optimal for "${current_workload}" Workload Sequence Execution Data Collection Finished >>>>>>>>"
    done
    echo "<<<<<<< [itr:"$itr"] Optimal for ALL Workload Sequence Execution Data Collection Finished >>>>>>>>"
done
echo "<<<<<<< Optimal Data Collection Finished for Sequential Execution >>>>>>>>"