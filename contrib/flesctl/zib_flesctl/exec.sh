#!/bin/bash

ENTRY_NODES_CNT=$(grep -E '^entry_nodes=' setup/config.cfg | cut -d'=' -f2)
PROCESSING_NODES_CNT=$(grep -E '^build_nodes=' setup/config.cfg | cut -d'=' -f2)
TIME_ALLOC=$(grep -E '^time=' setup/config.cfg | cut -d'=' -f2)
SET_NODE_LIST=$(grep -E '^set_node_list=' setup/config.cfg | cut -d'=' -f2)
NUM_CPUS=$(grep -E '^num_cpus=' setup/config.cfg | cut -d'=' -f2)

if [ "$SET_NODE_LIST" -eq 1 ]; then
    ENTRY_NODES_LIST=$(grep "^entry_nodes_list" setup/config.cfg | cut -d'=' -f2)
    BUILD_NODES_LIST=$(grep "^build_nodes_list" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_ENTRY_NODES=$(grep "^exclude_entry_nodes" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_BUILD_NODES=$(grep "^exclude_build_nodes" setup/config.cfg | cut -d'=' -f2)

    source flesctrl_venv/bin/activate

    ACTIVATE_TIMESLICEFORWARDING=$(grep "^GSI_Timesliceforwarding" setup/config.cfg | cut -d'=' -f2)
    ZIB_TIMESLICEFORWARDING=$(grep "^ZIB_Timesliceforwarding" setup/config.cfg | cut -d'=' -f2)
    echo $ACTIVATE_TIMESLICEFORWARDING
    echo $ZIB_TIMESLICEFORWARDING
    if  [ "$ACTIVATE_TIMESLICEFORWARDING" -eq 1 ]; then
        NODES=$((ENTRY_NODES_CNT + 2*PROCESSING_NODES_CNT))
	    PROCESS_NODES_LIST=$(grep "^process_nodes_list" setup/config.cfg | cut -d'=' -f2)
        EXCLUDE_PROCESS_NODES=$(grep "^exclude_process_nodes" setup/config.cfg | cut -d'=' -f2)
    	NODELIST="$ENTRY_NODES_LIST,$BUILD_NODES_LIST,$PROCESS_NODES_LIST"
        EXCLUDE_NODE_LIST="$EXCLUDE_ENTRY_NODES,$EXCLUDE_BUILD_NODES,$EXCLUDE_PROCESS_NODES" 
    elif [ "$ZIB_TIMESLICEFORWARDING" -eq 1 ]; then 
        CENTRAL_MANAGER_CNT=$(grep -E '^central_manager=' setup/config.cfg | cut -d'=' -f2)
        INPUT_NODES_CNT=$(grep -E '^input_nodes=' setup/config.cfg | cut -d'=' -f2)
        OUTPUT_NODES_CNT=$(grep -E '^output_nodes=' setup/config.cfg | cut -d'=' -f2)
        CENTRAL_MANAGER_NODE_LIST=$(grep '^central_manager_node_list=' setup/config.cfg | cut -d'=' -f2)
        INPUT_NODE_LIST=$(grep '^input_node_list=' setup/config.cfg | cut -d'=' -f2)
        OUTPUT_NODE_LIST=$(grep '^output_node_list=' setup/config.cfg | cut -d'=' -f2)
        EXCLUDE_CENTRAL_MANAGER=$(grep "^exclude_central_manager" setup/config.cfg | cut -d'=' -f2)
        EXCLUDE_INPUT_NODES=$(grep "^exclude_input_nodes" setup/config.cfg | cut -d'=' -f2)
        EXCLUDE_OUTPUT_NODES=$(grep "^exclude_output_nodes" setup/config.cfg | cut -d'=' -f2)
        USE_FLESNET=$(grep -E '^use_flesnet=' setup/config.cfg | cut -d'=' -f2)
        if [ "$USE_FLESNET" -eq 1 ]; then
            NODES=$((ENTRY_NODES_CNT + PROCESSING_NODES_CNT + CENTRAL_MANAGER_CNT + INPUT_NODES_CNT + OUTPUT_NODES_CNT))
            NODELIST="$ENTRY_NODES_LIST,$BUILD_NODES_LIST,$CENTRAL_MANAGER_NODE_LIST,$INPUT_NODE_LIST,$OUTPUT_NODE_LIST"
            EXCLUDE_NODE_LIST="$EXCLUDE_ENTRY_NODES,$EXCLUDE_BUILD_NODES,$EXCLUDE_INPUT_NODES,$EXCLUDE_CENTRAL_MANAGER,$EXCLUDE_OUTPUT_NODES" 
        else 
            NODES=$((CENTRAL_MANAGER_CNT + INPUT_NODES_CNT + OUTPUT_NODES_CNT))
            NODELIST="$CENTRAL_MANAGER_NODE_LIST,$INPUT_NODE_LIST,$OUTPUT_NODE_LIST"
            EXCLUDE_NODE_LIST="$EXCLUDE_INPUT_NODES,$EXCLUDE_CENTRAL_MANAGER,$EXCLUDE_OUTPUT_NODES" 
        fi
    else
        NODES=$((ENTRY_NODES_CNT + PROCESSING_NODES_CNT))
	    NODELIST="$ENTRY_NODES_LIST,$BUILD_NODES_LIST"
        EXCLUDE_NODE_LIST="$EXCLUDE_ENTRY_NODES,$EXCLUDE_BUILD_NODES" 
    fi
    NTASKS=4
    MEM=16GB
    p="big"
    TIME=$TIME_ALLOC
    EXCLUDE_NODES=$(grep -E '^exclude_nodes=' setup/config.cfg | cut -d'=' -f2)
    echo $EXCLUDE_NODES
    if [ "$EXCLUDE_NODES" -eq 1 ]; then 
        salloc --mem=$MEM --ntasks-per-node=1 -c $NUM_CPUS -p $p --nodes=$NODES --nodelist=$NODELIST --exclude=$EXCLUDE_NODE_LIST --constraint=Infiniband --time=$TIME 
    else 
        salloc --mem=$MEM --ntasks-per-node=1 -c $NUM_CPUS -p $p --nodes=$NODES --nodelist=$NODELIST --constraint=Infiniband --time=$TIME 
    fi
else
    source flesctrl_venv/bin/activate

    ACTIVATE_TIMESLICEFORWARDING=$(grep "^GSI_Timesliceforwarding" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_ENTRY_NODES=$(grep "^exclude_entry_nodes" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_BUILD_NODES=$(grep "^exclude_build_nodes" setup/config.cfg | cut -d'=' -f2)
    ZIB_TIMESLICEFORWARDING=$(grep "^ZIB_Timesliceforwarding" setup/config.cfg | cut -d'=' -f2)
    echo $ACTIVATE_TIMESLICEFORWARDING
    echo $ZIB_TIMESLICEFORWARDING
    if  [ "$ACTIVATE_TIMESLICEFORWARDING" -eq 1 ]; then
        EXCLUDE_PROCESS_NODES=$(grep "^exclude_process_nodes" setup/config.cfg | cut -d'=' -f2)
        NODES=$((ENTRY_NODES_CNT + 2*PROCESSING_NODES_CNT))
        EXCLUDE_NODE_LIST="$EXCLUDE_ENTRY_NODES,$EXCLUDE_BUILD_NODES,$EXCLUDE_PROCESS_NODES" 
    elif [ "$ZIB_TIMESLICEFORWARDING" -eq 1 ]; then 
        CENTRAL_MANAGER_CNT=$(grep -E '^central_manager=' setup/config.cfg | cut -d'=' -f2)
        INPUT_NODES_CNT=$(grep -E '^input_nodes=' setup/config.cfg | cut -d'=' -f2)
        OUTPUT_NODES_CNT=$(grep -E '^output_nodes=' setup/config.cfg | cut -d'=' -f2)
        EXCLUDE_CENTRAL_MANAGER=$(grep "^exclude_central_manager" setup/config.cfg | cut -d'=' -f2)
        EXCLUDE_INPUT_NODES=$(grep "^exclude_input_nodes" setup/config.cfg | cut -d'=' -f2)
        EXCLUDE_OUTPUT_NODES=$(grep "^exclude_output_nodes" setup/config.cfg | cut -d'=' -f2)
        USE_FLESNET=$(grep -E '^use_flesnet=' setup/config.cfg | cut -d'=' -f2)
        if [ "$USE_FLESNET" -eq 1 ]; then
            NODES=$((ENTRY_NODES_CNT + PROCESSING_NODES_CNT + CENTRAL_MANAGER_CNT + INPUT_NODES_CNT + OUTPUT_NODES_CNT))
            EXCLUDE_NODE_LIST="$EXCLUDE_ENTRY_NODES,$EXCLUDE_BUILD_NODES,$EXCLUDE_INPUT_NODES,$EXCLUDE_CENTRAL_MANAGER,$EXCLUDE_OUTPUT_NODES" 
        else 
            NODES=$((CENTRAL_MANAGER_CNT + INPUT_NODES_CNT + OUTPUT_NODES_CNT))
            EXCLUDE_NODE_LIST="$EXCLUDE_INPUT_NODES,$EXCLUDE_CENTRAL_MANAGER,$EXCLUDE_OUTPUT_NODES" 
        fi
    else 
        NODES=$((ENTRY_NODES_CNT + PROCESSING_NODES_CNT))
        EXCLUDE_NODE_LIST="$EXCLUDE_ENTRY_NODES,$EXCLUDE_BUILD_NODES" 
    fi
    #echo $((NODES+1))
    NTASKS=4
    MEM=16GB
    p="big"
    TIME=$TIME_ALLOC
    EXCLUDE_NODES=$(grep -E '^exclude_nodes=' setup/config.cfg | cut -d'=' -f2)
    if [ "$EXCLUDE_NODES" -eq 1 ]; then 
        salloc --nodes=$NODES --mem=$MEM --ntasks-per-node=1 --cpus-per-task=$NUM_CPUS -p $p --exclude=$EXCLUDE_NODE_LIST --constraint=Infiniband --time=$TIME 
    else
        salloc --nodes=$NODES --mem=$MEM --ntasks-per-node=1 --cpus-per-task=$NUM_CPUS -p $p --constraint=Infiniband --time=$TIME 
    fi
fi
