# dtsatool and dtsclient

![CMake Status](https://github.com/cbm-fles/flesnet/workflows/CMake/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/cbm-fles/flesnet/badge.svg?branch=master)](https://coveralls.io/github/cbm-fles/flesnet?branch=master)

The **dtsclient** is a program for testing applications that read timeslices from shared memory, without analyzing their content.

---

## Table of contents

1. [Overview](#overview)
2. [Usage](#usage)
   1. [Step 1: Creating `.dtsa` files with `dtsatool`](#step-1-creating-dtsa-files-with-dtsatool)
   2. [Step 2: Running `dtsclient`](#step-2-running-dtsclient)
3. [Implementation details](#implementation-details)
4. [Files created or changed](#files-created-or-changed)

---

## Overview

The approach works in two steps:

1. **Extract the descriptors.** The timeslice descriptors are written into a separate file (`*.dtsa`). The content is cut out.
2. **Replay with dummy content.** When `tsclient` is started with these `.dtsa` files, the content pointer of each microslice is set to a memory region filled with random numbers. The modified timeslice is then written to shared memory, where it can be used like a standard timeslice.

This has two advantages:

- **Runtime:** a huge improvement in throughput (from about 300 MB/s writing speed to nearly 16 GB/s), since disk limitations and serialization/deserialization are no longer a bottleneck.
- **Fewer operations:** some operations can be removed, such as reading from disk in the initial startup phase, since the amount of data that needs to be stored is significantly reduced.

---

## Usage

### Step 1: Creating `.dtsa` files with `dtsatool`

Before using `dtsclient`, you need `.dtsa` files. These are created with `dtsatool`, which offers two options:

1. Creating `.dtsa` files from pre-existing `.tsa` files
2. Creating `.dtsa` files from scratch

#### Option A: From pre-existing `.tsa` files

```bash
./dtsatool -i input1.tsa [input2.tsa] -o output_folder --create-folder 1
```

#### Option B: From scratch

This option is a bit more involved, since the size, the number of components, etc. can be set freely. The following parameters are available:

| Parameter            | Meaning                                                        |
|----------------------|----------------------------------------------------------------|
| `-d 1`               | Create one `.dtsa` file (required for this mode)               |
| `-o <output_archive>`| Output archive (required for this mode)                        |
| `-C`                 | Number of components                                           |
| `-N`                 | Timeslice size                                                 |
| `-n`                 | Number of timeslices in this file                              |
| `-m`                 | Minimum content size per microslice (see below)                |
| `-M`                 | Maximum content size per microslice (see below)                |

> **Note:** Only one `.dtsa` file can be created per call.

**Microslice content size.** To allow microslices of varying size, the content size is drawn from a Poisson distribution with

$$\lambda = \frac{m + M}{2},$$

i.e. the midpoint between `-m` (minimum content size) and `-M` (maximum content size). The drawn values are then clamped to the interval $[m, M]$.

**Example.** Create one file with 10 000 timeslices, a timeslice size of 100 and 1 MB per microslice:

```bash
./dtsatool -d 1 -O output.dtsa -C 1 -N 100 -n 10000 -m 1000000 -M 1000000
```

### Step 2: Running `dtsclient`

Once the `.dtsa` file exists, it can be used with `dtsclient` (which is `tsclient` with a few modifications). Three parameters have been added:

| Parameter       | Meaning                                                                                       |
|-----------------|-----------------------------------------------------------------------------------------------|
| `-D 1`          | Use `.dtsa` files instead of `.tsa` files. The program reports immediately if this is set incorrectly. |
| `--malloc_size` | Size of the memory region in bytes. Default: 1 GB.                                            |
| `--jump_size`   | Step by which the content pointer advances (technical; can be ignored in most cases).        |

#### `--malloc_size`

It is hard to judge in advance whether the memory region is large enough, since the microslice size varies.

> **Tip:** Whenever you run into a segmentation fault, increase this value.

#### `--jump_size`

This parameter is somewhat technical and can be ignored in most cases.

- **Default behaviour:** The program reads one microslice and places its content pointer at the beginning of the allocated memory region. It then reads the next microslice and places its pointer directly after the content of the first microslice, and so on.
- **Problem:** This may require accessing many different memory locations frequently, which might then not be cached. This can reduce performance.
- **Solution:** With `--jump_size`, the pointer does not advance to the end of the previous content, but only by the given amount (e.g. 10 KB), so the data of consecutive microslices overlaps.

Currently, a runtime improvement of this kind is not needed, but it may become important in the future.

---

## Implementation details

There are currently no known bugs in this code. However, the code is tied to the current code base, so keep the following three remarks in mind whenever something changes:

1. **`TDescriptor` class.** A new class, `TDescriptor`, was implemented to make this code work. It is exactly the same as the timeslice, except that it contains no content. **When the timeslice layout changes, this class needs to be adjusted as well.**

2. **Serialization.** As mentioned above, the descriptors are written to a separate file. To do so, the timeslices are read using the standard procedure and then written to a file, again using the standard procedure. **When the serialization procedure changes, this needs to be taken into account.**

3. **Shared memory (most important).** A timeslice is structured as follows: it has two vectors, one for the timeslice component descriptors and one for the content of each component (the whole microslice, i.e. content *and* microslice descriptor). Creating a timeslice therefore copies the whole content into the data vector. This copy is unnecessary, it reduces runtime performance and increases RAM usage. To remove it, the SHM classes were adjusted so that the content is copied straight from the allocated memory region into shared memory. **Whenever the SHM classes change, this needs to be adjusted as well.**

---

## Files created or changed

### Changed files

| Folder           | Files                                     |
|------------------|-------------------------------------------|
| `tsclient/`      | `Application.cpp`, `Application.hpp`      |
|                  | `Parameters.cpp`, `Parameters.hpp`        |
| `lib/fles_ipc/`  | `Timeslice.hpp`                           |
|                  | `Sink.hpp`                                |

### Files created from scratch

- Everything in the folder `dtsatool/`

### Files created as copies of the corresponding timeslice files

All of these are located in `lib/fles_ipc/`:

| New file(s)                                              | Based on                                                  |
|----------------------------------------------------------|-----------------------------------------------------------|
| `TDescriptor.cpp`, `TDescriptor.hpp`                     | A mixture of `Timeslice.hpp` and `StorableTimeslice.hpp`  |
| `StorableTimesliceDescriptor.cpp`, `StorableTimesliceDescriptor.hpp` | A copy of `StorableTimeslice.hpp`             |
| `TimesliceBuilder.cpp`, `TimesliceBuilder.hpp`           | A copy of `StorableTimeslice` *(see note)*                |
| `TimesliceDescriptorAutosource.hpp`, `TimesliceDescriptorSource.hpp`, `TimesliceDescriptorInputarchive.hpp`, `TimesliceDescriptorOutputArchive.hpp` | Copied from the corresponding timeslice files |
| `TDescriptorShmSink.cpp`, `TDescriptorShmSink.hpp`       | —                                                         |

> **Note:** The name `TimesliceBuilder` is unfortunate, since the new flesnet framework also contains files with this name.

For each file, the corresponding changes are named explicitly.
