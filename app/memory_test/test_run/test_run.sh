

# Warning the relative paths in the python file has to be changed if yout want to execute it, since these two files are in different folders

memory_test="../../../build/memory_test"



function test_chain() {
    # Check correct number of arguments
    if [ $# -ne 4 ]; then
        return 1;
    fi
    
    local input_tsa=$1
    local output_csv=$2
    local csv_data_name=$3
    local AutoVSManuell=$4

    echo "test run $csv_data_name"

    $memory_test -I ${input_tsa} -O ${output_csv} -A $AutoVSManuell
    python3 ../plotting.py $csv_data_name
    return $?
}
        
# test_chain "../../../build/tsa_files_test/*.tsa" "../../../build/csv_data/nickel_local_Auto_star.csv" "nickel_local_Auto_star" 1 
# if [ $? -ne 0 ]; then
#     echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
#     exit 1
# fi

# test_chain "../../../build/tsa_files_test/2391_node8_*_%n.tsa" "../../../build/csv_data/nickel_local_Auto_prcntgn.csv" "nickel_local_Auto_prcntgn" 1 
# if [ $? -ne 0 ]; then
#     echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
#     exit 1
# fi

# test_chain "../../../build/tsa_files_test/*.tsa" "../../../build/csv_data/nickel_local_Manuell.csv" "nickel_local_Manuell" 0 
# if [ $? -ne 0 ]; then
#     echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
#     exit 1
# fi

# test_chain "/scratch/htc/bzcschin/mcbm_data/2022_nickel/*.tsa" "../../../build/csv_data/nickel_server_Auto_star.csv" "nickel_server_Auto_star" 1 
# if [ $? -ne 0 ]; then
#     echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
#     exit 1
# fi

# test_chain "/scratch/htc/bzcschin/mcbm_data/2022_nickel/2391_node8_*_%n.tsa" "../../../build/csv_data/nickel_server_Auto_prcntgn.csv" "nickel_server_Auto_prcntgn" 1 
# if [ $? -ne 0 ]; then
#     echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
#     exit 1
# fi

# test_chain "/scratch/htc/bzcschin/mcbm_data/2022_nickel/*.tsa" "../../../build/csv_data/nickel_server_Manuell.csv" "nickel_server_Manuell" 0 
# if [ $? -ne 0 ]; then
#     echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
#     exit 1
# fi


test_chain "/scratch/htc/bzcschin/mcbm_data/2022_gold_partial/*.tsa" "../../../build/csv_data/gold_server_Auto_star.csv" "gold_server_Auto_star" 1 
if [ $? -ne 0 ]; then
    echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
    exit 1
fi

test_chain "/scratch/htc/bzcschin/mcbm_data/2022_gold_partial/2488_node*_%n.tsa" "../../../build/csv_data/gold_server_Auto_prcntgn.csv" "gold_server_Auto_prcntgn" 1 
if [ $? -ne 0 ]; then
    echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
    exit 1
fi

test_chain "/scratch/htc/bzcschin/mcbm_data/2022_gold_partial/*.tsa" "../../../build/csv_data/gold_server_Manuell.csv" "gold_server_Manuell" 0 
if [ $? -ne 0 ]; then
    echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
    exit 1
fi



echo -e "\e[1;37;1;42mTests successful\e[0m"
exit 0