#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:28:18 2025

@author: jschlieffen
"""

import params as par
import central_manager as cm

class exec_:
    
    def __init__(self):
        self.Par_ = par.Params('config.cfg')
        #self.start_sim()

    def start_sim(self):
        print(self.Par_.input_file_list)
        execution_cls = cm.execution(self.Par_.input_file_list, self.Par_.entry_nodes, self.Par_.build_nodes, self.Par_.show_total_data)
        execution_cls.start_Flesnet()
        execution_cls.stop_via_ctrl_c()
        
def main():
    exe = exec_()
    exe.start_sim()

if __name__ == '__main__':
    main()
        