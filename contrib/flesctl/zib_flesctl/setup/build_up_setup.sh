function create_venv() {
    python3 -m venv flesctrl_venv

    source flesctrl_venv/bin/activate

    pip install docopt

    pip install plotext

    pip install matplotlib

    pip install seaborn

    pip install deepdiff

    pip install influxdb_client

    deactivate
}

function create_config() {
    cp setup/config_example.cfg setup/config.cfg
}

function create_folders() {

    mkdir logs

    mkdir logs/general
    
    mkdir logs/collectl

    mkdir logs/collectl/entry_nodes

    mkdir logs/collectl/build_nodes

    mkdir logs/collectl/tsclient

    mkdir tmp

    touch tmp/run_id.txt

    echo '0' > tmp/run_id.txt

    mkdir Runs

    mkdir n_to_n_test

    chmod -R 777 n_to_n_test
}

cd ..
create_venv
create_config
create_folders
cd setup
