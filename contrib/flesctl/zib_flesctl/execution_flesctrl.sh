flesctrl="execution.py"
benchmark_eval="execution.py"

function execute_iteration() {

    python3 $flesctrl

    local Logfile=$(cat tmp/file_name.txt)
    Logfile="../${Logfile}"
    move_config $Logfile
    cd "benchmark_eval"
    python3 $benchmark_eval $Logfile --collectl_used --mode='all'
    cd ..
    #create_output_folder $Logfile 1
}

function move_config(){
    if [ $# -ne 1 ]; then
        return 1;
    fi

    local flesctrl_Logfile=$1
    filename="${flesctrl_Logfile##*/}"       
    foldername="Runs/${filename%.*}" 
    
    cp setup/config.cfg $foldername

    #cp -r tmp $foldername
}


execute_iteration

