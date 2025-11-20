
#include "LibfabricBarrier.hpp"
#include "MicrosliceDescriptor.hpp"
#include <inttypes.h>
#include <rdma/fabric.h>
#include <rdma/fi_endpoint.h>
#include <rdma/fi_domain.h>
#include <rdma/fabric.h>
#include <rdma/fi_endpoint.h>
#include <cstdio>
#include <cassert>
#include <vector>
#include <netinet/in.h>   // For sockaddr_in, sockaddr_in6
#include <arpa/inet.h>    // For inet_ntop
#include <sys/socket.h>   // For sockaddr
#include <cstring>        // For memset, etc.

//#include <arpa/inet.h>  
//#include <netinet/in.h> 

namespace tl_libfabric {

void LibfabricBarrier::create_barrier_instance(uint32_t remote_index,
                                               struct fid_domain* pd,
                                               bool is_root) {
  if (barrier_ == nullptr)
    barrier_ = new LibfabricBarrier(remote_index, pd, is_root);
  assert(LibfabricBarrier::barrier_ != nullptr);
}

LibfabricBarrier* LibfabricBarrier::get_instance() { return barrier_; }

LibfabricBarrier::~LibfabricBarrier() {}
LibfabricBarrier::LibfabricBarrier(uint32_t remote_index,
                                   struct fid_domain* pd,
                                   bool is_root)
    : LibfabricCollective(remote_index, pd), root_(is_root) {
  // TODO remote_index needed?
}

size_t LibfabricBarrier::call_barrier() {
  if (root_) {
    receive_all();
    broadcast();
  } else {
    broadcast(true);
    receive_all(true);
  }
  return 0;
}

void LibfabricBarrier::receive_all(bool only_root_eps) {
  std::vector<struct LibfabricCollectiveEPInfo*> endpoints =
      retrieve_endpoint_list();
  uint32_t count = 0;
  assert(endpoints.size() >= 1);
  for (uint32_t i = 0; i < endpoints.size(); i++) {
    if (!endpoints[i]->active || (only_root_eps && !endpoints[i]->root_ep))
      continue;
    recv(endpoints[i]);
    count++;
  }
  wait_for_recv_cq(count);
}

void LibfabricBarrier::broadcast(bool only_root_eps) {
  std::vector<struct LibfabricCollectiveEPInfo*> endpoints =
      retrieve_endpoint_list();
  assert(endpoints.size() > 0);
  std::cout<<"Endpoint size: "<<endpoints.size()<<std::endl;
  uint32_t count = 0;
  for (uint32_t i = 0; i < endpoints.size(); i++) {
    if (!endpoints[i]->active || (only_root_eps && !endpoints[i]->root_ep))
      continue;
    send(endpoints[i]);
    count++;
  }
  wait_for_send_cq(count);
}

void LibfabricBarrier::recv(const struct LibfabricCollectiveEPInfo* ep_info) {
  std::cout<<"test recv"<<std::endl;
  if (ep_info->recv_msg_wr.context == nullptr){
    L_(fatal)<<"context ist null";
  }
  else {
    L_(fatal)<<"context ist nicht null";
    std::cout << "recv context = " << ep_info->recv_msg_wr.context << std::endl;
  }
  int err = fi_trecvmsg(ep_info->ep, &ep_info->recv_msg_wr, FI_COMPLETION);
  if (err != 0) {
    L_(fatal) << "fi_recvmsg failed in LibfabricBarrier::recv: "
              << strerror(err);
    throw LibfabricException("fi_recvmsg failed");
  }
}


void LibfabricBarrier::send(const struct LibfabricCollectiveEPInfo* ep_info) {
  //sleep(10);
  if (ep_info->send_msg_wr.context == nullptr){
    L_(fatal)<<"context ist null";
  }
  else {
    L_(fatal)<<"context ist nicht null";
    std::cout << "send context = " << ep_info->send_msg_wr.context << std::endl;
  }
  int err = fi_tsendmsg(ep_info->ep, &ep_info->send_msg_wr, FI_COMPLETION);
  if (err != 0) {
    L_(fatal) << "fi_tsendmsg failed in LibfabricBarrier::v: " << strerror(err);
    throw LibfabricException("fi_tsendmsg failed");
  }
}



LibfabricBarrier* LibfabricBarrier::barrier_ = nullptr;
} // namespace tl_libfabric
