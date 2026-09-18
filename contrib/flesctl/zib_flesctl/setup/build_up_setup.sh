function ask_cluster() {
    read -p "Are you on the vae* cluster [y/N] " answer
    case "$answer" in
        [yY][eE][sS]|[yY])
            ON_VAE_CLUSTER=true
            ;;
        *)
            ON_VAE_CLUSTER=false
            ;;
    esac
}

function activate_modules() {
    echo "============================================================"
    echo "Activating module files for creating the python venv (only "
    echo "needed on the vae Clusters)"
    echo "============================================================"

    module use modules/python/

    module load 3.11.9

}

function purge_modules() {
    echo "============================================================"
    echo "Purging module files"
    echo "============================================================"
    module purge
    module unuse modules/python/
}

function build_python() {
    PYTHON_VERSION="3.11.9"
    PYTHON_PREFIX="$HOME/opt/python-${PYTHON_VERSION}"
    PYTHON_BIN="${PYTHON_PREFIX}/bin/python3"
 
    if [ -x "${PYTHON_BIN}" ]; then
        echo "============================================================"
        echo "Python ${PYTHON_VERSION} already built at ${PYTHON_PREFIX}, skipping"
        echo "============================================================"
        return
    fi
 
    echo "============================================================"
    echo "Building Python ${PYTHON_VERSION} from source into"
    echo "${PYTHON_PREFIX}"
    echo "(module-provided python on this cluster can't create venvs)"
    echo "============================================================"
 
    BUILD_DIR=$(mktemp -d)
    pushd "$BUILD_DIR" > /dev/null
 
    curl -fsSL -O "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"
    tar -xzf "Python-${PYTHON_VERSION}.tgz"
    cd "Python-${PYTHON_VERSION}"
 
    ./configure --prefix="${PYTHON_PREFIX}" --enable-optimizations
    make -j 4
    make install
 
    popd > /dev/null
    rm -rf "$BUILD_DIR"
 
    echo "============================================================"
    echo "Python ${PYTHON_VERSION} built successfully"
    echo "============================================================"
}


function create_venv() {
    echo "============================================================"
    echo "Building flesctrl python venv"
    echo "============================================================"

    python3 -m venv flesctrl_venv

    source flesctrl_venv/bin/activate

    pip install docopt

    pip install plotext

    pip install matplotlib

    pip install seaborn

    pip install deepdiff

    pip install influxdb_client

    pip install textual
    
    deactivate
}

function create_config() {
    echo "============================================================"
    echo "creating config"
    echo "============================================================"

    cp setup/config_example.cfg setup/config.cfg
}

function create_apptainer() {

    echo "============================================================"
    echo "building flesctrl container"
    echo "============================================================"

    apptainer build --fakeroot container_flesctrl.sif container_flesctrl.def
}

function create_folders() {

    echo "============================================================"
    echo "create execution folders"
    echo "============================================================"

    mkdir tmp

    mkdir tmp/communication

    mkdir tmp/interface

    mkdir tmp/params

    touch tmp/run_id.txt

    echo '0' > tmp/run_id.txt

    mkdir Runs

    mkdir n_to_n_test

    chmod -R 777 n_to_n_test
}


ask_cluster


cd ..
if [ "$ON_VAE_CLUSTER" = true ]; then
    build_python
    activate_modules
fi
create_venv
if [ "$ON_VAE_CLUSTER" = true ]; then
    purge_modules
fi
create_config
create_folders
if [ "$ON_VAE_CLUSTER" = true ]; then
    create_apptainer
fi
cd setup
