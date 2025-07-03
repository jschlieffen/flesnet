// Copyright 2015 Jan de Cuveland <cmail@cuveland.de>
/// \file
/// \brief Defines the fles::TimesliceOutputArchive class type.
#pragma once

#include "OutputArchive.hpp"
#include "OutputArchiveSequence.hpp"
//#include "StorableTimeslice.hpp"
#include "StorableTimesliceDescriptor.hpp"


namespace fles {

/**
 * \brief The TimesliceOutputArchive class serializes timeslice data sets to
 * an output file.
 */

using TimesliceDescriptorOutputArchive =
    OutputArchive<TDescriptor, StorableTimesliceDescriptor, ArchiveType::TimesliceDescriptorArchive>;

using TimesliceDescriptorOutputArchiveSequence =
    OutputArchiveSequence<TDescriptor,
                          StorableTimesliceDescriptor,
                          ArchiveType::TimesliceDescriptorArchive>;

} // namespace fles
