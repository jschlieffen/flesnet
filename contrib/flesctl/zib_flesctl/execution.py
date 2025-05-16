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
import os
os.environ['write_logfile'] = '1'
from log_msg import *
import logfile_gen as Logfile

# =============================================================================
# TODOs:1. finish timeslice-forwarding 
#       2. restructure file and folder org.
#       3. collectl connection
#       4. make possibility to name the flesnet logfile
#       5. make implementation for libfrabric
# =============================================================================

# =============================================================================
# This file is the execution file. It starts the logger, signal handler and 
# the central manager. 
# =============================================================================

# =============================================================================
# TODO timeslice-forwarding:
#       1. params for the timeslice-forwarding
#       2. start in execution file
#       3. restructure assembling in nodes
#       4. rewriting allocation
#       5. testing
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

    # =============================================================================
    # Starts the simulation  
    # =============================================================================
    def start_sim(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        self.execution_cls = cm.execution(self.Par_.input_file_list, self.Par_.entry_nodes, self.Par_.build_nodes, 
                                     self.Par_.show_total_data, self.Par_.influx_node_ip, self.Par_.influx_token,
                                     self.Par_.use_grafana, self.Par_.overlap_usage_of_nodes, self.Par_.path, 
                                     self.Par_.transport_method, self.Par_.customize_string, self.Par_.show_graph,
                                     self.Par_.show_progress_bar, self.Par_.show_only_entry_nodes, self.Par_.use_pattern_gen,
                                     self.Par_.use_dmsa_files, self.Par_.set_node_list, self.Par_.entry_nodes_list,
                                     self.Par_.build_nodes_list, self.Par_.activate_timesliceforwarding, 
                                     self.Par_.write_data_to_file, self.Par_.analyze_data, self.Par_.port)
        Logfile.logfile.transport_method = self.Par_.transport_method
        self.start_time = time.time()
        
        self.execution_cls.start_Flesnet()
        total_data, avg_data_rate = self.execution_cls.stop_via_ctrl_c()
        self.end_time = time.time()
        Logfile.logfile.exec_time = self.end_time - self.start_time
        Logfile.logfile.avg_data_rate = avg_data_rate
        self.create_end_message(total_data,avg_data_rate)
        Logfile.logfile.write()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    
    # =============================================================================
    # Defines the signal handler for a clean end of the experiment. Currently only
    # ctrl+c and sigterm are implemented. For safety reasons sigkill is not 
    # implemented so it is recommended to only use it if the other two fails
    # May be changed in the furture
    # =============================================================================
    def signal_handler(self,signum, frame):
        if signum == signal.SIGINT:
            logger.error(f'received signal {signum}. Handling termination')
            self.cleanup()
        elif signum == signal.SIGTERM:
            logger.error(f'received signal {signum}. Handling termination')
            self.cleanup()
    
    def cleanup(self):
        if self.Par_.overlap_usage_of_nodes:
            self.execution_cls.super_nodes_cls.stop_flesnet()
        else:
            self.execution_cls.entry_nodes_cls.stop_flesnet()
            self.execution_cls.build_nodes_cls.stop_flesnet()
        if self.Par_.activate_timesliceforwarding:
            print('test123')
            self.execution_cls.timeslice_forwarding_cls.stop_timeslice_forwarding()
        self.running = False
        self.create_logfile()
        sys.exit(1)
        
    
    def create_logfile(self):
        Logfile.logfile.write()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
            
    def create_end_message(self,total_data, avg_data_rate):
        if self.running:
            elapsed_seconds = self.end_time - self.start_time
            hours, remainder = divmod(elapsed_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_time = f"The simulation ran for {int(hours):02d}H:{int(minutes):02d}M:{int(seconds):02d}S"
            logger.info(formatted_time)
            data_rate_str = f"Total data send: {total_data} GB, with average data rate: {avg_data_rate} GB/s"
            logger.info(data_rate_str)
        
def main():
    exe = exec_()
    exe.start_sim()

if __name__ == '__main__':
    main()
        