// Copyright 2015 Jan de Cuveland <cmail@cuveland.de>
/// \file
/// \brief Defines the fles::StorableMicrosliceDescriptor class.
#pragma once

#include "ArchiveDescriptor.hpp"
#include "MicrosliceDescriptor.hpp"
#include <boost/serialization/access.hpp>
#include <boost/serialization/vector.hpp>
#include <type_traits>
#include <vector>
#include <iostream>
#include <ostream>

namespace fles {

template <class Base, class Storable, ArchiveType archive_type>
class InputArchive;
template <class Base, class Storable, ArchiveType archive_type>
class InputArchiveLoop;
template <class Base, class Storable, ArchiveType archive_type>
class InputArchiveSequence;

/**
 * \brief The StorableMicrosliceDescriptor class contains the data of a single microslice.
 *
 * Both metadata and content are stored within the object.
 */
class StorableMicrosliceDescriptor : public MicrosliceDescriptor {
public:
  /// Copy constructor.
  StorableMicrosliceDescriptor(const StorableMicrosliceDescriptor& ms);
  /// Delete assignment operator (not implemented).
  void operator=(const StorableMicrosliceDescriptor&) = delete;
  /// Move constructor.
  StorableMicrosliceDescriptor(StorableMicrosliceDescriptor&& ms) noexcept;

  /// Construct by copying from given Microslice object.
  //StorableMicrosliceDescriptor(const MicrosliceDescriptor& ms);

  /**
   * \brief Construct by copying from given data array.
   *
   * Copy the descriptor and the data pointed to by `content` into the
   * StorableMicrosliceDescriptor. The `size` field of the descriptor must already
   * be valid and will not be modified.
   */
  StorableMicrosliceDescriptor(MicrosliceDescriptor d);

  /**
   * \brief Construct by copying from given data vector.
   *
   * Copy the descriptor and copy or move the data contained in
   * `content` into the StorableMicrosliceDescriptor. The descriptor will be
   * updated to match the size of the `content` vector.
   *
   * Copying the vector is avoided if it is passed as an rvalue,
   * like in:
   *
   *     StorableMicrosliceDescriptor {..., std::move(some_vector)}
   *     StorableMicrosliceDescriptor {..., {1, 2, 3, 4, 5}}
   *     StorableMicrosliceDescriptor {..., create_some_vector()}
   */
  //StorableMicrosliceDescriptor(MicrosliceDescriptor d, std::vector<uint8_t> content_v);

  /// Retrieve non-const microslice descriptor reference
  MicrosliceDescriptor& desc() {return desc_; };

  /// Retrieve a non-const pointer to the microslice data
  //uint8_t* content() { return content_ptr_; }

  //void initialize_crc();

private:
  friend class boost::serialization::access;
  friend class InputArchive_test<MicrosliceDescriptor,
                            StorableMicrosliceDescriptor,
                            ArchiveType::MicrosliceDescriptorArchive>;
  friend class InputArchive<MicrosliceDescriptor,
                            StorableMicrosliceDescriptor,
                            ArchiveType::MicrosliceDescriptorArchive>;
  friend class InputArchiveLoop<MicrosliceDescriptor,
                                StorableMicrosliceDescriptor,
                                ArchiveType::MicrosliceDescriptorArchive>;
  friend class InputArchiveSequence<MicrosliceDescriptor,
                                    StorableMicrosliceDescriptor,
                                    ArchiveType::MicrosliceDescriptorArchive>;

  StorableMicrosliceDescriptor();

  template <class Archive>
  void serialize(Archive& ar, const unsigned int /* version */) {
    ar& desc_;
    init_pointers();
  }
  
  void init_pointers() {
    hdr_id = desc_.hdr_id;  
    hdr_ver = desc_.hdr_ver; 
    eq_id = desc_.eq_id;  
    flags = desc_.flags;  
    sys_id = desc_.sys_id;  
    sys_ver = desc_.sys_ver; 
    idx = desc_.idx;    
    crc = desc_.crc;    
    size = desc_.size;   
    offset = desc_.offset; 


  }

  MicrosliceDescriptor desc_{};
  //std::vector<uint8_t> content_;
};

} // namespace fles
