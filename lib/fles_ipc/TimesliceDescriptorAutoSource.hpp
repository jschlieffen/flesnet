// Copyright 2021 Jan de Cuveland <cmail@cuveland.de>
/// \file
/// \brief Defines the fles::TimesliceAutoSource class.
#pragma once

#include "AutoSource.hpp"
#include "StorableTimeslice.hpp"
#include "StorableTimesliceDescriptor.hpp"
//#include "TimesliceView.hpp"
#include "TimesliceDescriptorView.hpp"

namespace fles {

using TimesliceDescriptorAutoSource = AutoSource<TDescriptor,
                                                 StorableTimesliceDescriptor,
                                                 TimesliceDescriptorView,
                                                 ArchiveType::TimesliceDescriptorArchive>;

} // namespace fles
