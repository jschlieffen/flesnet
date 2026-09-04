#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 13 21:22:38 2026

@author: jschlieffen
"""

import sys
sys.path.append('../')
from setup import params as par

class params_interactive:
    
    def __init__(self):
        self.Par_ = par.Params('setup/config_interactive.cfg')
        self.display_params = self.check_display_params()
        self.groups = self.form_groups()
        
    def check_display_params(self):
        display_params = [
            "use_collectl",
            "use_flescluster",
            "activate_timesliceforwarding",
            "ZIB_timesliceforwarding",
            "num_cpus",
            'mem',
            "loglevel",
            "activate_robustness_test",
            "set_node_list",
            "exclude_nodes",
            "path",
            "use_infiniband",
            "desc_size",
            "data_size",
            "num_components",
            "write_data_to_file",
            "use_dtsa_files",
            "analyze_data",
            "port",
            "input_tsa_files",
            "show_total_data",
            "use_grafana"
        ]
        if self.Par_.use_flescluster:
            display_params += ['is_flescluster','cm_ip']
        if self.Par_.activate_timesliceforwarding:
            display_params += ['num_receivers']
            if self.Par_.set_node_list:
                display_params += ['sender_node_list','receiver_node_list']
            if self.Par_.exclude_nodes:
                display_params += ['exclude_sender_nodes','exclude_process_nodes']
            if self.Par_.activate_robustness_test:
                display_params += ['num_min_sender_nodes_alive','num_min_process_nodes_alive']
        elif self.Par_.ZIB_timesliceforwarding:
            if self.Par_.use_flescluster:
                if self.Par_.is_flescluster:
                    display_params += ['num_input_nodes']
                else:
                    display_params += ['num_central_manager','num_output_nodes']
            else:
                display_params += ['num_central_manager','num_input_nodes','num_output_nodes']
            if self.Par_.set_node_list:
                if self.Par_.use_flescluster:
                    if self.Par_.is_flescluster:
                        display_params += ['input_node_list']
                    else:
                        display_params += ['central_manager_list','output_node_list']
                else:
                    display_params +=  ['central_manager_list','output_node_list','input_node_list']
            if self.Par_.exclude_nodes:
                if self.Par_.use_flescluster:
                    if self.Par_.is_flescluster:
                        display_params += ['exclude_input_nodes']
                    else:
                        display_params += ['exclude_central_manager_nodes','exclude_output_nodes']
                else:
                    display_params += ['exclude_central_manager','exclude_output_nodes', 'exclude_input_nodes']
            if self.Par_.activate_robustness_test:
                if self.Par_.use_flescluster:
                    if self.Par_.is_flescluster:
                        display_params += ['num_min_input_nodes_alive']
                    else:
                        display_params += ['num_min_central_manager_alive','num_min_output_nodes_alive']
                else:
                    display_params += ['num_min_central_manager_alive','num_min_input_nodes_alive','num_min_output_nodes_alive']     
            if self.Par_.write_data_to_file:
                display_params += ['path_to_output_file']
            if self.Par_.use_dtsa_files:
                display_params += ['malloc_size']
            if self.Par_.show_total_data:
                display_params += ['show_graph','show_progress_bar']
            if self.Par_.use_grafana:
                display_params += ['influx_node_ip','token']
        return display_params
    
    def form_groups(self):
        groups = {}
    
        groups['Number_of_Nodes'] = [
            'num_receivers',
            'num_central_manager',
            'num_input_nodes',
            'num_output_nodes',
        ]
    
        groups['set_node_list'] = [
            'set_node_list',
            'exclude_nodes',
            'sender_node_list',
            'receiver_node_list',
            'central_manager_list',
            'output_node_list',
            'input_node_list',
            'exclude_sender_nodes',
            'exclude_process_nodes',
            'exclude_central_manager_nodes',
            'exclude_input_nodes',
            'exclude_output_nodes',
        ]
    
        groups['mode'] = [
            'activate_timesliceforwarding',
            'ZIB_timesliceforwarding',
            'use_flescluster',
            'is_flescluster',
            'cm_ip',
        ]
    
        groups['general'] = [
            'num_cpus',
            'loglevel',
            'mem',
            'use_collectl',
        ]
    
        groups['robustness_test'] = [
            'activate_robustness_test',
            'num_min_sender_nodes_alive',
            'num_min_process_nodes_alive',
            'num_min_input_nodes_alive',
            'num_min_central_manager_alive',
            'num_min_output_nodes_alive',
        ]
    
        groups['flesnet_commands'] = [
            'path',
            'use_infiniband',
        ]
    
        groups['shm_commands'] = [
            'desc_size',
            'data_size',
            'num_components',
        ]
    
        groups['tsclient_commands'] = [
            'write_data_to_file',
            'path_to_output_file',
            'use_dtsa_files',
            'analyze_data',
            'port',
            'malloc_size',
        ]
    
        groups['ts_input_files'] = [
            'input_tsa_files',
        ]
    
        groups['Monotoring'] = [
            'show_total_data',
            'enable_graph',
            'enable_progress_bar',
        ]
    
        groups['influxdb'] = [
            'use_grafana',
            'influx_node_ip',
            'token',
        ]
    
        return groups
    
    
    def change_param(self,section,param,value):
        self.Par_.config[section][param] = str(value)
        with open('setup/config_interactive.cfg','w') as f:
            self.Par_.config.write(f)
        self.Par_ = par.Params('setup/config_interactive.cfg')
        self.display_params = self.check_display_params()
        self.groups = self.form_groups()
        
    def get_param_section(self, param):
        for section in self.Par_.config.sections():
            if self.Par_.config.has_option(
                section,
                param
            ):
                return section
        return None
                        
        
    def get_param_value(self, param):
        return getattr(
            self.Par_,
            param
        )
