#!/bin/bash

# Read the value directly
list=$(grep "^entry_nodes_list" config.cfg | cut -d'=' -f2- | sed 's/^ *//;s/ *$//')

# Convert to array
IFS=',' read -ra my_array <<< "$list"

# Print the items
for item in "${my_array[@]}"; do
    echo "$item"
done



my_var=1

if [ "$my_var" -eq 1 ]; then
    echo "The variable is equal to 1"
else
    echo "The variable is NOT equal to 1"
fi
