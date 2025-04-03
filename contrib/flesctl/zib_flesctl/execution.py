#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:28:18 2025

@author: jschlieffen
"""

import params as par
import central_manager as cm
import time
import sys
import signal
from log_msg import *

# =============================================================================
# TODOs: 1. make a possibility to disable grafana done
#        2. improve monotoring 
#        3. search for env- variables that may overwrite the config variables
#           done except input file list done
#        4. comment code 
#        5. write documentation for the code. 
#        6. make a fitting implementation for the use of sbatch
#        7. make zeromq implementation. (big problem I guess? different log files) done
#        8. make implementation for libfabric (get libabric run first) 
#           (maybe to complicated at first do this when I have the time to.)
# =============================================================================
class exec_:
    
    def __init__(self):
        self.Par_ = par.Params('config.cfg')
        self.Par_.validation_params()
        logger.success('Params valid and successfully set')
        self.execution_cls = None
        self.running = True
        self.start_time = 0
        self.end_time = 0

    def start_sim(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        self.execution_cls = cm.execution(self.Par_.input_file_list, self.Par_.entry_nodes, self.Par_.build_nodes, 
                                     self.Par_.show_total_data, self.Par_.influx_node_ip, self.Par_.influx_token,
                                     self.Par_.use_grafana, self.Par_.overlap_usage_of_nodes, self.Par_.path, 
                                     self.Par_.transport_method, self.Par_.customize_string, self.Par_.show_graph,
                                     self.Par_.show_progress_bar, self.Par_.show_only_entry_nodes)
        self.start_time = time.time()
        self.execution_cls.start_Flesnet()
        total_data, avg_data_rate = self.execution_cls.stop_via_ctrl_c()
        self.end_time = time.time()
        
        self.create_end_message(total_data,avg_data_rate)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        
    def signal_handler(self,signum, frame):
        if signum == signal.SIGINT:
            print(f'\033[31mERROR: received signal {signum}. Handling termination\033[0m')
        elif signum == signal.SIGTERM:
            print(f'\033[31mERROR: received signal {signum}. Handling termination\033[0m')
        self.cleanup()
    
    def cleanup(self):
        if self.Par_.overlap_usage_of_nodes:
            self.execution_cls.super_nodes_cls.stop_flesnet()
        else:
            self.execution_cls.entry_nodes_cls.stop_flesnet()
            self.execution_cls.build_nodes_cls.stop_flesnet()
        #self.end_time = time.time()
        self.running = False
        sys.exit(1)
    
    def create_end_message(self,total_data, avg_data_rate):
        if self.running:
            elapsed_seconds = self.end_time - self.start_time
            hours, remainder = divmod(elapsed_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            #formatted_time = f"\033[36mSTATUS: The simulation ran for {int(hours):02d}H:{int(minutes):02d}M:{int(seconds):02d}S\033[0m"
            #print(formatted_time)
            #data_rate_str = f"\033[36mSTATUS: Total data send: {total_data} GB, with average data rate: {avg_data_rate} GB/s\033[0m"
            #print(data_rate_str)
            formatted_time = f"The simulation ran for {int(hours):02d}H:{int(minutes):02d}M:{int(seconds):02d}"
            logger.info(formatted_time)
            #logger.info('test')
            data_rate_str = f"Total data send: {total_data} GB, with average data rate: {avg_data_rate} GB/s"
            logger.info(f"Total data send: {total_data} GB, with average data rate: {avg_data_rate} GB/s")
        
def main():
    exe = exec_()
    exe.start_sim()

if __name__ == '__main__':
    main()
        