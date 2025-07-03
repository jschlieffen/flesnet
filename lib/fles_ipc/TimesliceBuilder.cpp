// Copyright 2013 Jan de Cuveland <cmail@cuveland.de>

#include "TimesliceBuilder.hpp"

#include <algorithm>

namespace fles {

TimesliceBuilder::TimesliceBuilder(const TimesliceBuilder& ts)
    : Timeslice(ts), data_(ts.data_), desc_(ts.desc_) {
  init_pointers();
}

TimesliceBuilder::TimesliceBuilder(TimesliceBuilder&& ts) noexcept
    : Timeslice(ts), data_(std::move(ts.data_)), desc_(std::move(ts.desc_)) {
  init_pointers();
}

TimesliceBuilder::TimesliceBuilder(const Timeslice& ts)
    : data_(ts.timeslice_descriptor_.num_components),
      desc_(ts.timeslice_descriptor_.num_components) {
  timeslice_descriptor_ = ts.timeslice_descriptor_;
  for (std::size_t component = 0;
       component < ts.timeslice_descriptor_.num_components; ++component) {
    uint64_t size = ts.desc_ptr_[component]->size;
    data_[component].resize(size);
    std::copy_n(ts.data_ptr_[component], size, data_[component].begin());
    desc_[component] = *ts.desc_ptr_[component];
  }

  init_pointers();
}

TimesliceBuilder::TimesliceBuilder() = default;

} // namespace fles
