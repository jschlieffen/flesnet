flesctrl="execution.py"
benchmark_eval="execution.py"

function execute_iteration() {

    python3 $flesctrl

    local Logfile=$(cat tmp/file_name.txt)
    Logfile="../${Logfile}"
    #echo $Logfile
    cd "benchmark_eval"
    python3 $benchmark_eval $Logfile --collectl_used --mode='all'
    cd ..
    create_output_folder $Logfile 1
}

function create_output_folder() {

    if [ $# -ne 2 ]; then
        return 1;
    fi

    local flesctrl_Logfile=$1
    local delete_folder_after_cp=$2

    
    
    filename="${flesctrl_Logfile##*/}"       
    foldername="Runs/${filename%.*}"    
    #echo "$foldername"             

    #foldername="Runs/$(echo ${flesctrl_Logfile} | cut -d "/" -f 2 | cut -d "." -f 1)"

    #echo $foldername

    mkdir $foldername

    data_folder="benchmark_eval/data"
    plot_folder="benchmark_eval/plots"
    collectl_folder="benchmark_eval/collectl"
    logfolder="logs"

    cp -r $data_folder $foldername

    cp -r $plot_folder $foldername

    cp -r $logfolder $foldername
    
    cp -r $collectl_folder $foldername

    #cp -r tmp $foldername

    if [ $delete_folder_after_cp -eq 1 ]; then
        rm -rf $data_folder

        rm -rf $plot_folder

        rm -rf $logfolder
    	
        rm -rf $collectl_folder	

	create_folders
    fi

    # Also copy the flesnet logfiles, as well as the collectl logfiles.
}

function create_folders() {

    mkdir logs

    mkdir logs/general
    
    mkdir logs/collectl

    mkdir logs/collectl/entry_nodes

    mkdir logs/collectl/build_nodes

    mkdir logs/collectl/tsclient

    mkdir logs/collectl/timeslice_forwarding
    
    mkdir logs/collectl/timeslice_forwarding/central_manager

    mkdir logs/collectl/timeslice_forwarding/input_nodes

    mkdir logs/collectl/timeslice_forwarding/output_nodes

    mkdir logs/timeslice_forwarding 

    mkdir logs/timeslice_forwarding/central_manager

    mkdir logs/timeslice_forwarding/input_nodes

    mkdir logs/timeslice_forwarding/output_nodes

    mkdir logs/timeslice_forwarding/tsclient

}



execute_iteration

#create_output_folder ../Run_50_2025-06-06-19-10-20.log 0
