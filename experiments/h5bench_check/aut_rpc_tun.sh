#!/bin/bash

workload=$1
k_val=$2
operation_type=$3
excn_durn=300
wld_excn_src=/mnt/hasanfs/h5_patterns/sync
chown -R mrashid2 $wld_excn_src

echo "Workload File: ${workload}.json"
cat "${workload}.json"

# Creating directories
mkdir -p rpc_tuning_tests/model_k_"$k_val"/all_wld_csvs_with_system_stats_and_features

for itr in {1..5}; do
    wld="${workload}_itern_${itr}"
    wd_dir="dir_${wld}"
    mkdir -p rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"
    cp ${workload}.json rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"


    tund_dir=rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"
    mkdir -p "${tund_dir}"

    echo 3 > /proc/sys/vm/drop_caches |& tee -a "${tund_dir}"/"${wld}_h5bench_rpc_tuning_output.txt"
    lctl set_param ldlm.namespaces.*.lru_size=clear |& tee -a "${tund_dir}"/"${wld}_h5bench_rpc_tuning_output.txt"

    echo "RPC tuning execution started for ${wld}.json"
    # Initial default values are set, will be overwritten later by tuning scripts
    lctl set_param osc.*.max_pages_per_rpc=1024 osc.*.max_rpcs_in_flight=8 osc.*.max_dirty_mb=2000 |& tee -a "${tund_dir}"/"${wld}_h5bench_rpc_tuning_output.txt"
    lfs df -h |& tee -a "${tund_dir}"/"${wld}_h5bench_rpc_tuning_output.txt"
    lctl get_param osc.*.max_pages_per_rpc osc.*.max_rpcs_in_flight osc.*.max_dirty_mb |& tee -a "${tund_dir}"/"${wld}_h5bench_rpc_tuning_output.txt"

    sed -i 's/output.csv/itern-'"${itr}"'-tuned-output.csv/g' ${workload}.json

    # The value 1 for Greedy Strategy
    { timeout "${excn_durn}"s python3 -u "tuning_rpc_param.py" "${tund_dir}" "${wld}_h5bench" 1 "$k_val" |& tee -a "${tund_dir}"/"${wld}_rpc_tuning_module_output.txt"; } &
    RPC_PID=$!
    { timeout "${excn_durn}"s h5bench -d -f "${operation_type}" "${workload}.json" |& tee -a "${tund_dir}"/"${wld}_h5bench_rpc_tuning_output.txt"; } &

    echo "<<<<<<< RPC Tuning Data Collection Started for ${wld}.json >>>>>>>>"
    wait $RPC_PID
    echo "<<<<<<< RPC Tuning Data Collection Finished for ${wld}.json >>>>>>>>"

    sed -i 's/itern-'"${itr}"'-tuned-output.csv/output.csv/g' ${workload}.json

    shopt -s globstar # Enable globstar to allow ** to search directories recursively

    for file in "${wld_excn_src}/${workload}"/**/*itern-${itr}-tuned-output.csv; do
        if [[ -f "$file" ]]; then
            yes | cp -f "$file" "${tund_dir}/"
        fi
    done

    shopt -u globstar # Disable globstar if it was not previously enabled


    dflt_dir=rpc_tuning_tests/model_k_"$k_val"/"$wd_dir"
    mkdir -p "${dflt_dir}"

    echo 3 > /proc/sys/vm/drop_caches |& tee -a "${dflt_dir}"/"${wld}_h5bench_default_output.txt"
    lctl set_param ldlm.namespaces.*.lru_size=clear |& tee -a "${dflt_dir}"/"${wld}_h5bench_default_output.txt"

    echo "Default execution started for ${wld}.json"
    # Re-setting default values
    bash clear_stats.sh "${dflt_dir}"/"${wld}_default_stats_output.txt"
    lctl set_param osc.*.max_pages_per_rpc=1024 osc.*.max_rpcs_in_flight=8 osc.*.max_dirty_mb=2000 |& tee -a "${dflt_dir}"/"${wld}_h5bench_default_output.txt"
    lfs df -h |& tee -a "${dflt_dir}"/"${wld}_h5bench_default_output.txt"
    lctl get_param osc.*.max_pages_per_rpc osc.*.max_rpcs_in_flight osc.*.max_dirty_mb |& tee -a "${dflt_dir}"/"${wld}_h5bench_default_output.txt"

    sed -i 's/output.csv/itern-'"${itr}"'-dflt-output.csv/g' ${workload}.json

    { timeout "${excn_durn}"s h5bench -d -f "${operation_type}" "${workload}.json" |& tee -a "${dflt_dir}"/"${wld}_h5bench_default_output.txt"; } &
    DFLT_PID=$!

    echo "<<<<<<< Default Data Collection Started for ${wld}.json >>>>>>>>"
    wait $DFLT_PID
    echo "<<<<<<< Default Data Collection Finished for ${wld}.json >>>>>>>>"

    sed -i 's/itern-'"${itr}"'-dflt-output.csv/output.csv/g' ${workload}.json
    bash collect_data.sh "${dflt_dir}"/"${wld}_default_stats_output.txt"

    shopt -s globstar # Enable globstar to allow ** to search directories recursively

    for file in "${wld_excn_src}/${workload}"/**/*itern-${itr}-dflt-output.csv; do
        if [[ -f "$file" ]]; then
            yes | cp -f "$file" "${dflt_dir}/"
        fi
    done

    shopt -u globstar # Disable globstar if it was not previously enabled
done
