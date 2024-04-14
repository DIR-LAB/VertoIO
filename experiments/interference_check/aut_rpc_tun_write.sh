#!/bin/bash

source /root/localssd/miniconda3/etc/profile.d/conda.sh
conda activate ml_test_env

lctl set_param 'llite.*.max_cached_mb=90g'

workload=$1
k_val=$2
run_no=$3
tun_script=tuning_rpc_param.py
inf_excn_type=modify
excn_durn=320

echo "Workload File: $workload.f"
cat "$workload".f

# Require creating rpc_tuning_tests directory beforehand.
mkdir -p rpc_tuning_tests/inf_run_"$run_no"/"$inf_excn_type"/all_wld_csvs_with_system_stats_and_features

for itr in {1..5}
do
    wld="${workload}_itern_${itr}"
    wd_dir=rpc_tuning_tests/inf_run_"$run_no"/"$inf_excn_type"/"dir_${wld}"
    mkdir -p "$wd_dir"

    echo "RPC tuning execution started for ${wld}.f"
    # Initial default values are set, will be overwritten later by tuning scripts
    lctl set_param osc.*.max_pages_per_rpc=1024 osc.*.max_rpcs_in_flight=8 osc.*.max_dirty_mb=2000 |& tee -a "$wd_dir"/"${wld}_filebench_rpc_tuning_output.txt"
    lfs df -h |& tee -a "$wd_dir"/"${wld}_filebench_rpc_tuning_output.txt"
    lctl get_param osc.*.max_pages_per_rpc osc.*.max_rpcs_in_flight osc.*.max_dirty_mb |& tee -a "$wd_dir"/"${wld}_filebench_rpc_tuning_output.txt"

    # The value 1 for Greedy Strategy
    { timeout "${excn_durn}"s python3 -u "$tun_script" "$wd_dir" "${wld}_filebench" 1 "$k_val" |& tee -a "$wd_dir"/"${wld}_rpc_tuning_module_output.txt"; } &
    RPC_PID=$!
    { timeout "${excn_durn}"s ./filebench -f "${workload}.f" |& tee -a "$wd_dir"/"${wld}_filebench_rpc_tuning_output.txt"; } &

    echo "<<<<<<< RPC Tuning Data Collection Started for ${wld}.f >>>>>>>>"
    wait $RPC_PID
    echo "<<<<<<< RPC Tuning Data Collection Finished for ${wld}.f >>>>>>>>"

    echo "Default execution started for ${wld}.f"
    # Re-setting default values
    bash clear_stats.sh "$wd_dir"/"${wld}_default_stats_output.txt"
    lctl set_param osc.*.max_pages_per_rpc=1024 osc.*.max_rpcs_in_flight=8 osc.*.max_dirty_mb=2000 |& tee -a "$wd_dir"/"${wld}_filebench_default_output.txt"
    lfs df -h |& tee -a "$wd_dir"/"${wld}_filebench_default_output.txt"
    lctl get_param osc.*.max_pages_per_rpc osc.*.max_rpcs_in_flight osc.*.max_dirty_mb |& tee -a "$wd_dir"/"${wld}_filebench_default_output.txt"

    # The value 0 for Default Strategy *** THIS IS A WORKAROUND: FIXME ***
    { timeout "${excn_durn}"s python3 -u "$tun_script" "$wd_dir" "${wld}_filebench" 0 "$k_val" |& tee -a "$wd_dir"/"${wld}_default_stats_output.txt"; } &
    DFLT_PID=$!
    { timeout "${excn_durn}"s ./filebench -f "${workload}.f" |& tee -a "$wd_dir"/"${wld}_filebench_default_output.txt"; } &

    echo "<<<<<<< Default Data Collection Started for ${wld}.f >>>>>>>>"
    wait $DFLT_PID
    echo "<<<<<<< Default Data Collection Finished for ${wld}.f >>>>>>>>"
    bash collect_data.sh "$wd_dir"/"${wld}_default_stats_output.txt"
done