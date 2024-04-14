#!/bin/bash

workload=$1
k_val=$2
tun_script="tuning_rpc_param.py"
excn_durn=360
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
csv_file="${script_dir}/wld_optml_config.csv"  # CSV file in the current working directory

echo "Workload File: ${workload}.f"
cat "${workload}.f"

# Extracting optimal configuration values from CSV file based on workload
while IFS=, read -r wld optml_mppr optml_mrif; do
    if [[ "$wld" == "$workload" ]]; then
        max_pages_per_rpc=$(echo "$optml_mppr" | tr -d '[:space:]')
        max_rpcs_in_flight=$(echo "$optml_mrif" | tr -d '[:space:]')
        break
    fi
done < "$csv_file"

# Creating directories
mkdir -p rpc_tuning_tests/model_k_"$k_val"/all_wld_csvs_with_system_stats_and_features

for itr in {1..5}; do
    wld="${workload}_itern_${itr}"
    wd_dir="dir_${wld}"
    mkdir -p rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"

    echo "RPC tuning execution started for ${wld}.f"
    # Initial default values are set, will be overwritten later by tuning scripts
    lctl set_param osc.*.max_pages_per_rpc=1024 osc.*.max_rpcs_in_flight=8 osc.*.max_dirty_mb=2000 |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_rpc_tuning_output.txt"
    lfs df -h |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_rpc_tuning_output.txt"
    lctl get_param osc.*.max_pages_per_rpc osc.*.max_rpcs_in_flight osc.*.max_dirty_mb |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_rpc_tuning_output.txt"

    # The value 1 for Greedy Strategy
    { timeout "${excn_durn}"s python3 -u "$tun_script" rpc_tuning_tests/model_k_"$k_val"/"$wd_dir" "${wld}_filebench" 1 "$k_val" |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_rpc_tuning_module_output.txt"; } &
    RPC_PID=$!
    { timeout "${excn_durn}"s ./filebench -f "${workload}.f" |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_rpc_tuning_output.txt"; } &

    echo "<<<<<<< RPC Tuning Data Collection Started for ${wld}.f >>>>>>>>"
    wait $RPC_PID
    echo "<<<<<<< RPC Tuning Data Collection Finished for ${wld}.f >>>>>>>>"

    echo "Optimal execution started for ${wld}.f"
    # Setting values from CSV
    bash clear_stats.sh rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_optimal_stats_output.txt"
    lctl set_param osc.*.max_pages_per_rpc="$max_pages_per_rpc" osc.*.max_rpcs_in_flight="$max_rpcs_in_flight" |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_optimal_output.txt"
    lfs df -h |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_optimal_output.txt"
    lctl get_param osc.*.max_pages_per_rpc osc.*.max_rpcs_in_flight osc.*.max_dirty_mb |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_optimal_output.txt"

    { timeout "${excn_durn}"s ./filebench -f "${workload}.f" |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_optimal_output.txt"; } &
    OPTML_PID=$!
    echo "<<<<<<< Optimal Data Collection Started for ${wld}.f >>>>>>>>"
    wait $OPTML_PID
    echo "<<<<<<< Optimal Data Collection Finished for ${wld}.f >>>>>>>>"
    bash collect_data.sh rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_optimal_stats_output.txt"

    echo "Default execution started for ${wld}.f"
    # Re-setting default values
    bash clear_stats.sh rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_default_stats_output.txt"
    lctl set_param osc.*.max_pages_per_rpc=1024 osc.*.max_rpcs_in_flight=8 osc.*.max_dirty_mb=2000 |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_default_output.txt"
    lfs df -h |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_default_output.txt"
    lctl get_param osc.*.max_pages_per_rpc osc.*.max_rpcs_in_flight osc.*.max_dirty_mb |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_default_output.txt"

    { timeout "${excn_durn}"s ./filebench -f "${workload}.f" |& tee -a rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_filebench_default_output.txt"; } &
    DFLT_PID=$!
    echo "<<<<<<< Default Data Collection Started for ${wld}.f >>>>>>>>"
    wait $DFLT_PID
    echo "<<<<<<< Default Data Collection Finished for ${wld}.f >>>>>>>>"
    bash collect_data.sh rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"/"${wld}_default_stats_output.txt"
done
