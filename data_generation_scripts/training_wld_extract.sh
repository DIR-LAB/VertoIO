#!/bin/bash

shopt -s nullglob
for workload in *.f
do
        echo "$workload"
        filename=$(basename "$workload" .f)
        echo "$filename"
        bash training_config_explore.sh "$filename"
done
shopt -u nullglob