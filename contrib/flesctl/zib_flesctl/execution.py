#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:28:18 2025

@author: jschlieffen
"""

import params as par
import central_manager as cm


# =============================================================================
# TODOs: 1. make a possibility to disable grafana done
#        2. improve monotoring
#        3. search for env- variables that may overwrite the config variables
#           done except input file list done
#        4. comment code 
#        5. write documentation for the code. 
#        6. make a fitting implementation for the use of sbatch
#        7. make zeromq implementation. (big problem I guess? different log files)
#        8. make implementation for libfabric (get libabric run first) 
#           (maybe to complicated at first do this when I have the time to.)
# =============================================================================
class exec_:
    
    def __init__(self):
        self.Par_ = par.Params('config.cfg')

    def start_sim(self):
        execution_cls = cm.execution(self.Par_.input_file_list, self.Par_.entry_nodes, self.Par_.build_nodes, 
                                     self.Par_.show_total_data, self.Par_.influx_node_ip, self.Par_.influx_token,
                                     self.Par_.use_grafana, self.Par_.overlap_usage_of_nodes)
        execution_cls.start_Flesnet()
        execution_cls.stop_via_ctrl_c()
        
def main():
    exe = exec_()
    exe.start_sim()

if __name__ == '__main__':
    main()
        