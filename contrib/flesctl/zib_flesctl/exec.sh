#!/bin/bash

ENTRY_NODES_CNT=$(grep -E '^entry_nodes=' config.cfg | cut -d'=' -f2)
PROCESSING_NODES_CNT=$(grep -E '^build_nodes=' config.cfg | cut -d'=' -f2)
TIME_ALLOC=$(grep -E '^time=' config.cfg | cut -d'=' -f2)
SET_NODE_LIST=$(grep -E '^set_node_list=' config.cfg | cut -d'=' -f2)


if [ "$SET_NODE_LIST" -eq 1 ]; then
    ENTRY_NODES_LIST=$(grep "^entry_nodes_list" config.cfg | cut -d'=' -f2)
    BUILD_NODES_LIST=$(grep "^build_nodes_list" config.cfg | cut -d'=' -f2)

    source flesctrl_venv/bin/activate

    ACTIVATE_TIMESLICEFORWARDING=$(grep "^activate_timesliceforwarding" config.cfg | cut -d'=' -f2)
    if  [ "$ACTIVATE_TIMESLICEFORWARDING" -eq 1 ]; then
        NODES=$((ENTRY_NODES_CNT + 2*PROCESSING_NODES_CNT))
    else
        NODES=$((ENTRY_NODES_CNT + PROCESSING_NODES_CNT))
    fi
    NTASKS=4
    MEM=16G
    p="big"
    TIME=$TIME_ALLOC
    NODELIST="$ENTRY_NODES_LIST,$BUILD_NODES_LIST"

    salloc --mem=$MEM --ntasks-per-node=6 -c 6 -p $p --nodes=$NODES --nodelist=$NODELIST --constraint=Infiniband --time=$TIME 
else
    source flesctrl_venv/bin/activate

    ACTIVATE_TIMESLICEFORWARDING=$(grep "^activate_timesliceforwarding" config.cfg | cut -d'=' -f2)

    echo $ACTIVATE_TIMESLICEFORWARDING
    if  [ "$ACTIVATE_TIMESLICEFORWARDING" -eq 1 ]; then
        NODES=$((ENTRY_NODES_CNT + 2*PROCESSING_NODES_CNT))
    else
        NODES=$((ENTRY_NODES_CNT + PROCESSING_NODES_CNT))
    fi
    #echo $((NODES+1))
    NTASKS=4
    MEM=16G
    p="big"
    TIME=$TIME_ALLOC

    salloc --nodes=$NODES --mem=$MEM --ntasks-per-node=1 -c 6 -p $p -x htc-cmp127 --constraint=Infiniband --time=$TIME 

fi
