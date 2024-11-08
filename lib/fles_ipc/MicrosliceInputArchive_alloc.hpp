// Copyright 2015, 2020 Jan de Cuveland <cmail@cuveland.de>
/// \file
/// \brief Defines the fles::MicrosliceInputArchive class type.
#pragma once

#include "ArchiveDescriptor.hpp"
#include "InputArchive_alloc.hpp"
#include "InputArchiveLoop.hpp"
#include "InputArchiveSequence.hpp"

namespace fles {

class Microslice;
class StorableMicroslice;
class StorableMicrosliceDescriptor;

/**
 * \brief The MicrosliceInputArchive class deserializes microslice data sets
 * from an input file.
 */
using MicrosliceInputArchive_alloc = InputArchive_alloc<MicrosliceDescriptor,
                                            StorableMicrosliceDescriptor,
                                            ArchiveType::MicrosliceArchive>;

using MicrosliceInputArchiveLoop =
    InputArchiveLoop<Microslice,
                     StorableMicroslice,
                     ArchiveType::MicrosliceArchive>;

using MicrosliceInputArchiveSequence =
    InputArchiveSequence<Microslice,
                         StorableMicroslice,
                         ArchiveType::MicrosliceArchive>;

} // namespace fles
