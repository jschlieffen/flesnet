// Copyright 2013, 2015 Jan de Cuveland <cmail@cuveland.de>
/// \file
/// \brief Defines the fles::InputArchive template class.
#pragma once

#include "ArchiveDescriptor.hpp"
#include "MicrosliceDescriptor.hpp"
#include "Microslice.hpp"
#include "Source.hpp"
#include "StorableMicrosliceDescriptor.hpp"
#include <boost/archive/binary_iarchive.hpp>
#include <type_traits>
#ifdef BOOST_IOS_HAS_ZSTD
  #include <boost/iostreams/filter/zstd.hpp>
#endif
#include <boost/iostreams/filtering_stream.hpp>
#include <fstream>
#include <memory>
#include <string>
#include <iostream>

namespace fles {

/**
 * \brief The InputArchive class deserializes data sets from an input file.
 */
template <class Base, class Storable, ArchiveType archive_type>
class InputArchive_alloc : public Source<Base> {
public:
  /**
   * \brief Construct an input archive object, open the given archive file for
   * reading, and read the archive descriptor.
   *
   * \param filename File name of the archive file
   */
  explicit InputArchive_alloc(const std::string& filename) {
    ifstream_ =
        std::make_unique<std::ifstream>(filename.c_str(), std::ios::binary);
    if (!*ifstream_) {
      throw std::ios_base::failure("error opening file \"" + filename + "\"");
    }

    iarchive_ = std::make_unique<boost::archive::binary_iarchive>(*ifstream_);

    *iarchive_ >> descriptor_;
    if (descriptor_.archive_type() != archive_type) {
      throw std::runtime_error("File \"" + filename +
                               "\" is not of correct archive type");
    }

    if (descriptor_.archive_compression() != ArchiveCompression::None) {
#ifdef BOOST_IOS_HAS_ZSTD
      in_ = std::make_unique<boost::iostreams::filtering_istream>();
      if (descriptor_.archive_compression() == ArchiveCompression::Zstd) {
        in_->push(boost::iostreams::zstd_decompressor());
      } else {
        throw std::runtime_error(
            "Unsupported compression type for input archive file \"" +
            filename + "\"");
      }
      in_->push(*ifstream_);
      iarchive_ = std::make_unique<boost::archive::binary_iarchive>(
          *in_, boost::archive::no_header);
#else
      throw std::runtime_error(
          "Unsupported compression type for input archive file \"" +
          filename + "\"");
#endif
    }
  }

  /// Delete copy constructor (non-copyable).
  InputArchive_alloc(const InputArchive_alloc&) = delete;
  /// Delete assignment operator (non-copyable).
  void operator=(const InputArchive_alloc&) = delete;

  ~InputArchive_alloc() override = default;

  /// Read the next data set.
  std::unique_ptr<Storable> get() {
    return std::unique_ptr<Storable>(do_get());
  };

  /// Retrieve the archive descriptor.
  [[nodiscard]] const ArchiveDescriptor& descriptor() const {
    return descriptor_;
  };

  [[nodiscard]] bool eos() const override { return eos_; }
  int it_counter = 0;
  int c1 = 0;
  uint64_t idx_old = 1;
  uint64_t idx_new = 2;
  unsigned long long pos1 = 113;

private:
  Storable* do_get() override {
    //std::cout<<"test"<<std::endl;
    if (eos_) {
      return nullptr;
    }
    //int i = 0;
    Storable* sts = nullptr;
    try {
      //std::cout<<"test"<<std::endl;
      sts = new Storable(); // NOLINT
      //i++;
      //std::cout<<i<< " test"<<std::endl;
      //
      //  MyMSDesc desc;
      //  auto file_ptr = iarchive_.get_pointer();
      //  if (!file_ptr)
      //    break;
      //  desc.deserialize(file_ptr);
      //  file_ptr += desc.size;
      //
      //auto file_ptr = iarchive_.get_pointer();
      *iarchive_ >> *sts;
      //idx_new = sts->desc().idx;
      // if (idx_old >= idx_new){
      //   unsigned long long pos_test_2 = static_cast<unsigned long long>(ifstream_->tellg());
      //   unsigned long long pos_test = pos_test_2+sts->desc().size;
      //   std::cout<<"pos:    "<<unsigned(ifstream_->tellg())+sts->desc().size<<std::endl;
      //   std::cout<<"pos_t:  "<<pos_test<<std::endl;
      //   std::cout<<"size:   "<<sts->desc().size<<std::endl;
      //   std::cout<<"offset: "<<sts->desc().offset<<std::endl;
      //   std::cout<<"index:  "<<sts->desc().idx<<std::endl;
      //   //std::cout<<"test1123"<<std::endl;
      //   std::cout<<"it_c:   "<<it_counter<<std::endl;
      //   std::cout<<std::endl;
      //   c1++;
      // }
      it_counter++;
      
      //idx_old = idx_new;
      //std::cout<<it_counter<<std::endl;
      //unsigned long long pos = static_cast<unsigned long long>(ifstream_->tellg());
      //ifstream_->seekg(pos+sts->desc().size+8);
      pos1= pos1 + sts->desc().size+40;
      //std::cout<<"test"<<std::endl;
      // if (it_counter < 10){
      //   std::cout<<"current pos:  "<<unsigned(ifstream_->tellg())<<std::endl;
      //   std::cout<<"calc. pos:    "<<pos1<<std::endl;
      //   std::cout<<"diff:         "<<unsigned(ifstream_->tellg())-pos1<<std::endl<<std::endl;
      // } 
      ifstream_->seekg(pos1);
    } catch (boost::archive::archive_exception& e) {
      if (e.code == boost::archive::archive_exception::input_stream_error) {
        delete sts; // NOLINT
        eos_ = true;
        return nullptr;
      }
      throw;
    }
    return sts;
  }

  std::unique_ptr<std::ifstream> ifstream_;
  std::unique_ptr<boost::iostreams::filtering_istream> in_;
  std::unique_ptr<boost::archive::binary_iarchive> iarchive_;
  ArchiveDescriptor descriptor_;

  bool eos_ = false;
};

} // namespace fles
