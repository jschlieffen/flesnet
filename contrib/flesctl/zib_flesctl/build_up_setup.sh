function create_venv() {
    python3 -m venv flesctrl_venv

    source flesctrl_venv/bin/activate

    pip install docopt

    pip install plotext

    pip install matplotlib

    pip install seaborn

    pip install deepdiff

    deactivate
}

function create_config() {

    cp config_example.cfg config.cfg

}

function create_folders() {

    mkdir logs

    mkdir logs/general
    
    mkdir logs/collectl

    mkdir logs/collectl/entry_nodes

    mkdir logs/collectl/build_nodes

    mkdir logs/collectl/tsclient
}

#create_venv
#create_config
create_folders
