#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9]+$ ]]; then
    echo "Usage: $0 <n>"
    exit 1
fi

n=$1

run_folder=$(<tmp/Run_folder_name.txt)
log_dir="Runs/$run_folder/logs/timeslice_forwarding/input_nodes"

# Get logfiles in sorted order
mapfile -t logfiles < <(find "$log_dir" -maxdepth 1 -type f | sort)

if (( n < 1 || n > ${#logfiles[@]} )); then
    echo "Error: logfile $n does not exist."
    echo "Found ${#logfiles[@]} logfiles."
    exit 1
fi

logfile="${logfiles[$((n - 1))]}"

echo "Tailing: $logfile"
echo "----------------------------------------"

tail -n +1 -f "$logfile"
