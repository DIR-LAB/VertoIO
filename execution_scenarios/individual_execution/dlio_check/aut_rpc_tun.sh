#!/bin/bash

workload=$1
k_val=$2
excn_durn=600
wld_file="workload/${workload}.yaml"

echo "Workload File: ${wld_file}"
lctl set_param 'llite.*.max_cached_mb=1g'

for itr in {1..5}; do
    wld="${workload}_itern_${itr}"
    wd_dir="dir_${wld}"


    mkdir -p rpc_tuning_tests/"$workload"_tund/"$wd_dir"
    mkdir -p rpc_tuning_tests/"$workload"_tund/model_k_"$k_val"/all_wld_csvs_with_system_stats_and_features
    sed -i 's|rpc_tuning_tests/'"${workload}"'|rpc_tuning_tests/'"${workload}"'_tund/'"$wd_dir"'|g' "${wld_file}"
    tund_dir=rpc_tuning_tests/"${workload}"_tund/model_k_"$k_val"/"$wd_dir"
    mkdir -p "${tund_dir}"

    echo "RPC tuning execution started for ${wld_file}"
    # Initial default values are set, will be overwritten later by tuning scripts
    cat "${wld_file}" |& tee -a "${tund_dir}"/"${wld}_dlio_rpc_tuning_output.txt"
    echo 3 > /proc/sys/vm/drop_caches |& tee -a "${tund_dir}"/"${wld}_dlio_rpc_tuning_output.txt"
    lctl set_param ldlm.namespaces.*.lru_size=clear |& tee -a "${tund_dir}"/"${wld}_dlio_rpc_tuning_output.txt"
    lctl set_param osc.*.max_pages_per_rpc=1024 osc.*.max_rpcs_in_flight=8 osc.*.max_dirty_mb=2000 |& tee -a "${tund_dir}"/"${wld}_dlio_rpc_tuning_output.txt"
    lfs df -h |& tee -a "${tund_dir}"/"${wld}_dlio_rpc_tuning_output.txt"
    lctl get_param osc.*.max_pages_per_rpc osc.*.max_rpcs_in_flight osc.*.max_dirty_mb |& tee -a "${tund_dir}"/"${wld}_dlio_rpc_tuning_output.txt"

    # The value 1 for Greedy Strategy
    { timeout "${excn_durn}"s python3 -u "tuning_rpc_param.py" "${tund_dir}" "${wld}_dlio" 1 "$k_val" |& tee -a "${tund_dir}"/"${wld}_rpc_tuning_module_output.txt"; } &
    RPC_PID=$!
    { timeout "${excn_durn}"s bash exec_scripts/train/"${workload}_train.sh" |& tee -a "${tund_dir}"/"${wld}_dlio_rpc_tuning_output.txt"; } &

    echo "<<<<<<< RPC Tuning Data Collection Started for ${wld_file} >>>>>>>>"
    wait $RPC_PID
    echo "<<<<<<< RPC Tuning Data Collection Finished for ${wld_file} >>>>>>>>"
    sed -i 's|rpc_tuning_tests/'"${workload}"'_tund/'"$wd_dir"'|rpc_tuning_tests/'"${workload}"'|g' "${wld_file}"


    mkdir -p rpc_tuning_tests/"$workload"_dflt/"$wd_dir"
    sed -i 's|rpc_tuning_tests/'"${workload}"'|rpc_tuning_tests/'"${workload}"'_dflt/'"$wd_dir"'|g' "${wld_file}"
    dflt_dir=rpc_tuning_tests/"${workload}"_dflt
    mkdir -p "${dflt_dir}"

    bash clear_stats.sh "${dflt_dir}"/"${wld}_default_stats_output.txt"
    cat "${wld_file}" |& tee -a "${dflt_dir}"/"${wld}_dlio_default_output.txt"
    echo 3 > /proc/sys/vm/drop_caches |& tee -a "${dflt_dir}"/"${wld}_dlio_default_output.txt"
    lctl set_param ldlm.namespaces.*.lru_size=clear |& tee -a "${dflt_dir}"/"${wld}_dlio_default_output.txt"
    lctl set_param osc.*.max_pages_per_rpc=1024 osc.*.max_rpcs_in_flight=8 osc.*.max_dirty_mb=2000 |& tee -a "${dflt_dir}"/"${wld}_dlio_default_output.txt"
    lfs df -h |& tee -a "${dflt_dir}"/"${wld}_dlio_default_output.txt"
    lctl get_param osc.*.max_pages_per_rpc osc.*.max_rpcs_in_flight osc.*.max_dirty_mb |& tee -a "${dflt_dir}"/"${wld}_dlio_default_output.txt"

    { timeout "${excn_durn}"s bash exec_scripts/train/"${workload}_train.sh" |& tee -a "${dflt_dir}"/"${wld}_dlio_default_output.txt"; } &
    DFLT_PID=$!

    echo "<<<<<<< Default Data Collection Started for ${wld_file} >>>>>>>>"
    wait $DFLT_PID
    echo "<<<<<<< Default Data Collection Finished for ${wld_file} >>>>>>>>"
    bash collect_data.sh "${dflt_dir}"/"${wld}_default_stats_output.txt"
    sed -i 's|rpc_tuning_tests/'"${workload}"'_dflt/'"$wd_dir"'|rpc_tuning_tests/'"${workload}"'|g' "${wld_file}"
done
