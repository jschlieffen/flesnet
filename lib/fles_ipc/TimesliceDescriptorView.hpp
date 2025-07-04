// Copyright 2013 Jan de Cuveland <cmail@cuveland.de>
/// \file
/// \brief Defines the fles::TimesliceDescriptorView class.
#pragma once

#include "ItemWorkerProtocol.hpp"
//#include "Timeslice.hpp"
#include "TDescriptor.hpp"
//#include "TimesliceShmWorkItem.hpp"
#include "TimesliceDescriptorShmWorkItem.hpp"
#include <boost/interprocess/managed_shared_memory.hpp>
#include <memory>

namespace fles {

template <class Base, class View> class Receiver;

/**
 * \brief The TimesliceDescriptorView class provides access to the data of a single
 * timeslice in memory.
 */
class TimesliceDescriptorView : public TDescriptor {
public:
  /// Delete copy constructor (non-copyable).
  TimesliceDescriptorView(const TimesliceDescriptorView&) = delete;
  /// Delete assignment operator (non-copyable).
  void operator=(const TimesliceDescriptorView&) = delete;

  ~TimesliceDescriptorView() = default;

private:
  friend class Receiver<TDescriptor, TimesliceDescriptorView>;
  friend class StorableTimeslice;

  TimesliceDescriptorView(
      std::shared_ptr<boost::interprocess::managed_shared_memory> managed_shm,
      std::shared_ptr<const Item> work_item,
      const TimesliceDescriptorShmWorkItem& timeslice_item);

  std::shared_ptr<boost::interprocess::managed_shared_memory> managed_shm_;
  std::shared_ptr<const Item> work_item_;
  fles::TimesliceDescriptorShmWorkItem timeslice_item_;
};

} // namespace fles
