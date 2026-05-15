flesctrl="./execution_flesctrl.sh"
CONFIG_FILE="setup/config.cfg"


# Read command line argument
num_nodes=$1

# Check if argument exists
if [ -z "$num_nodes" ]; then
    echo "Usage: $0 <number_of_nodes>"
    exit 1
fi

function execute_iteration () {

    set_config_ZIB_tsclient $num_nodes

    $flesctrl &

    flesctrl_pid=$!

    sleep 120

    #kill -INT -"$flesctrl_pid"

    pkill -INT -f "python3 execution.py"

    wait "$flesctrl_pid"

    folder_name_ZIB_tsclient=$(get_run_folder)

    set_config_ZIB_flesnet $num_nodes

    $flesctrl &

    flesctrl_pid=$!

    sleep 120

    #kill -INT -"$flesctrl_pid"
    pkill -INT -f "python3 execution.py"

    wait "$flesctrl_pid"

    folder_name_ZIB_flesnet=$(get_run_folder)

    set_config_GSI_tsclient $num_nodes

    $flesctrl &

    flesctrl_pid=$!

    sleep 120

    #kill -INT -"$flesctrl_pid"

    pkill -INT -f "python3 execution.py"
    wait "$flesctrl_pid"

    folder_name_GSI_tsclient=$(get_run_folder)


    set_config_GSI_flesnet $num_nodes

    $flesctrl &

    flesctrl_pid=$!

    sleep 120

    #kill -INT -"$flesctrl_pid"
    pkill -INT -f "python3 execution.py"

    wait "$flesctrl_pid"

    folder_name_GSI_flesnet=$(get_run_folder)

    move_folders $folder_name_ZIB_tsclient $folder_name_ZIB_flesnet $folder_name_GSI_tsclient $folder_name_GSI_flesnet
}

function set_config_ZIB_tsclient () {

    local NODES="$1"


    #node settings
    sed -i "s/^input_nodes=.*/input_nodes=${NODES}/" "$CONFIG_FILE"
    sed -i "s/^output_nodes=.*/output_nodes=${NODES}/" "$CONFIG_FILE"

    #mode settings
    sed -i "s/^use_flesnet=.*/use_flesnet=0/" "$CONFIG_FILE"
    sed -i "s/^GSI_Timesliceforwarding=.*/GSI_Timesliceforwarding=0/" "$CONFIG_FILE"
    sed -i "s/^ZIB_Timesliceforwarding=.*/ZIB_Timesliceforwarding=1/" "$CONFIG_FILE"
}

function set_config_ZIB_flesnet () {

    local NODES="$1"

    echo "Setting nodes to $NODES"
    sed -i "s/^entry_nodes=.*/entry_nodes=${NODES}/" "$CONFIG_FILE"
    sed -i "s/^build_nodes=.*/build_nodes=${NODES}/" "$CONFIG_FILE"
    sed -i "s/^input_nodes=.*/input_nodes=${NODES}/" "$CONFIG_FILE"
    sed -i "s/^output_nodes=.*/output_nodes=${NODES}/" "$CONFIG_FILE"

    sed -i "s/^use_flesnet=.*/use_flesnet=1/" "$CONFIG_FILE"
    sed -i "s/^GSI_Timesliceforwarding=.*/GSI_Timesliceforwarding=0/" "$CONFIG_FILE"
    sed -i "s/^ZIB_Timesliceforwarding=.*/ZIB_Timesliceforwarding=1/" "$CONFIG_FILE"
}


function set_config_GSI_tsclient () {

    local NODES="$1"

    echo "Setting nodes to $NODES"

    sed -i "s/^receiver_nodes=.*/receiver_nodes=${NODES}/" "$CONFIG_FILE"

    sed -i "s/^use_flesnet=.*/use_flesnet=0/" "$CONFIG_FILE"
    sed -i "s/^GSI_Timesliceforwarding=.*/GSI_Timesliceforwarding=1/" "$CONFIG_FILE"
    sed -i "s/^ZIB_Timesliceforwarding=.*/ZIB_Timesliceforwarding=0/" "$CONFIG_FILE"
}

function set_config_GSI_flesnet () {

    local NODES="$1"


    echo "Setting nodes to $NODES"
    sed -i "s/^entry_nodes=.*/entry_nodes=${NODES}/" "$CONFIG_FILE"
    sed -i "s/^build_nodes=.*/build_nodes=${NODES}/" "$CONFIG_FILE"
    sed -i "s/^receiver_nodes=.*/receiver_nodes=${NODES}/" "$CONFIG_FILE"

    sed -i "s/^use_flesnet=.*/use_flesnet=1/" "$CONFIG_FILE"
    sed -i "s/^GSI_Timesliceforwarding=.*/GSI_Timesliceforwarding=1/" "$CONFIG_FILE"
    sed -i "s/^ZIB_Timesliceforwarding=.*/ZIB_Timesliceforwarding=0/" "$CONFIG_FILE"
}


function get_run_folder () {
    
    local Logfile=$(cat tmp/file_name.txt)
    Logfile="../${Logfile}"

    filename="${Logfile##*/}"       
    foldername="Runs/${filename%.*}" 

    echo "$foldername"
}


function move_folders () {

    local folder_name_ZIB_tsclient="$1"
    local folder_name_ZIB_flesnet="$2"
    local folder_name_GSI_tsclient="$3"
    local folder_name_GSI_flesnet="$4"

    local folder_test="n_to_n_test/node_num_$num_nodes"

    mkdir -p "$folder_test"

    cp -r "$folder_name_ZIB_tsclient" "$folder_test"

    mv "$folder_test/$(basename "$folder_name_ZIB_tsclient")" \
       "$folder_test/ZIB_Timeslice_forwarding_tsclient"

    cp -r "$folder_name_ZIB_flesnet" "$folder_test"

    mv "$folder_test/$(basename "$folder_name_ZIB_flesnet")" \
       "$folder_test/ZIB_Timeslice_forwarding_flesnet"

    cp -r "$folder_name_GSI_tsclient" "$folder_test"

    mv "$folder_test/$(basename "$folder_name_GSI_tsclient")" \
       "$folder_test/GSI_Timeslice_forwarding_tsclient"

    cp -r "$folder_name_GSI_flesnet" "$folder_test"

    mv "$folder_test/$(basename "$folder_name_GSI_flesnet")" \
       "$folder_test/GSI_Timeslice_forwarding_flesnet"
}

execute_iteration