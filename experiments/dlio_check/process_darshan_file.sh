#!/bin/bash

chown -R mrashid2 .

# Iterate over each .darshan file in the current directory
for darshan_file in *.darshan; do
    echo "Processing $darshan_file..."

    python -m darshan summary --enable_dxt_heatmap "$darshan_file"

    # # Extract the name without the .darshan extension
    # dir_name="${darshan_file%.darshan}"
    # darshan-dxt-parser --show-incomplete "$darshan_file" > "$dir_name".txt

    # # Create a directory with this name if it doesn't already exist
    # mkdir -p "$dir_name"

    # # Run the darshan summary command on the file
    # dxt-explorer -t -s -p "./$dir_name" "$darshan_file"
done

echo "Processing complete."
