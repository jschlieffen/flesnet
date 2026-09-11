#!/bin/bash

CONFIG_FILE="setup/config.cfg"

if [[ "$1" == "--interactive" ]]; then
    CONFIG_FILE="setup/config_interactive.cfg"
elif [[ -n "$1" ]]; then
    echo "Usage: $0 [--interactive]"
    exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: config file '$CONFIG_FILE' not found."
    exit 1
fi


function set_general_params(){
    RECEIVER_NODES_CNT=$(grep -E '^num_receivers=' "$CONFIG_FILE" | cut -d'=' -f2)
    TIME=$(grep -E '^time=' "$CONFIG_FILE" | cut -d'=' -f2)
    SET_NODE_LIST=$(grep -E '^set_node_list=' "$CONFIG_FILE" | cut -d'=' -f2)
    EXCLUDE_NODES=$(grep -E '^exclude_nodes=' "$CONFIG_FILE" | cut -d'=' -f2)
    NUM_CPUS=$(grep -E '^num_cpus=' "$CONFIG_FILE" | cut -d'=' -f2)
    MEM=$(grep -E '^mem=' "$CONFIG_FILE" | cut -d'=' -f2)
    ACTIVATE_TIMESLICEFORWARDING=$(grep "^GSI_Timesliceforwarding" "$CONFIG_FILE" | cut -d'=' -f2)
    ZIB_TIMESLICEFORWARDING=$(grep "^ZIB_Timesliceforwarding" "$CONFIG_FILE" | cut -d'=' -f2)
    USE_FLESNET=$(grep "^use_flesnet" "$CONFIG_FILE" | cut -d'=' -f2)
    TSMANAGER_CNT=$(grep -E '^num_tsmanager=' "$CONFIG_FILE" | cut -d'=' -f2)
    STSERVER_CNT=$(grep -E '^num_stserver=' "$CONFIG_FILE" | cut -d'=' -f2)
    TSBUILDER_CNT=$(grep -E '^num_tsbuilder=' "$CONFIG_FILE" | cut -d'=' -f2)
    CENTRAL_MANAGER_CNT=$(grep -E '^num_central_manager=' "$CONFIG_FILE" | cut -d'=' -f2)
    INPUT_NODES_CNT=$(grep -E '^num_input_nodes=' "$CONFIG_FILE" | cut -d'=' -f2)
    OUTPUT_NODES_CNT=$(grep -E '^num_output_nodes=' "$CONFIG_FILE" | cut -d'=' -f2)
    USE_FLESCLUSTER=$(grep "^use_flescluster" "$CONFIG_FILE" | cut -d'=' -f2)
    IS_FLESCLUSTER=$(grep "^is_flescluster" "$CONFIG_FILE" | cut -d'=' -f2)

    USE_INPUT_NODES=$(( !USE_FLESNET && ( !USE_FLESCLUSTER || IS_FLESCLUSTER ) ))
    USE_OUTPUT_NODES=$(( !USE_FLESCLUSTER || !IS_FLESCLUSTER ))

    NODES=0

    if [ "$USE_FLESNET" -eq 1 ];then
        ((NODES=TSMANAGER_CNT+STSERVER_CNT+TSBUILDER_CNT))
    fi
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
    TSMANAGER_NODE_LIST=$(grep '^tsmanager_list=' "$CONFIG_FILE" | cut -d'=' -f2)
    STSERVER_NODE_LIST=$(grep '^stserver_list=' "$CONFIG_FILE" | cut -d'=' -f2)
    TSBUILDER_NODE_LIST=$(grep '^tsbuilder_list=' "$CONFIG_FILE" | cut -d'=' -f2)
    SENDER_NODES_LIST=$(grep '^sender_nodes_list=' "$CONFIG_FILE" | cut -d'=' -f2)
    PROCESS_NODES_LIST=$(grep "^process_nodes_list" "$CONFIG_FILE" | cut -d'=' -f2)
    CENTRAL_MANAGER_NODE_LIST=$(grep '^central_manager_node_list=' "$CONFIG_FILE" | cut -d'=' -f2)
    INPUT_NODE_LIST=$(grep '^input_node_list=' "$CONFIG_FILE" | cut -d'=' -f2)
    OUTPUT_NODE_LIST=$(grep '^output_node_list=' "$CONFIG_FILE" | cut -d'=' -f2)

    NODELIST=""
    NODELIST_COMMAND=""
    if [ "$USE_FLESNET" -eq 1 ]; then
        NODELIST="$TSMANAGER_NODE_LIST,$STSERVER_NODE_LIST,$TSBUILDER_NODE_LIST,$SENDER_NODES_LIST"
    fi
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


function set_exclude_node_list() {
    EXCLUDE_TSMANAGER=$(grep '^exclude_tsmanager=' "$CONFIG_FILE" | cut -d'=' -f2)
    EXCLUDE_STSERVER=$(grep '^exclude_stserver=' "$CONFIG_FILE" | cut -d'=' -f2)
    EXCLUDE_TSBUILDER=$(grep '^exclude_tsbuilder=' "$CONFIG_FILE" | cut -d'=' -f2)
    EXCLUDE_SENDER_NODES=$(grep '^exclude_sender_nodes=' "$CONFIG_FILE" | cut -d'=' -f2)
    EXCLUDE_PROCESS_NODES=$(grep "^exclude_process_nodes" "$CONFIG_FILE" | cut -d'=' -f2)
    EXCLUDE_CENTRAL_MANAGER=$(grep "^exclude_central_manager" "$CONFIG_FILE" | cut -d'=' -f2)
    EXCLUDE_INPUT_NODES=$(grep "^exclude_input_nodes" "$CONFIG_FILE" | cut -d'=' -f2)
    EXCLUDE_OUTPUT_NODES=$(grep "^exclude_output_nodes" "$CONFIG_FILE" | cut -d'=' -f2)

    EXCLUDE_NODE_LIST=""
    EXCLUDE_COMMAND=""
    if [ "$USE_FLESNET" -eq 1 ]; then
            EXCLUDE_NODE_LIST="$EXCLUDE_TSMANAGER,$EXCLUDE_STSERVER,$EXCLUDE_TSBUILDER,$EXCLUDE_SENDER_NODES"

    if [ "$ACTIVATE_TIMESLICEFORWARDING" -eq 1 ]; then
        EXCLUDE_NODE_LIST="$EXCLUDE_NODE_LIST,$EXCLUDE_PROCESS_NODES"
    elif [ "$ZIB_TIMESLICEFORWARDING" -eq 1 ]; then
        if (( !$USE_INPUT_NODES )); then
            EXCLUDE_INPUT_NODES=""
        fi

        if (( !$USE_OUTPUT_NODES )); then
            EXCLUDE_CENTRAL_MANAGER=""
            EXCLUDE_OUTPUT_NODES=""
        fi

        EXCLUDE_NODE_LIST="$EXCLUDE_NODE_LIST,$EXCLUDE_CENTRAL_MANAGER,$EXCLUDE_INPUT_NODES,$EXCLUDE_OUTPUT_NODES"
    fi

    if [ "$EXCLUDE_NODES" -eq 1 ]; then
        EXCLUDE_COMMAND="--exclude=$EXCLUDE_NODE_LIST"
    fi
}


function set_cluster_commands() {
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

    echo "Using config: $CONFIG_FILE"
    echo "Node list: $NODELIST"

    source flesctrl_venv/bin/activate

    echo "salloc --nodes=$NODES --mem=$MEM --ntasks-per-node=1 --cpus-per-task=$NUM_CPUS $CLUSTER_COMMAND $NODELIST_COMMAND $EXCLUDE_COMMAND --time=$TIME"

    salloc \
        --nodes="$NODES" \
        --mem="$MEM" \
        --ntasks-per-node=1 \
        --cpus-per-task="$NUM_CPUS" \
        $CLUSTER_COMMAND \
        $NODELIST_COMMAND \
        $EXCLUDE_COMMAND \
        --time="$TIME"
}


allocate_nodes