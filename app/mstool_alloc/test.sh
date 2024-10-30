mstool_alloc="../../build/mstool_alloc"
flesnet="../../build/flesnet"
mstool="../../build/mstool"
tsclient="../../build/tsclient"

function test_chain_normal() {

    if [ $# -ne 3 ]; then
        return 1;
    fi

    local msa_files=$1 #the name of the msa file
    local tsa_files=$2 #the name of the tsa file
    local ts_cnt=$3
    
    #rm -rf $tsa_files
    rm -rf /dev/shm/fles_in # Cleanup leftovers from last testrun

    local mstool_pids=()

    local input_shm="shm:/fles_in/0"
    local output_shm="shm:fles_out/0"

    #echo "test"
    $mstool -i $msa_files -O "fles_in" > /dev/null 2>&1 &
    mstool_pids+=($!)

    sleep 1

    local processor_executable="$tsclient -i shm:%s -o file:$tsa_files"

    $flesnet -n $ts_cnt -t zeromq -i 0 -I $input_shm -o 0 -O $output_shm --timeslice-size 100 --processor-instances 1 -e "$processor_executable"

    sleep 15
    for pid in "${mstool_pids[@]}";
    do
        kill -9 $pid > /dev/null 2>&1
    done

    return $?

}

function create_dmsa(){

    if [ $# -ne 1 ]; then
        return 1;
    fi

    local msa_files=$1 #the name of the msa file

    #echo $msa_files

    local dmsa_files="../../build/test.dmsa"   

    $mstool_alloc -i $msa_files -o $dmsa_files -d 1
}

function test_chain_malloc() {

    if [ $# -ne 3 ]; then
        return 1;
    fi

    local msa_files=$1 #the name of the msa file
    local tsa_files=$2 #the name of the tsa file
    local ts_cnt=$3
    
    rm -rf $tsa_files

    local dmsa_files="../../build/test.dmsa"

    #$mstool_alloc -i $msa_files -o $dmsa_files -d 1

    local mstool_pids=()

    local input_shm="shm:/fles_in/0"
    local output_shm="shm:fles_out/0"

    rm -rf /dev/shm/fles_in # Cleanup leftovers from last testrun
    $mstool_alloc -i $dmsa_files -O "fles_in" -D 1 > /dev/null 2>&1 &
    mstool_pids+=($!)

    sleep 1


    local processor_executable="$tsclient -i shm:%s -o file:$tsa_files"

    $flesnet -n $ts_cnt -t zeromq -i 0 -I $input_shm -o 0 -O $output_shm --timeslice-size 100 --processor-instances 1 -e "$processor_executable"

    sleep 15
    for pid in "${mstool_pids[@]}";
    do
        kill -9 $pid > /dev/null 2>&1
    done

    return $?

}

echo "start with normal flesnet"

start_TRD_normal=`date +%s`
test_chain_normal ../../build/msa_files/2391_node8__TRD_32979.msa ../../build/tsa_files/TRD_normal.tsa 343
if [ $? -ne 0 ]; then
    echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
    exit 1
fi
end_TRD_normal=`date +%s`
runtime_TRD_normal=$((end_TRD_normal-start_TRD_normal))


start_MUCH_normal=`date +%s`
test_chain_normal ../../build/msa_files/2488_node_MUCH_8196.msa ../../build/tsa_files/MUCH_normal.tsa 3433
if [ $? -ne 0 ]; then
    echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
    exit 1
fi
end_MUCH_normal=`date +%s`
runtime_MUCH_normal=$((end_MUCH_normal-start_MUCH_normal))

start_RICH_normal=`date +%s`
test_chain_normal ../../build/msa_files/2488_node_RICH_12289.msa ../../build/tsa_files/RICH_normal.tsa 3447
if [ $? -ne 0 ]; then
    echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
    exit 1
fi
end_RICH_normal=`date +%s`
runtime_RICH_normal=$((end_RICH_normal-start_RICH_normal))

start_STS_normal=`date +%s`
test_chain_normal ../../build/msa_files/2488_node_STS_4101.msa ../../build/tsa_files/STS_normal.tsa 3447
if [ $? -ne 0 ]; then
    echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
    exit 1
fi
end_STS_normal=`date +%s`
runtime_STS_normal=$((end_STS_normal-start_STS_normal))

echo "start with malloc"


create_dmsa ../../build/msa_files/2391_node8__TRD_32979.msa 
start_TRD_malloc=`date +%s`
test_chain_malloc ../../build/msa_files/2391_node8__TRD_32979.msa ../../build/tsa_files/TRD_malloc.tsa 343
if [ $? -ne 0 ]; then
    echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
    exit 1
fi
end_TRD_malloc=`date +%s`
runtime_TRD_malloc=$((end_TRD_malloc-start_TRD_malloc))

create_dmsa ../../build/msa_files/2488_node_MUCH_8196.msa
start_MUCH_malloc=`date +%s`
test_chain_malloc ../../build/msa_files/2488_node_MUCH_8196.msa ../../build/tsa_files/MUCH_malloc.tsa 3433
if [ $? -ne 0 ]; then
    echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
    exit 1
fi
end_MUCH_malloc=`date +%s`
runtime_MUCH_malloc=$((end_MUCH_malloc-start_MUCH_malloc))

create_dmsa ../../build/msa_files/2488_node_RICH_12289.msa
start_RICH_malloc=`date +%s`
test_chain_malloc ../../build/msa_files/2488_node_RICH_12289.msa ../../build/tsa_files/RICH_malloc.tsa 3447
if [ $? -ne 0 ]; then
    echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
    exit 1
fi
end_RICH_malloc=`date +%s`
runtime_RICH_malloc=$((end_RICH_malloc-start_RICH_malloc))

create_dmsa ../../build/msa_files/2488_node_STS_4101.msa
start_STS_malloc=`date +%s`
test_chain_malloc ../../build/msa_files/2488_node_STS_4101.msa ../../build/tsa_files/STS_malloc.tsa 3447
if [ $? -ne 0 ]; then
    echo -e "\e[1;37;1;41mTests FAILED\e[0m" >&2
    exit 1
fi
end_STS_malloc=`date +%s`
runtime_STS_malloc=$((end_STS_malloc-start_STS_malloc))


echo "runtime for TRD normal:  $runtime_TRD_normal"
echo "runtime for MUCH normal: $runtime_MUCH_normal"
echo "runtime for RICH normal: $runtime_RICH_normal"
echo "runtime for STS normal:  $runtime_STS_normal"
echo "runtime for TRD malloc:  $runtime_TRD_malloc"
echo "runtime for MUCH malloc: $runtime_MUCH_malloc"
echo "runtime for RICH malloc: $runtime_RICH_malloc"
echo "runtime for STS malloc:  $runtime_STS_malloc"

