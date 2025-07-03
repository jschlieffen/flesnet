#pragma once

#include "MicrosliceDescriptor.hpp"
#include "MicrosliceView.hpp"
#include "TimesliceComponentDescriptor.hpp"
#include "TimesliceDescriptor.hpp"
#include <fstream>
#include <vector>
#include <cstdint>
#include<algorithm>
#include<iostream>
#include <boost/serialization/access.hpp>
#include <boost/serialization/vector.hpp>


namespace fles{

class TDescriptor {

public:

  TDescriptor() = default;
/*
  TDescriptor(TimesliceDescriptor TSDesc){
    std::cout<<"test21"<<std::endl;
    timeslice_descriptor_ = TSDesc;
    std::cout<<"test22"<<std::endl;
    init_pointers();
    std::cout<<"test23"<<std::endl;
  }
*/
  TDescriptor(uint32_t num_core_microslices,
              uint64_t index = UINT64_MAX,
              uint64_t ts_pos = UINT64_MAX){
    timeslice_descriptor_.index = index;
    timeslice_descriptor_.ts_pos = ts_pos;
    timeslice_descriptor_.num_core_microslices = num_core_microslices;
    timeslice_descriptor_.num_components = 0;
  }

  [[nodiscard]] TimesliceDescriptor get_desc(){return timeslice_descriptor_;}
  //virtual ~TDescriptor();
      /// Retrieve the timeslice index.
  [[nodiscard]] uint64_t index() const { return timeslice_descriptor_.index; }

  /// Retrieve the number of core microslices.
  [[nodiscard]] uint64_t num_core_microslices() const {
    return timeslice_descriptor_.num_core_microslices;
  }

  /// Retrieve the total number of microslices.
  [[nodiscard]] uint64_t num_microslices(uint64_t component) const {
    return desc_ptr_[component]->num_microslices;
  }

  /// Retrieve the number of components (contributing input channels).
  [[nodiscard]] uint64_t num_components() const {
    return timeslice_descriptor_.num_components;
  }

  /// Retrieve the size of a given component.
  [[nodiscard]] uint64_t size_component(uint64_t component) const {
    return desc_ptr_[component]->size;
  }


  /// Retrieve the descriptor of a given microslice
  [[nodiscard]] const MicrosliceDescriptor&
  descriptor(uint64_t component, uint64_t microslice) const {
    return reinterpret_cast<const MicrosliceDescriptor*>(
        data_ptr_[component])[microslice];
  }


  uint32_t append_component(uint64_t num_microslices,
                            uint64_t /* dummy */ = 0) {
    TimesliceComponentDescriptor ts_desc = TimesliceComponentDescriptor();
    ts_desc.ts_num = timeslice_descriptor_.index;
    ts_desc.offset = 0;
    ts_desc.num_microslices = num_microslices;

    std::vector<uint8_t> data;
    for (uint64_t m = 0; m < num_microslices; ++m) {
      MicrosliceDescriptor desc = MicrosliceDescriptor();
      auto* desc_bytes = reinterpret_cast<uint8_t*>(&desc);
      data.insert(data.end(), desc_bytes,
                  desc_bytes + sizeof(MicrosliceDescriptor));
    }

    ts_desc.size = data.size();
    desc_.push_back(ts_desc);
    data_.push_back(data);
    uint32_t component = timeslice_descriptor_.num_components++;

    init_pointers();
    return component;
  }

//Nochmal genau anschauen, wie ich mir desc_ und data_ definiere.
 void append_ms_desc(uint32_t component,
                    uint64_t microslice,
                    MicrosliceDescriptor descriptor)
    {
    assert(component < timeslice_descriptor_.num_components);
    std::vector<uint8_t>& this_data = data_[component];
    TimesliceComponentDescriptor& this_desc = desc_[component];

    assert(microslice < this_desc.num_microslices);
    auto* desc_bytes = reinterpret_cast<uint8_t*>(&descriptor);

    // set offset relative to first microslice
    if (microslice > 0) {
      uint64_t offset = this_data.size() - this_desc.num_microslices *
                                               sizeof(MicrosliceDescriptor);
      uint64_t first_offset =
          reinterpret_cast<MicrosliceDescriptor*>(this_data.data())->offset;
      descriptor.offset = offset + first_offset;
    }

    std::copy(desc_bytes, desc_bytes + sizeof(MicrosliceDescriptor),
              &this_data[microslice * sizeof(MicrosliceDescriptor)]);
    //std::cout<<desc_bytes<<std::endl;
    //this_data.insert(this_data.end(), content, content + descriptor.size);
    this_desc.size = this_data.size();

    init_pointers();
  }



  /// Retrieve the offical start time of the timeslice
  [[nodiscard]] uint64_t start_time() const {
    if (num_components() != 0 && num_microslices(0) != 0) {
      return descriptor(0, 0).idx;
    }
    return 0;
  }

protected:


  //friend class StorableTimeslice;
  //friend class ::ManagedTimesliceBuffer;

  friend class StorableTimesliceDescriptor;

  /// The timeslice descriptor.
  TimesliceDescriptor timeslice_descriptor_{};

  /// A vector of pointers to the data content, one per timeslice component.
  std::vector<uint8_t*> data_ptr_;

  /// \brief A vector of pointers to the microslice descriptors, one per
  /// timeslice component.
  std::vector<TimesliceComponentDescriptor*> desc_ptr_;


  void init_pointers() {
    //std::cout<<"test41"<<std::endl;
    data_ptr_.resize(num_components());
    //std::cout<<"test42"<<std::endl;
    desc_ptr_.resize(num_components());
    //std::cout<<"test43"<<std::endl;
    for (size_t c = 0; c < num_components(); ++c) {
      desc_ptr_[c] = &desc_[c];
      //std::cout<<"test44"<<std::endl;
      //std::cout << "data_.size() = " << data_.size() << ", data_ptr_.size() = " << data_ptr_.size() << std::endl;
      //std::cout << "data_[c].size() = " << data_[c].size() << std::endl;
      data_ptr_[c] = data_[c].data();

      //std::cout<<"test45"<<std::endl;
    }
  }
  std::vector<std::vector<uint8_t>> data_;
  std::vector<TimesliceComponentDescriptor> desc_;
};

} // namespace fles

