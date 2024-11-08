// Copyright 2015 Jan de Cuveland <cmail@cuveland.de>

#include "StorableMicrosliceDescriptor.hpp"

namespace fles {

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wextra"
StorableMicrosliceDescriptor::StorableMicrosliceDescriptor(const StorableMicrosliceDescriptor& ms)
    : desc_(ms.desc_) {
      init_pointers();
    }
#pragma GCC diagnostic pop

StorableMicrosliceDescriptor::StorableMicrosliceDescriptor(StorableMicrosliceDescriptor&& ms) noexcept
    : desc_(ms.desc_) {
  init_pointers();
}

//StorableMicrosliceDescriptor::StorableMicrosliceDescriptor(const MicrosliceDescriptor& ms)
//     : fles::StorableMicrosliceDescriptor{ms} {}

StorableMicrosliceDescriptor::StorableMicrosliceDescriptor(MicrosliceDescriptor d)
    : desc_(d) // cannot use {}, see http://stackoverflow.com/q/19347004
      {
  init_pointers();
}

// StorableMicroslice::StorableMicroslice(MicrosliceDescriptor d,
//                                        std::vector<uint8_t> content_v)
//     : desc_(d), content_{std::move(content_v)} {
//   desc_.size = static_cast<uint32_t>(content_.size());
//   init_pointers();
// }

StorableMicrosliceDescriptor::StorableMicrosliceDescriptor() = default;

//void StorableMicroslice::initialize_crc() { desc_.crc = compute_crc(); }

} // namespace fles
