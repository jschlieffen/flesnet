CBM FLES Timeslice Building
===========================
![CMake Status](https://github.com/cbm-fles/flesnet/workflows/CMake/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/cbm-fles/flesnet/badge.svg?branch=master)](https://coveralls.io/github/cbm-fles/flesnet?branch=master)

This Program is used to track the RAM usage of TimesliceAutosource. 

Getting started
---------------

Once the Program is compiled, the following command has to be typed in the terminal:

  *./memory_test  -I  input1.tsa  [ input2.tsa ... ]  -O  output.csv  -A  1 or 0*

* -I:   This parameter describes the input. Every Linux Wildacrd can be used to read in the data. If the .tsa files are read in with TimesliceAutosource, %n is also allowed.
* -O:   This parameter describes the output. The ouput has to be an .csv file. If the file does not exist the program will generate it.
* -A:   This parameter defines whether TimesliceAutosource should be used (A = 1) or the .tsa files should be read in manually (A = 0).  

*Note: There are currently no default settings for the parameters*


First test results
------------------

The first testresults can be find in the folder app/memory_test/test_run/plots. 

These results show that using %n to read in .tsa files via TimesliceAutosource can reduce the RAM usage and 
lower the processing time, if there are more then .tsa file per node (e.g. gold run). But if every node build exactly one .tsa file, there are no improvements regarding the RAM usage and the
processing time.
