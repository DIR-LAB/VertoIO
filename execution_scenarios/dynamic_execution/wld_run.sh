#!/bin/bash

# Ask the user for the operation type (read or write or rw)
read -p "Enter the operation type (read/write/rw): " operation_type
read -p "Start no of the sequence: " start_no
read -p "End no of the sequence: " end_no

# Using a C-style for loop to iterate from start_no to end_no
for (( itr=$start_no; itr<=$end_no; itr++ )); do
    # Determine which script to call based on the operation type
    if [[ "$operation_type" == "read" ]] || [[ "$operation_type" == "write" ]] || [[ "$operation_type" == "rw" ]]; then
        bash aut_rpc_tun.sh "$itr" "$operation_type"
    else
        echo "Invalid operation type. Please enter 'read' or 'write' or 'rw'."
        exit 1
    fi
done
