#!/bin/bash

function set_general_params(){
    RECEIVER_NODES_CNT=$(grep -E '^receiver_nodes=' setup/config.cfg | cut -d'=' -f2)
    TIME=$(grep -E '^time=' setup/config.cfg | cut -d'=' -f2)
    SET_NODE_LIST=$(grep -E '^set_node_list=' setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_NODES=$(grep -E '^exclude_nodes=' setup/config.cfg | cut -d'=' -f2)
    NUM_CPUS=$(grep -E '^num_cpus=' setup/config.cfg | cut -d'=' -f2)
    MEM=$(grep -E '^mem=' setup/config.cfg | cut -d'=' -f2)
    ACTIVATE_TIMESLICEFORWARDING=$(grep "^GSI_Timesliceforwarding" setup/config.cfg | cut -d'=' -f2)
    ZIB_TIMESLICEFORWARDING=$(grep "^ZIB_Timesliceforwarding" setup/config.cfg | cut -d'=' -f2)
    CENTRAL_MANAGER_CNT=$(grep -E '^central_manager=' setup/config.cfg | cut -d'=' -f2)
    INPUT_NODES_CNT=$(grep -E '^input_nodes=' setup/config.cfg | cut -d'=' -f2)
    OUTPUT_NODES_CNT=$(grep -E '^output_nodes=' setup/config.cfg | cut -d'=' -f2)
    USE_FLESCLUSTER=$(grep "^use_flescluster" setup/config.cfg | cut -d'=' -f2)
    IS_FLESCLUSTER=$(grep "^is_flescluster" setup/config.cfg | cut -d'=' -f2)
    USE_INPUT_NODES=$(( ( !USE_FLESCLUSTER || IS_FLESCLUSTER ) ))
    USE_OUTPUT_NODES=$(( !USE_FLESCLUSTER || !IS_FLESCLUSTER ))
    NODES=0
    if [ "$ACTIVATE_TIMESLICEFORWARDING" -eq 1 ]; then
        ((NODES=2*RECEIVER_NODES_CNT))
    elif [ "$ZIB_TIMESLICEFORWARDING" -eq 1 ]; then
        if (( !$USE_INPUT_NODES )); then
            INPUT_NODES_CNT=0
        fi 
        if (( !$USE_OUTPUT_NODES )); then
            CENTRAL_MANAGER_CNT=0
            OUTPUT_NODES_CNT=0
        fi
        ((NODES=NODES+INPUT_NODES_CNT+OUTPUT_NODES_CNT+CENTRAL_MANAGER_CNT))
    fi
}


function set_node_list() {
    PROCESS_NODES_LIST=$(grep "^process_nodes_list" setup/config.cfg | cut -d'=' -f2)
    CENTRAL_MANAGER_NODE_LIST=$(grep '^central_manager_node_list=' setup/config.cfg | cut -d'=' -f2)
    INPUT_NODE_LIST=$(grep '^input_node_list=' setup/config.cfg | cut -d'=' -f2)
    OUTPUT_NODE_LIST=$(grep '^output_node_list=' setup/config.cfg | cut -d'=' -f2)
    NODELIST=""
    NODELIST_COMMAND=""
    if [ "$ACTIVATE_TIMESLICEFORWARDING" -eq 1 ]; then
        NODELIST="$NODELIST,$PROCESS_NODES_LIST"
    elif [ "$ZIB_TIMESLICEFORWARDING" -eq 1 ]; then
        if (( !$USE_INPUT_NODES )); then 
            INPUT_NODE_LIST=""
        fi
        if (( !$USE_OUTPUT_NODES )); then 
            CENTRAL_MANAGER_NODE_LIST=""
            OUTPUT_NODE_LIST=""
        fi
        NODELIST="$NODELIST,$INPUT_NODE_LIST,$CENTRAL_MANAGER_NODE_LIST,$OUTPUT_NODE_LIST"
    fi
    if [ "$SET_NODE_LIST" -eq 1 ]; then
        NODELIST_COMMAND="--nodelist=$NODELIST "
    fi

}

set_exclude_node_list() {
    EXCLUDE_PROCESS_NODES=$(grep "^exclude_process_nodes" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_CENTRAL_MANAGER=$(grep "^exclude_central_manager" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_INPUT_NODES=$(grep "^exclude_input_nodes" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_OUTPUT_NODES=$(grep "^exclude_output_nodes" setup/config.cfg | cut -d'=' -f2)
    EXCLUDE_NODE_LIST=""
    EXCLUDE_COMMAND=""
    if [ "$ACTIVATE_TIMESLICEFORWARDING" -eq 1 ]; then
        EXCLUDE_NODE_LIST="$EXCLUDE_NODE_LIST,$EXCLUDE_PROCESS_NODES"
    elif [ "$ZIB_TIMESLICEFORWARDING" -eq 1 ]; then
        if (( !$USE_INPUT_NODES )); then
            EXCLUDE_INPUT_NODES=""
        fi
        if (( !$USE_OUTPUT_NODES )); then 
            EXCLUDE_CENTRAL_MANAGER=""
            EXCLUDE_BUILD_NODES="" 
        fi
        EXCLUDE_NODE_LIST="$EXCLUDE_NODE_LIST,$EXCLUDE_CENTRAL_MANAGER,$EXCLUDE_INPUT_NODES,$EXCLUDE_OUTPUT_NODES"
    fi
    if [ "$EXCLUDE_NODES" -eq 1 ]; then
        EXCLUDE_COMMAND="--exclude=$EXCLUDE_NODE_LIST"
    fi 
}

set_cluster_commands() {
    USE_FLESCLUSTER=$(grep "^use_flescluster" setup/config.cfg | cut -d'=' -f2)
    IS_FLESCLUSTER=$(grep "^is_flescluster" setup/config.cfg | cut -d'=' -f2)
    CLUSTER_COMMAND=""
    if [ "$USE_FLESCLUSTER" -eq 1 ]; then 
        if [ "$IS_FLESCLUSTER" -eq 1 ]; then
            CLUSTER_COMMAND=""
        else
            CLUSTER_COMMAND="--singularity-container=container_flesctrl.sif"
        fi
    else
        CLUSTER_COMMAND="-p big --constraint=Infiniband"
    fi
}

function allocate_nodes(){
    set_general_params
    NTASKS=4

    p="big"
    set_node_list
    set_exclude_node_list
    set_cluster_commands
    echo $NODELIST
    source flesctrl_venv/bin/activate
    echo salloc --nodes=$NODES --mem=$MEM --ntasks-per-node=1 --cpus-per-task=$NUM_CPUS $CLUSTER_COMMAND $NODELIST_COMMAND $EXCLUDE_COMMAND --time=$TIME 
    salloc --nodes=$NODES --mem=$MEM --ntasks-per-node=1 --cpus-per-task=$NUM_CPUS $CLUSTER_COMMAND $NODELIST_COMMAND $EXCLUDE_COMMAND --time=$TIME 
}

allocate_nodes
