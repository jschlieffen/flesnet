#pragma once


#include "DualRingBuffer.hpp"
#include "MicrosliceDescriptor.hpp"
#include "RingBuffer.hpp"
#include "RingBufferView.hpp"
#include "log.hpp"
#include <algorithm>
#include <random>


class PatternGenerator : public fles::MicrosliceDescriptor {
public:

    PatternGenerator(uint64_t index,
                    unsigned int min_size,
                    unsigned int max_size,
                    uint64_t offset_);


    PatternGenerator(const PatternGenerator&) = delete;
    void operator=(const PatternGenerator&) = delete;

    void generate_desc();

    unsigned int Poisson_with_bounds(unsigned int lower, unsigned int upper);

    

private: 
    std::default_random_engine random_generator_;

    uint64_t index_given;
    unsigned int min_size_;
    unsigned int max_size_;
    uint64_t offset_current;
};