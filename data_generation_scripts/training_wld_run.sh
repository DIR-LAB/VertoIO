#!/bin/bash

workload=$1
itrn=$2

echo "[wld_run] itrn value: $itrn"
excn_durn=320
echo "Workload File: $workload.f"
cat "$workload".f

# Require creating latest_training_data_source directory beforehand.
mkdir dataset
mkdir dataset/latest_training_data_source
mkdir dataset/training_logs

for itr in "$itrn"
do
    wd_dir="$workload"_data
    mkdir dataset/latest_training_data_source/"$wd_dir"
    
    wld="$workload"_itern_"$itr"

    wd_log_dir="$wld"_log
    mkdir dataset/training_logs/"$wd_log_dir"

    { timeout "$excn_durn"s python3 -u random_config_stat_collection_script.py dataset/latest_training_data_source/"$wd_dir" "$wld"_filebench 0 &>> dataset/training_logs/"$wd_log_dir"/"$wld"_rpc_tuning_module_output.txt; } &
    RPC_PID=$!
    { timeout "$excn_durn"s ./filebench -f "$workload".f |& tee -a dataset/training_logs/"$wd_log_dir"/"$wld"_filebench_rpc_tuning_output.txt; } &

    echo "<<<<<<< TRAINING Data Collection Started for "$wld".f >>>>>>>>"
    wait $RPC_PID
    echo "<<<<<<< TRAINING Data Collection Finished for "$wld".f >>>>>>>>"
done