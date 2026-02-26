#!/bin/bash

function set_general_params(){
    ENTRY_NODES_CNT=$(grep -E '^entry_nodes=' setup/config.cfg | cut -d'=' -f2)
    PROCESSING_NODES_CNT=$(grep -E '^build_nodes=' setup/config.cfg | cut -d'=' -f2)
    TIME=$(grep -E '^time=' setup/config.cfg | cut -d'=' -f2)
    SET_NODE_LIST=$(grep -E '^set_node_list=' setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_NODES=$(grep -E '^exclude_nodes=' setup/config.cfg | cut -d'=' -f2)
    NUM_CPUS=$(grep -E '^num_cpus=' setup/config.cfg | cut -d'=' -f2)
    ACTIVATE_TIMESLICEFORWARDING=$(grep "^GSI_Timesliceforwarding" setup/config.cfg | cut -d'=' -f2)
    ZIB_TIMESLICEFORWARDING=$(grep "^ZIB_Timesliceforwarding" setup/config.cfg | cut -d'=' -f2)
    CENTRAL_MANAGER_CNT=$(grep -E '^central_manager=' setup/config.cfg | cut -d'=' -f2)
    INPUT_NODES_CNT=$(grep -E '^input_nodes=' setup/config.cfg | cut -d'=' -f2)
    OUTPUT_NODES_CNT=$(grep -E '^output_nodes=' setup/config.cfg | cut -d'=' -f2)
    USE_FLESNET=$(grep -E '^use_flesnet=' setup/config.cfg | cut -d'=' -f2)
    NODES=0
    if [ "$USE_FLESNET" -eq 1 ]; then
        ((NODES=NODES+ENTRY_NODES_CNT+PROCESSING_NODES_CNT))
    fi
    if [ "$ACTIVATE_TIMESLICEFORWARDING" -eq 1 ]; then
        ((NODES=NODES+PROCESSING_NODES_CNT))
    elif [ "$ZIB_TIMESLICEFORWARDING" -eq 1 ]; then 
        ((NODES=NODES+INPUT_NODES_CNT+OUTPUT_NODES_CNT+CENTRAL_MANAGER_CNT))
    fi
}


function set_node_list() {
    ENTRY_NODES_LIST=$(grep "^entry_nodes_list" setup/config.cfg | cut -d'=' -f2)
    BUILD_NODES_LIST=$(grep "^build_nodes_list" setup/config.cfg | cut -d'=' -f2)
    PROCESS_NODES_LIST=$(grep "^process_nodes_list" setup/config.cfg | cut -d'=' -f2)
    CENTRAL_MANAGER_NODE_LIST=$(grep '^central_manager_node_list=' setup/config.cfg | cut -d'=' -f2)
    INPUT_NODE_LIST=$(grep '^input_node_list=' setup/config.cfg | cut -d'=' -f2)
    OUTPUT_NODE_LIST=$(grep '^output_node_list=' setup/config.cfg | cut -d'=' -f2)
    NODELIST=""
    if [ "$USE_FLESNET" -eq 1 ]; then
        NODELIST="$ENTRY_NODES_LIST,$OUTPUT_NODE_LIST"
    fi
    if [ "$ACTIVATE_TIMESLICEFORWARDING" -eq 1 ]; then
        NODELIST="$NODELIST,$PROCESS_NODES_LIST"
    elif [ "$ZIB_TIMESLICEFORWARDING" -eq 1 ]; then
        NODELIST="$NODELIST,$INPUT_NODE_LIST,$CENTRAL_MANAGER_NODE_LIST,$OUTPUT_NODE_LIST"
    fi
}

set_exclude_node_list() {
    EXCLUDE_ENTRY_NODES=$(grep "^exclude_entry_nodes" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_BUILD_NODES=$(grep "^exclude_build_nodes" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_PROCESS_NODES=$(grep "^exclude_process_nodes" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_CENTRAL_MANAGER=$(grep "^exclude_central_manager" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_INPUT_NODES=$(grep "^exclude_input_nodes" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_OUTPUT_NODES=$(grep "^exclude_output_nodes" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_NODE_LIST=""
    if [ "$USE_FLESNET" -eq 1 ]; then
        EXCLUDE_NODE_LIST="$EXCLUDE_NODE_LIST,$EXCLUDE_ENTRY_NODES,$EXCLUDE_BUILD_NODES"
    fi
    if [ "$ACTIVATE_TIMESLICEFORWARDING" -eq 1 ]; then
        EXCLUDE_NODE_LIST="$EXCLUDE_NODE_LIST,$EXCLUDE_PROCESS_NODES"
    elif [ "$ZIB_TIMESLICEFORWARDING" -eq 1 ]; then
        EXCLUDE_NODE_LIST="$EXCLUDE_NODE_LIST,$EXCLUDE_CENTRAL_MANAGER,$EXCLUDE_INPUT_NODES,$EXCLUDE_OUTPUT_NODES"
    fi
}

function allocate_nodes(){
    set_general_params
    NTASKS=4
    MEM=16GB
    p="big"
    set_node_list
    set_exclude_node_list
    echo $NODELIST
    source flesctrl_venv/bin/activate
    if [ "$SET_NODE_LIST" -eq 1 ]; then
        if [ "$EXCLUDE_NODES" -eq 1 ]; then 
            echo salloc --mem=$MEM --ntasks-per-node=1 -c $NUM_CPUS -p $p --nodes=$NODES --nodelist=$NODELIST --exclude=$EXCLUDE_NODE_LIST --constraint=Infiniband --time=$TIME
            salloc --mem=$MEM --ntasks-per-node=1 -c $NUM_CPUS -p $p --nodes=$NODES --nodelist=$NODELIST --exclude=$EXCLUDE_NODE_LIST --constraint=Infiniband --time=$TIME 
        else 
            echo salloc --mem=$MEM --ntasks-per-node=1 -c $NUM_CPUS -p $p --nodes=$NODES --nodelist=$NODELIST --constraint=Infiniband --time=$TIME 
            salloc --mem=$MEM --ntasks-per-node=1 -c $NUM_CPUS -p $p --nodes=$NODES --nodelist=$NODELIST --constraint=Infiniband --time=$TIME 
        fi
    else
        if [ "$EXCLUDE_NODES" -eq 1 ]; then 
            echo salloc --nodes=$NODES --mem=$MEM --ntasks-per-node=1 --cpus-per-task=$NUM_CPUS -p $p --exclude=$EXCLUDE_NODE_LIST --constraint=Infiniband --time=$TIME 
            salloc --nodes=$NODES --mem=$MEM --ntasks-per-node=1 --cpus-per-task=$NUM_CPUS -p $p --exclude=$EXCLUDE_NODE_LIST --constraint=Infiniband --time=$TIME 
        else
            echo salloc --nodes=$NODES --mem=$MEM --ntasks-per-node=1 --cpus-per-task=$NUM_CPUS -p $p --constraint=Infiniband --time=$TIME 
            salloc --nodes=$NODES --mem=$MEM --ntasks-per-node=1 --cpus-per-task=$NUM_CPUS -p $p --constraint=Infiniband --time=$TIME 
        fi 
    fi
}

allocate_nodes