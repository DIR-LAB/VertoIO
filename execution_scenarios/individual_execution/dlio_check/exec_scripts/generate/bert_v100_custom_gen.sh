#!/bin/bash

echo 3 > /proc/sys/vm/drop_caches
lctl set_param ldlm.namespaces.*.lru_size=clear
lctl set_param 'llite.*.max_cached_mb=90g'
lctl set_param osc.*.max_pages_per_rpc=1024 osc.*.max_rpcs_in_flight=256 osc.*.max_dirty_mb=2000

mpi_cmd="mpirun -np 32"
CUSTOM_CONFIG_FOLDER="/root/localssd/dlio_tests"
custom_workload="bert_v100_custom"

$mpi_cmd dlio_benchmark --config-dir $CUSTOM_CONFIG_FOLDER workload=$custom_workload ++workload.workflow.generate_data=True ++workload.workflow.train=False