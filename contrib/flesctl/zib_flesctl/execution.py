#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:28:18 2025

@author: jschlieffen
"""

import params as par
import central_manager as cm
import time

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

    def start_sim(self):
        execution_cls = cm.execution(self.Par_.input_file_list, self.Par_.entry_nodes, self.Par_.build_nodes, 
                                     self.Par_.show_total_data, self.Par_.influx_node_ip, self.Par_.influx_token,
                                     self.Par_.use_grafana, self.Par_.overlap_usage_of_nodes, self.Par_.path, 
                                     self.Par_.transport_method, self.Par_.customize_string, self.Par_.show_graph,
                                     self.Par_.show_progress_bar, self.Par_.show_only_entry_nodes)
        start_time = time.time()
        execution_cls.start_Flesnet()
        execution_cls.stop_via_ctrl_c()
        end_time = time.time()
        
        elapsed_seconds = end_time - start_time
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"The simulation ran for {int(hours):02d}H:{int(minutes):02d}M:{int(seconds):02d}S"
        print(formatted_time)
        
        
def main():
    exe = exec_()
    exe.start_sim()

if __name__ == '__main__':
    main()
        