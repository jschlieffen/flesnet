Memory Test for %n 
===========================
![CMake Status](https://github.com/cbm-fles/flesnet/workflows/CMake/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/cbm-fles/flesnet/badge.svg?branch=master)](https://coveralls.io/github/cbm-fles/flesnet?branch=master)

This Program checks the RAM usage for certain ways to read timslice archives.


Getting started
---------------

One can execute the program by the following command line:

    ./memory_test -I input1.tsa [input2.tsa ...] -O Output.csv -A 1||0

The following parameters are mandatory to set:

* Input data is defined by timeslice archives (*.tsa)
* Output data is defined by .csv files
* -A decsribes the reading method of the input file.
    * A == 1: The program will use TimesliceAutosource
    * A == 0: The program will use the method of the archive validator

one can use the python file plotting.py if the data should be plotted.
