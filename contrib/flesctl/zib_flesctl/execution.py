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

#TODO: make timeslice-forwarding cpu ids 
# =============================================================================
# TODOs:
#       1. restructure file and folder org.                 improvement needed
#       2. make implementation for libfrabric
# =============================================================================

# =============================================================================
# This file is the execution file. It starts the logger, signal handler and 
# the central manager. 
# =============================================================================

class exec_:
    
    def __init__(self):
        self.clean_files()
        self.Par_ = par.Params('config.cfg')
        foobar = self.Par_.validation_params(False)
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
        '''
        self.execution_cls = cm.execution(self.Par_.input_file_list, self.Par_.entry_nodes, self.Par_.build_nodes, 
                                     self.Par_.show_total_data, self.Par_.influx_node_ip, self.Par_.influx_token,
                                     self.Par_.use_grafana, self.Par_.overlap_usage_of_nodes, self.Par_.path, 
                                     self.Par_.transport_method, self.Par_.customize_string, self.Par_.show_graph,
                                     self.Par_.show_progress_bar, self.Par_.show_only_entry_nodes, self.Par_.use_pattern_gen,
                                     self.Par_.use_dmsa_files, self.Par_.set_node_list, self.Par_.entry_nodes_list,
                                     self.Par_.build_nodes_list, self.Par_.activate_timesliceforwarding, 
                                     self.Par_.write_data_to_file, self.Par_.analyze_data, self.Par_.port, self.Par_.use_infiniband, 
                                     self.Par_.use_collectl)
        '''
        self.execution_cls = cm.execution(self.Par_)
        Logfile.logfile.transport_method = self.Par_.transport_method
        Logfile.logfile.infiniband_used = self.Par_.use_infiniband
        self.start_time = time.time()
        
        self.execution_cls.start_Flesnet()

        self.execution_cls.stop_via_ctrl_c()
        if self.Par_.show_total_data:
            total_data, avg_data_rate = self.execution_cls.stop_monitoring()
        else:
            total_data, avg_data_rate = 0,0
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
        total_data, avg_data_rate = self.execution_cls.stop_program()
        self.running = False
        self.end_time = time.time()
        Logfile.logfile.exec_time = self.end_time - self.start_time
        Logfile.logfile.avg_data_rate = avg_data_rate
        self.create_end_message(total_data,avg_data_rate)
        Logfile.logfile.write()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        sys.exit(1)
        
    def clean_files(self):
        with open("tmp/central_manager.txt", "w") as f:
            f.truncate(0)
            f.close()
        with open("tmp/nodes_response.txt", "w") as f:
            f.truncate(0)
            f.close()
        with open("tmp/build_nodes_params.txt", "w") as f:
            f.truncate(0)
            f.close()
        with open("tmp/entry_nodes_params.txt", "w") as f:
            f.truncate(0)
            f.close()
        with open("tmp/super_nodes_params.txt", "w") as f:
            f.truncate(0)
            f.close()
        with open("tmp/receiving_nodes_params.txt", "w") as f:
            f.truncate(0)
            f.close()
    
    def create_logfile(self):
        Logfile.logfile.write()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
            
    def create_end_message(self,total_data, avg_data_rate):
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
        