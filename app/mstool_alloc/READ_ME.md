mstool_alloc 
===========================
![CMake Status](https://github.com/cbm-fles/flesnet/workflows/CMake/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/cbm-fles/flesnet/badge.svg?branch=master)](https://coveralls.io/github/cbm-fles/flesnet?branch=master)

This Program writes microslices into the shared memory, but instead of writing the actual content, it writes random data of the size of the content into the shared memory


Getting started
---------------

One can execute the program by the following command line:

    ./mstool_alloc -i input.dmsa -o output-shm -D 1

The following parameters are mandatory to set:

* Input data is defined by descriptor microslice archives (*.dmsa)
* output-shm is the output-shared memory
* -D tells the program that we use an descriptor source

one can use the tool msa2dmsa to convert ms-archives into descriptor-archives

Only for testing purpose!!!

First test results:

* Improved writing speed from 300 MB/s to 12GB/s

