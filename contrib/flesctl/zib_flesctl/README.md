FLESCTRL
===========================
![CMake Status](https://github.com/cbm-fles/flesnet/workflows/CMake/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/cbm-fles/flesnet/badge.svg?branch=master)](https://coveralls.io/github/cbm-fles/flesnet?branch=master)

Flesctrl aims to automize the flesnet routine on the cluster at the ZIB. It also provides some monotoring and logging features, that may be extended in the future.

Requirements
------------

To execute the code one needs at least Python 3.6 and in addition the libaries

* docopt
* plotext

If you use a virtual env. it is recommended to name it flesctrl_venv, since the file ./exec.sh starts it automatically then. 

First usage
-----------


The code itself reads the params from the file **`config.cfg`**. This has to be structered just as the file **`config_example.cfg`**. The usage of each parameter is explained also there.

NOTE: After the first execution of the program flesctrl removes the comments, that explain the usage of the params. Thus it is recommended to create a new config, rather than just renaming **`config_example.cfg`**.

In order to create all necessary folders, setting up the virtual enviroment, downloading all used libaries, one can execute the file 

`./build_up_setup.sh`

This only needs to be done once, unless changes in the code appeared.

NOTE: It is recommended to create the folders like that, due to the fact that some paths cannot easily be found in the code and are not created automatically

Getting started
---------------

To start flesctrl one needs to firstly allocate the nodes required. This can be done by using the command

  `./exec.sh`


Monitoring
----------

This flesctrl has a monitoring tool, where the data rates and progress is printed inside the terminal. To activate this one needs to set the specific parameters in the config file. The monitoring itself is executed in a seperate tmux session. In order to see the output, one needs to open a new terminal and make an ssh jump on the login node. Then execute the following command 

`tmux attach-session -t monitoring`

This will connect your terminal to the tmux session created by flesctrl. If a bug occurs one can kill the session manually via 

`tmux kill-session -t monitoring`



After this is done, one can start with flesctrl by using the command

  `./execution.py`

The program needs to be terminated manually by using ctrl+c
