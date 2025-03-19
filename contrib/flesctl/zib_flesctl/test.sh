#!/bin/bash

# Extract entry_nodes
entry_nodes=$(grep -E '^entry_nodes=' config.cfg | cut -d'=' -f2)

# Extract build_nodes
build_nodes=$(grep -E '^build_nodes=' config.cfg | cut -d'=' -f2)

echo "Entry Nodes: $entry_nodes"
echo "Build Nodes: $build_nodes"
