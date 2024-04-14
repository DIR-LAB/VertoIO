#!/bin/bash

shopt -s nullglob
for workload in *.yaml; do
    echo "$workload"
    filename=$(basename "$workload" .yaml)
    echo "$filename"

    for itr in {1..1}; do
        bash aut_rpc_tun.sh "$filename" "$itr"
    done
done
# unset it now
shopt -u nullglob
