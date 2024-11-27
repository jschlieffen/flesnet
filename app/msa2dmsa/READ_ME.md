msa2dmsa
===========================
![CMake Status](https://github.com/cbm-fles/flesnet/workflows/CMake/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/cbm-fles/flesnet/badge.svg?branch=master)](https://coveralls.io/github/cbm-fles/flesnet?branch=master)

This Program transforms ms-Archives into descriptor-Archives. Also it can generate new descriptor-Archives, without a ms-Archive.


Getting started
---------------

One can transform a ms-Archive into a descriptor-Archive with the following command.

    ./msa2dmsa -i input.dmsa

The following parameters are mandatory to set:

* Input data is defined by descriptor microslice archives (*.dmsa)

The following command is for generating new descriptor-Archives

    ./msa2dmsa -d 1 -O output.dmsa

This will create a dmsa-file with 10000 microslices with microslice size 1MB (overall 10GB in size). To adjust the size and number of microslices, one can execute the following command

    ./msa2dmsa -d 1 -O output.dmsa --num-ms 10000 --contentsize-min 10000 --contentsize-max 10000000
