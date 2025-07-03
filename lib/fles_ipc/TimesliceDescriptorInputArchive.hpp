// Copyright 2015, 2020 Jan de Cuveland <cmail@cuveland.de>
/// \file
/// \brief Defines the fles::TimesliceInputArchive class type.
#pragma once

#include "ArchiveDescriptor.hpp"
#include "InputArchive.hpp"
#include "InputArchiveLoop.hpp"
#include "InputArchiveSequence.hpp"

namespace fles {

class TDescriptor;
class StorableTimesliceDescriptor;

/**
 * \brief The TimesliceInputArchive deserializes timeslice data sets from an
 * input file.
 */
using TimesliceDescriptorInputArchive =
    InputArchive<TDescriptor, StorableTimesliceDescriptor, ArchiveType::TimesliceDescriptorArchive>;

using TimesliceDescriptorInputArchiveLoop =
    InputArchiveLoop<TDescriptor,
                     StorableTimesliceDescriptor,
                     ArchiveType::TimesliceDescriptorArchive>;

using TimesliceDescriptorInputArchiveSequence =
    InputArchiveSequence<TDescriptor,
                         StorableTimesliceDescriptor,
                         ArchiveType::TimesliceDescriptorArchive>;

} // namespace fles
