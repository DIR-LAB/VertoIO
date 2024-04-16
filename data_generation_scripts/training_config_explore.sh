#!/bin/bash

workload=$1
itrn=1
for mppr in 4 32 256
do
    for mrif in 8 64
    do
        eval "lctl set_param osc.*.max_pages_per_rpc=$mppr"
        eval "lctl set_param osc.*.max_rpcs_in_flight=$mrif"
        echo "[Training] itrn value: $itrn"
        bash training_wld_run.sh "$workload" "$itrn"
        itrn=$((itrn+1))
    done

done