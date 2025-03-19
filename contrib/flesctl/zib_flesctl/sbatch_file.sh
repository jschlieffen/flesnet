#!/bin/bash

ENTRY_NODES_CNT=$(grep -E '^entry_nodes=' config.cfg | cut -d'=' -f2)
PROCESSING_NODES_CNT=$(grep -E '^build_nodes=' config.cfg | cut -d'=' -f2)


NODES=$((ENTRY_NODES_CNT + PROCESSING_NODES_CNT))
NTASKS=$((ENTRY_NODES_CNT + PROCESSING_NODES_CNT))
MEM=16
p="big"
A="csr"
TIME="00:10:00"

sbatch --mem $MEM -A $A -p $p --exclusive --nodes $NODES --nodes $NODES --ntasks $NTASKS --time $TIME ./central_manager.py 0