/**
 * @file
 * @author Dirk Hutter <hutter@compeng.uni-frankfurt.de>
 *
 */

#include "cri_device.hpp"
#include "cri_link.hpp"
#include "cri_registers.hpp"
#include "data_structures.hpp"
#include "pda/device.hpp"
#include "pda/device_operator.hpp"
#include "pda/pci_bar.hpp"
#include "register_file_bar.hpp"
#include <arpa/inet.h> // ntohl
#include <ctime>
#include <iomanip>

namespace cri {

cri_device::cri_device(int device_nr) {
  m_device_op =
      std::unique_ptr<pda::device_operator>(new pda::device_operator());
  m_device = std::unique_ptr<pda::device>(
      new pda::device(m_device_op.get(), device_nr));
  init();
}

cri_device::cri_device(uint8_t bus, uint8_t device, uint8_t function) {
  m_device_op = nullptr;
  m_device =
      std::unique_ptr<pda::device>(new pda::device(bus, device, function));
  init();
}

cri_device::~cri_device() = default;

void cri_device::init() {
  m_bar = std::unique_ptr<pda::pci_bar>(new pda::pci_bar(m_device.get(), 0));
  // register file access
  m_register_file =
      std::unique_ptr<register_file_bar>(new register_file_bar(m_bar.get(), 0));
  // enforce correct magic number and hw version
  check_magic_number();
  check_hw_ver(hw_ver_table);
  // create link objects
  uint8_t num_links = number_of_hw_links();
  for (size_t i = 0; i < num_links; i++) {
    m_link.push_back(std::unique_ptr<cri_link>(
        new cri_link(i, m_device.get(), m_bar.get())));
  }
  // init cached variable
  m_reg_perf_interval_cached = m_register_file->get_reg(CRI_REG_SYS_PERF_INT);
}

bool cri_device::check_hw_ver(std::array<uint16_t, 1> hw_ver_table) {
  uint16_t hw_ver = m_register_file->get_reg(0) >> 16; // CRI_REG_HARDWARE_INFO;
  bool match = false;

  // check if version of hardware is part of suported versions
  for (auto it = hw_ver_table.begin();
       it != hw_ver_table.end() && match == false; ++it) {
    if (hw_ver == *it) {
      match = true;
    }
  }
  if (!match) {
    std::stringstream msg;
    msg << "Hardware - libcri version missmatch! CRI ver: " << hw_ver;
    throw CriException(msg.str());
  }

  // INFO: disabled check to allow 'mixed' hw headers
  // check if version of hardware matches exactly version of header
  if (hw_ver != CRI_C_HARDWARE_VERSION) {
    match = false;
  }
  if (!match) {
    std::stringstream msg;
    msg << "Header file version missmatch! CRI ver: " << hw_ver;
    throw CriException(msg.str());
  }
  return match;
}

// void cri_device::enable_mc_cnt(bool enable) {
//   m_register_file->set_bit(CRI_REG_MC_CNT_CFG, 31, enable);
// }
//
// void cri_device::set_mc_time(uint32_t time) {
//   // time: 31 bit wide, in units of 8 ns
//   uint32_t reg = m_register_file->get_reg(CRI_REG_MC_CNT_CFG);
//   reg = (reg & ~0x7FFFFFFF) | (time & 0x7FFFFFFF);
//   m_register_file->set_reg(CRI_REG_MC_CNT_CFG, reg);
// }

uint8_t cri_device::number_of_hw_links() {
  return (m_register_file->get_reg(CRI_REG_N_CHANNELS) & 0xFF);
}

uint16_t cri_device::hardware_version() {
  return (static_cast<uint16_t>(m_register_file->get_reg(0) >> 16));
  // CRI_REG_HARDWARE_INFO
}

time_t cri_device::build_date() {
  time_t time = (static_cast<time_t>(
      m_register_file->get_reg(CRI_REG_BUILD_DATE_L) |
      (static_cast<uint64_t>(m_register_file->get_reg(CRI_REG_BUILD_DATE_H))
       << 32)));
  return time;
}

std::string cri_device::build_host() {
  uint32_t host[4];
  host[0] = ntohl(m_register_file->get_reg(CRI_REG_BUILD_HOST_3)); // NOLINT
  host[1] = ntohl(m_register_file->get_reg(CRI_REG_BUILD_HOST_2)); // NOLINT
  host[2] = ntohl(m_register_file->get_reg(CRI_REG_BUILD_HOST_1)); // NOLINT
  host[3] = ntohl(m_register_file->get_reg(CRI_REG_BUILD_HOST_0)); // NOLINT
  return std::string(reinterpret_cast<const char*>(host));
}

std::string cri_device::build_user() {
  uint32_t user[4];
  user[0] = ntohl(m_register_file->get_reg(CRI_REG_BUILD_USER_3)); // NOLINT
  user[1] = ntohl(m_register_file->get_reg(CRI_REG_BUILD_USER_2)); // NOLINT
  user[2] = ntohl(m_register_file->get_reg(CRI_REG_BUILD_USER_1)); // NOLINT
  user[3] = ntohl(m_register_file->get_reg(CRI_REG_BUILD_USER_0)); // NOLINT
  return std::string(reinterpret_cast<const char*>(user));
}

struct build_info_t cri_device::build_info() {
  build_info_t info;

  info.date = build_date();
  info.host = build_host();
  info.user = build_user();
  info.rev[0] = m_register_file->get_reg(CRI_REG_BUILD_REV_0);
  info.rev[1] = m_register_file->get_reg(CRI_REG_BUILD_REV_1);
  info.rev[2] = m_register_file->get_reg(CRI_REG_BUILD_REV_2);
  info.rev[3] = m_register_file->get_reg(CRI_REG_BUILD_REV_3);
  info.rev[4] = m_register_file->get_reg(CRI_REG_BUILD_REV_4);
  info.hw_ver = hardware_version();
  info.clean = ((m_register_file->get_reg(CRI_REG_BUILD_FLAGS) & 0x1) != 0u);
  info.repo = (m_register_file->get_reg(CRI_REG_BUILD_FLAGS) & 0x6) >> 1;
  return info;
}

std::string cri_device::print_build_info() {
  build_info_t build = build_info();

  // TODO: hack to overcome gcc limitation, for c++11 use:
  // std::put_time(std::localtime(&build.date), "%c %Z")
  char mbstr[100];
  std::strftime(mbstr, sizeof(mbstr), "%c %Z UTC%z",
                std::localtime(&build.date));

  std::stringstream ss;
  ss << "CRI Build Info:" << std::endl
     << "Build Date:     " << mbstr << std::endl
     << "Build Source:   " << build.user << "@" << build.host << std::endl;
  switch (build.repo) {
  case 1:
    ss << "Build from a git repository" << std::endl
       << "Repository Revision: " << std::hex << std::setfill('0')
       << std::setw(8) << build.rev[4] << std::setfill('0') << std::setw(8)
       << build.rev[3] << std::setfill('0') << std::setw(8) << build.rev[2]
       << std::setfill('0') << std::setw(8) << build.rev[1] << std::setfill('0')
       << std::setw(8) << build.rev[0] << std::endl;
    break;
  case 2:
    ss << "Build from a svn repository" << std::endl
       << "Repository Revision: " << std::dec << build.rev[0] << std::endl;
    break;
  default:
    ss << "Build from a unknown repository" << std::endl;
    break;
  }
  if (build.clean) {
    ss << "Repository Status:   clean " << std::endl;
  } else {
    ss << "Repository Status:   NOT clean " << std::endl;
  }
  ss << "Hardware Version:    " << std::dec << build.hw_ver;
  return ss.str();
}

std::string cri_device::print_devinfo() {
  std::stringstream ss;
  ss << std::hex << std::setw(2) << std::setfill('0')
     << static_cast<unsigned>(m_device->bus()) << ":" << std::setw(2)
     << std::setfill('0') << static_cast<unsigned>(m_device->slot()) << "."
     << static_cast<unsigned>(m_device->func());
  return ss.str();
}

size_t cri_device::number_of_links() { return m_link.size(); }

std::vector<cri_link*> cri_device::links() {
  std::vector<cri_link*> links;
  for (auto& l : m_link) {
    links.push_back(l.get());
  }
  return links;
}

cri_link* cri_device::link(size_t n) { return m_link.at(n).get(); }

void cri_device::id_led(bool enable) {
  m_register_file->set_bit(CRI_REG_APP_CFG, 0, enable);
}

void cri_device::set_testreg(uint32_t data) {
  m_register_file->set_reg(CRI_REG_TESTREG_DEVICE, data);
}

uint32_t cri_device::get_testreg() {
  return m_register_file->get_reg(CRI_REG_TESTREG_DEVICE);
}

//////*** Performance Counters ***//////

// set messurement avaraging interval in ms (max 17s)
void cri_device::set_perf_interval(uint32_t interval) {
  if (interval > 17000) {
    interval = 17000;
  }
  m_reg_perf_interval_cached = interval * (pci_clk * 1E-3);
  m_register_file->set_reg(CRI_REG_SYS_PERF_INT, m_reg_perf_interval_cached);
}

// get configured perf interval in clock cycles
uint32_t cri_device::get_perf_interval_cycles() {
  return m_reg_perf_interval_cached;
}

// back pressure from pcie core (cycles)
uint32_t cri_device::get_pci_stall() {
  return m_register_file->get_reg(CRI_REG_PERF_PCI_NRDY);
}

// words accepted from pcie core (cycles)
uint32_t cri_device::get_pci_trans() {
  return m_register_file->get_reg(CRI_REG_PERF_PCI_TRANS);
}

// max. duration of continious back pressure from pcie core (us)
float cri_device::get_pci_max_stall() {
  float pci_max_stall =
      static_cast<float>(m_register_file->get_reg(CRI_REG_PERF_PCI_MAX_NRDY));
  return pci_max_stall * (1.0 / pci_clk) * 1E6;
}

dma_perf_data_t cri_device::get_dma_perf() {
  std::array<uint32_t, 9> raw_data;
  m_register_file->set_reg(CRI_REG_UNI_CFG, 3); // capture and reset
  m_register_file->get_mem(CRI_REG_PERF_CYCLE_CNT, raw_data.data(), 9);

  dma_perf_data_t data{};
  if (raw_data[0] == 0xFFFFFFFF) {
    data.overflow = 1;
  } else {
    data.overflow = 0;
    data.cycle_cnt = raw_data[0];
    data.fifo_fill[0] = raw_data[1];
    data.fifo_fill[1] = raw_data[2];
    data.fifo_fill[2] = raw_data[3];
    data.fifo_fill[3] = raw_data[4];
    data.fifo_fill[4] = raw_data[5];
    data.fifo_fill[5] = raw_data[6];
    data.fifo_fill[6] = raw_data[7];
    data.fifo_fill[7] = raw_data[8];
  }
  return data;
}

register_file_bar* cri_device::rf() const { return m_register_file.get(); }

bool cri_device::check_magic_number() {
  // CRI_REG_HARDWARE_INFO
  if ((m_register_file->get_reg(0) & 0xFFFF) != CRI_C_HARDWARE_ID) {
    std::stringstream msg;
    msg << "Cannot read magic number! \n Try to reinitialize CRI";
    throw CriException(msg.str());
  }
  return true;
}
} // namespace cri