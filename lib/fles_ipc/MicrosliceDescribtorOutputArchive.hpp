// Copyright 2015 Jan de Cuveland <cmail@cuveland.de>
/// \file
/// \brief Defines the fles::MicrosliceOutputArchive class type.
#pragma once

#include "OutputArchive.hpp"
#include "OutputArchiveSequence.hpp"
//#include "StorableMicroslice.hpp"
#include "StorableMicrosliceDescriptor.hpp"

namespace fles {

/**
 * \brief The MicrosliceOutputArchive class serializes microslice data sets to
 * an output file.
 */
using MicrosliceDescriptorOutputArchive = OutputArchive<MicrosliceDescriptor,
                                              StorableMicrosliceDescriptor,
                                              ArchiveType::MicrosliceDescriptorArchive>;

using MicrosliceDescriptorOutputArchiveSequence =
    OutputArchiveSequence<MicrosliceDescriptor,
                          StorableMicrosliceDescriptor,
                          ArchiveType::MicrosliceDescriptorArchive>;

} // namespace fles
