#!/bin/bash

ENTRY_NODES_CNT=$(grep -E '^entry_nodes=' config.cfg | cut -d'=' -f2)
PROCESSING_NODES_CNT=$(grep -E '^build_nodes=' config.cfg | cut -d'=' -f2)
TIME_ALLOC=$(grep -E '^time=' config.cfg | cut -d'=' -f2)
SET_NODE_LIST=$(grep -E '^set_node_list=' config.cfg | cut -d'=' -f2)


if [ "$SET_NODE_LIST" -eq 1 ]; then
    ENTRY_NODES_LIST=$(grep "^entry_nodes_list" config.cfg | cut -d'=' -f2)
    BUILD_NODES_LIST=$(grep "^build_nodes_list" config.cfg | cut -d'=' -f2)

    source flesctrl_venv/bin/activate


    NODES=$((ENTRY_NODES_CNT + PROCESSING_NODES_CNT))
    NTASKS=4
    MEM=16G
    p="big"
    TIME=$TIME_ALLOC
    NODELIST="$ENTRY_NODES_LIST,$BUILD_NODES_LIST"

    salloc --mem $MEM -p $p --nodes=$NODES --nodelist=$NODELIST --constraint=Infiniband --time=$TIME 
else
    source flesctrl_venv/bin/activate

    NODES=$((ENTRY_NODES_CNT + PROCESSING_NODES_CNT))
    #echo $((NODES+1))
    NTASKS=4
    MEM=16G
    p="big"
    TIME=$TIME_ALLOC

    salloc --mem $MEM -p $p --nodes=$NODES --constraint=Infiniband --time=$TIME 
fi
