#!/bin/bash

ENTRY_NODES_CNT=$(grep -E '^entry_nodes=' config.cfg | cut -d'=' -f2)
PROCESSING_NODES_CNT=$(grep -E '^build_nodes=' config.cfg | cut -d'=' -f2)
TIME_ALLOC=$(grep -E '^time=' config.cfg | cut -d'=' -f2)

echo $TIME_ALLOC

source flesctrl_venv/bin/activate

NODES=$((ENTRY_NODES_CNT + PROCESSING_NODES_CNT))
#echo $((NODES+1))
NTASKS=4
MEM=16G
p="big"
TIME=$TIME_ALLOC

salloc --mem $MEM -p $p --nodes=$NODES --constraint=Infiniband --time=$TIME 
