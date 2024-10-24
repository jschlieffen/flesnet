// Copyright 2015 Jan de Cuveland <cmail@cuveland.de>
/// \file
/// \brief Defines the fles::MicrosliceSource class type.
#pragma once

#include "MicrosliceDescriptor.hpp"
#include "Source.hpp"

namespace fles {

/**
 * \brief The MicrosliceSource base class implements the generic
 * microslice-based input interface.
 */
using MicrosliceDescriptorSource = Source<MicrosliceDescriptor>;

} // namespace fles
