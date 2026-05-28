flesctrl="./execution_flesctrl.sh"
CONFIG_FILE="setup/config.cfg"


# Read command line argument
num_nodes_sender=$1
num_nodes_receiver=$2

# Check if both arguments exist
if [ -z "$num_nodes_sender" ] || [ -z "$num_nodes_receiver" ]; then
    echo "Usage: $0 <number_of_nodes_sender> <number_of_nodes_receiver>"
    exit 1
fi


function execute_iteration () {

    set_config_ZIB_tsclient $num_nodes_sender $num_nodes_receiver

    start_flesctrl

    folder_name_ZIB_tsclient=$(get_run_folder)

    set_config_ZIB_flesnet $num_nodes_sender $num_nodes_receiver

    start_flesctrl

    folder_name_ZIB_flesnet=$(get_run_folder)

    move_folders $folder_name_ZIB_tsclient $folder_name_ZIB_flesnet 
}

function set_config_ZIB_tsclient () {

    local NODES_SENDER="$1"

    local NODES_RECEIVER="$2"


    #node settings
    sed -i "s/^input_nodes=.*/input_nodes=${NODES_SENDER}/" "$CONFIG_FILE"
    sed -i "s/^output_nodes=.*/output_nodes=${NODES_RECEIVER}/" "$CONFIG_FILE"

    #mode settings
    sed -i "s/^use_flesnet=.*/use_flesnet=0/" "$CONFIG_FILE"
    sed -i "s/^GSI_Timesliceforwarding=.*/GSI_Timesliceforwarding=0/" "$CONFIG_FILE"
    sed -i "s/^ZIB_Timesliceforwarding=.*/ZIB_Timesliceforwarding=1/" "$CONFIG_FILE"
}

function set_config_ZIB_flesnet () {


    local NODES_SENDER="$1"

    local NODES_RECEIVER="$2"


    #echo "Setting nodes to $NODES"
    sed -i "s/^entry_nodes=.*/entry_nodes=${NODES_SENDER}/" "$CONFIG_FILE"
    sed -i "s/^build_nodes=.*/build_nodes=${NODES_SENDER}/" "$CONFIG_FILE"
    sed -i "s/^input_nodes=.*/input_nodes=${NODES_SENDER}/" "$CONFIG_FILE"
    sed -i "s/^output_nodes=.*/output_nodes=${NODES_RECEIVER}/" "$CONFIG_FILE"

    sed -i "s/^use_flesnet=.*/use_flesnet=1/" "$CONFIG_FILE"
    sed -i "s/^GSI_Timesliceforwarding=.*/GSI_Timesliceforwarding=0/" "$CONFIG_FILE"
    sed -i "s/^ZIB_Timesliceforwarding=.*/ZIB_Timesliceforwarding=1/" "$CONFIG_FILE"
}

function start_flesctrl () {

    $flesctrl &

    flesctrl_pid=$!

    sleep 180

    #kill -INT -"$flesctrl_pid"

    pkill -INT -f "python3 execution.py"

    wait "$flesctrl_pid"

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

    local folder_test="/scratch/htc/jschlieffen/m_to_n_test/node_num_$num_nodes_sender_$num_nodes_receiver"

    mkdir -p "$folder_test"


    cp -r "$folder_name_ZIB_tsclient" "$folder_test"

    mv "$folder_test/$(basename "$folder_name_ZIB_tsclient")" \
       "$folder_test/ZIB_Timeslice_forwarding_tsclient"

    cp -r "$folder_name_ZIB_flesnet" "$folder_test"

    mv "$folder_test/$(basename "$folder_name_ZIB_flesnet")" \
       "$folder_test/ZIB_Timeslice_forwarding_flesnet"


    chmod -R 777 "$folder_test"
}

execute_iteration
