#!/bin/bash

function test_chain() {

    if [ $# -ne 0 ];then
        return 1;
    fi
    
    echo $SLURMLIST

    local venv_path="../../../build/flesctl_venv/bin/activate"
    local alloc_nodes="allocating_nodes.py"

    source $venv_path

    #ip a

    python3 $alloc_nodes 0

    deactivate 
}

test_chain
