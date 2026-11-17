/* Copyright (C) 2026 FIAS, Goethe-Universität Frankfurt am Main
   SPDX-License-Identifier: GPL-3.0-only
   Author: Jan de Cuveland */

#include "TDescriptorShmSink.hpp"
#include "SubTimeslice.hpp"
#include "Timeslice.hpp"
#include "Utility.hpp"
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <format>
#include <stdexcept>
#include <thread>
#include <utility>
#include "TDescriptor.hpp"   // whatever the actual file is called

namespace fles {

TDescriptorShmSink::TDescriptorShmSink(zmq::context_t& context,
                                   std::string shm_identifier,
                                   std::size_t buffer_size)
    : m_buffer(context, std::move(shm_identifier), buffer_size) {}

void TDescriptorShmSink::put(std::shared_ptr<const TDescriptor> timeslice) {
  handle_completions();

  const uint64_t id = timeslice->index();

  tsb::StDescriptor desc;
  desc.start_time_ns = timeslice->start_time();
  desc.duration_ns = timeslice->duration();
  desc.flags = timeslice->flags();
  uint64_t size = 0;
  for (uint64_t c = 0; c < timeslice->num_components(); ++c) {
    tsb::StComponentDescriptor& component = desc.components.emplace_back();
    component.ms_data_offset = static_cast<std::ptrdiff_t>(size);
    component.ms_data_size = timeslice->size_component(c);
    component.num_microslices = timeslice->num_microslices(c);
    component.flags = timeslice->desc_ptr_[c]->flags;
    size += component.ms_data_size;
  }

  if (size > m_buffer.get_size()) {
    throw std::runtime_error(std::format(
        "timeslice {} of size {} does not fit into shared memory of size {}",
        id, human_readable_count(size, true),
        human_readable_count(m_buffer.get_size(), true)));
  }

  // Wait for timeslices to be released until the allocation succeeds
  std::byte* buffer = nullptr;
  while ((buffer = m_buffer.allocate(std::max<uint64_t>(size, 1))) == nullptr) {
    if (m_buffer.empty()) {
      throw std::runtime_error(std::format(
          "failed to allocate {} for timeslice {} in empty shared memory",
          human_readable_count(size, true), id));
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    handle_completions();
  }

  // for (uint64_t c = 0; c < timeslice->num_components(); ++c) {
  //   const auto& component = desc.components[c];
  //   std::memcpy(buffer + component.ms_data_offset, timeslice->data_ptr_[c],
  //               component.ms_data_size);
  // }
  for (uint64_t c = 0; c < timeslice->num_components(); ++c) {
    const auto& component = desc.components[c];
    const uint64_t n = component.num_microslices;
    if (n == 0) {
      continue;
    }
    std::byte* dst = buffer + component.ms_data_offset;

    // 1. The microslice descriptor array
    const std::size_t desc_bytes = n * sizeof(MicrosliceDescriptor);
    std::memcpy(dst, &timeslice->descriptor(c, 0), desc_bytes);

    // 2. The contents, one microslice at a time, at the same relative offsets
    const uint64_t base = timeslice->descriptor(c, 0).offset;
    for (uint64_t m = 0; m < n; ++m) {
      std::shared_ptr<fles::Microslice> ms =
          std::make_shared<fles::MicrosliceView>(timeslice->get_microslice(c, m));

      const MicrosliceDescriptor& md = ms->desc();
      const uint64_t rel = md.offset - base;
      if (desc_bytes + rel + md.size > component.ms_data_size) {
        throw std::runtime_error(std::format(
            "timeslice {}: microslice {} of component {} exceeds component size",
            id, m, c));
      }
      std::memcpy(dst + desc_bytes + rel, ms->content(), md.size);
    }
  }
  for (auto& component : desc.components) {
    component.ms_data_offset += m_buffer.offset_of(buffer);
  }
  m_buffer.send_work_item(id, desc, reinterpret_cast<std::uintptr_t>(buffer));
}

void TDescriptorShmSink::handle_completions() {
  while (auto completion = m_buffer.try_receive_completion()) {
    m_buffer.deallocate(reinterpret_cast<std::byte*>(completion->user_data));
  }
}

} // namespace fles
