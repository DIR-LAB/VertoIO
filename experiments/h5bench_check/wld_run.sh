#!/bin/bash

# Ask the user for the operation type (read or write)
read -p "Enter the operation type (read/write): " operation_type

shopt -s nullglob
for workload in *.json; do
    echo "$workload"
    filename=$(basename "$workload" .json)
    echo "$filename"

    for itr in {1..1}; do
        # Determine which script to call based on the operation type
        if [ "$operation_type" == "read" ]; then
            lctl set_param 'llite.*.max_cached_mb=1g'
        elif [ "$operation_type" == "write" ]; then
            lctl set_param 'llite.*.max_cached_mb=90g'
        else
            echo "Invalid operation type. Please enter 'read' or 'write'."
            exit 1
        fi
        bash aut_rpc_tun.sh "$filename" "$itr" "$operation_type"
    done
done
# unset it now
shopt -u nullglob
