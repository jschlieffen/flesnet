// Copyright 2015, 2020 Jan de Cuveland <cmail@cuveland.de>
/// \file
/// \brief Defines the fles::MicrosliceInputArchive class type.
#pragma once

#include "ArchiveDescriptor.hpp"
#include "InputArchive.hpp"
#include "InputArchiveLoop.hpp"
#include "InputArchiveSequence.hpp"

namespace fles {

//class MicrosliceDescriptor;
class StorableMicrosliceDescriptor;

/**
 * \brief The MicrosliceInputArchive class deserializes microslice data sets
 * from an input file.
 */
using MicrosliceDescriptorInputArchive = InputArchive<MicrosliceDescriptor,
                                            StorableMicrosliceDescriptor,
                                            ArchiveType::MicrosliceDescriptorArchive>;

using MicrosliceDescriptorInputArchiveLoop =
    InputArchiveLoop<MicrosliceDescriptor,
                     StorableMicrosliceDescriptor,
                     ArchiveType::MicrosliceDescriptorArchive>;

using MicrosliceDescriptorInputArchiveSequence =
    InputArchiveSequence<MicrosliceDescriptor,
                         StorableMicrosliceDescriptor,
                         ArchiveType::MicrosliceDescriptorArchive>;

} // namespace fles
