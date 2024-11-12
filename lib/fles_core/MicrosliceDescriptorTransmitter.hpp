// Copyright 2015 Jan de Cuveland <cmail@cuveland.de>
/// \file
/// \brief Defines the fles::MicrosliceTransmitter class.
#pragma once

#include "DualRingBuffer.hpp"
#include "Microslice.hpp"
#include "Sink.hpp"
#include <memory>

namespace fles {

/**
 * \brief The MicrosliceTransmitter class implements a mechanism to transmit
 * Microslices to an InputBufferWriteInterface object.
 */
class MicrosliceDescriptorTransmitter : public MicrosliceDescriptorSink {
public:
  /// Construct Microslice Transmitter connected to a given data sink.
  explicit MicrosliceDescriptorTransmitter(InputBufferWriteInterface& data_sink);

  /// Delete copy constructor (non-copyable).
  MicrosliceDescriptorTransmitter(const MicrosliceDescriptorTransmitter&) = delete;
  /// Delete assignment operator (non-copyable).
  void operator=(const MicrosliceDescriptorTransmitter&) = delete;

  ~MicrosliceDescriptorTransmitter() override = default;

  /**
   * \brief Transmit the next item.
   *
   * This function blocks if there is not enough space available.
   */
  void put(std::shared_ptr<const MicrosliceDescriptor> item) override;

  void end_stream() override { data_sink_.set_eof(true); }

private:
  bool try_put(const std::shared_ptr<const MicrosliceDescriptor>& item);

  /// Data sink (e.g., shared memory buffer).
  InputBufferWriteInterface& data_sink_;

  DualIndex write_index_ = {0, 0};
  DualIndex read_index_cached_ = {0, 0};
};
} // namespace fles
