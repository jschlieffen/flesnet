flesctrl="execution.py"
benchmark_eval="benchmark_eval/execution.py"

function execute_iteration() {

    python3 $flesctrl

    local Logfile=$(cat tmp/file_name.txt)
    Logfile="../${Logfile}"
    echo $Logfile

    rm -rf tmp

    python3 $benchmark_eval $Logfile --collectl_used --mode='all'
}

execute_iteration
