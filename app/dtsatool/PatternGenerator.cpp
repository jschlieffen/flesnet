#include "PatternGenerator.hpp"
#include <random>

PatternGenerator::PatternGenerator(uint64_t index,
                                unsigned int min_size,
                                unsigned int max_size,
                                uint64_t offset_){
                                    
                                    index_given = index;
                                    min_size_ = min_size;
                                    max_size_ = max_size;
                                    offset_current = offset_;
                                    std::random_device rd;
                                    random_generator_.seed(rd());                                
                                    generate_desc();

                    }

unsigned int PatternGenerator::Poisson_with_bounds(unsigned int lower, unsigned int upper){
    float lambda = (lower+upper)/2;

    std::poisson_distribution<unsigned int> random_distribution_(lambda);
    unsigned int rand_num = random_distribution_(random_generator_);
    return std::clamp(rand_num, lower, upper);
}

void PatternGenerator::generate_desc(){

    hdr_id = static_cast<uint8_t>(fles::HeaderFormatIdentifier::Standard);
    hdr_ver = static_cast<uint8_t>(fles::HeaderFormatVersion::Standard);
    eq_id = 0xE001;
    flags = 0x0000;
    sys_id = static_cast<uint8_t>(fles::Subsystem::FLES);
    sys_ver = static_cast<uint8_t>(fles::SubsystemFormatFLES::BasicRampPattern);
    idx = index_given;
    offset = offset_current;
    crc = 0x00000000; //currently w.o crc.
    size = Poisson_with_bounds(min_size_,max_size_);

}