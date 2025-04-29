#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 25 13:43:40 2025

@author: jschlieffen
"""
import matplotlib.pyplot as plt
import Logfile_reader as LR
import os

class create_plots_entry_nodes:
    
    def __init__(self,data_rates,shm_usages):
        self.time_stmps = []
        self.data_rates = data_rates
        self.shm_usages = shm_usages
        self.get_time_stmps()
        
    
    def get_time_stmps(self):
        largest_key = max(self.data_rates, key=lambda k: len(self.data_rates[k]))
        largest_dict = self.data_rates[largest_key]
        self.time_stmps = [key for key in largest_dict.keys()]
    
    def plot_total_data_rate(self):
        #print('test')
        dir = os.path.dirname(__file__)
        path = os.path.join(dir,'plots/general/entry_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        total_data_rate = []
        for time_stmp in self.time_stmps:
            total_data_rate_tmp = 0
            for val in self.data_rates.values():
                if time_stmp in val:
                    total_data_rate_tmp += val[time_stmp]
            total_data_rate.append(total_data_rate_tmp)   
        plt.figure(figsize=(10, 6))
        plt.plot(self.time_stmps, total_data_rate, marker='o', linestyle='-', color='b')
        plt.xlabel("Timestamp")
        plt.ylabel("Data rate in GB")
        plt.title("Total data rate")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        #plt.show()
        plt.savefig(path + 'total_data_rate.png')
        
    def plot_avg_data_rate(self):
        dir = os.path.dirname(__file__)
        path = os.path.join(dir,'plots/general/entry_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        num_nodes = len(self.data_rates)
        avg_data_rate = []
        for time_stmp in self.time_stmps:
            avg_data_rate_tmp = 0
            for val in self.data_rates.values():
                if time_stmp in val:
                    avg_data_rate_tmp += val[time_stmp]
            avg_data_rate.append(avg_data_rate_tmp/num_nodes)   
        plt.figure(figsize=(10, 6))
        plt.plot(self.time_stmps, avg_data_rate, marker='o', linestyle='-', color='b')
        plt.xlabel("Timestamp")
        plt.ylabel("Data rate in GB")
        plt.title("Average data rate")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        #plt.show()
        plt.savefig(path + 'avg_data_rate.png')
        
    def plot_data_rate_single(self):
        dir = os.path.dirname(__file__)
        path = os.path.join(dir,'plots/nodes/entry_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        for key,val in self.data_rates.items():
            total_data_rate = []
            for time_stmp in self.time_stmps:
                if time_stmp in val:
                    total_data_rate.append(val[time_stmp])   
                else:
                    total_data_rate.append(0)
            plt.figure(figsize=(10, 6))
            plt.plot(self.time_stmps, total_data_rate, marker='o', linestyle='-', color='b')
            plt.xlabel("Timestamp")
            plt.ylabel("Data rate in GB")
            plt.title(f"data rate for node {key}")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            #plt.show()
            plt.savefig(path + f'data_rate_{key}.png')
    
    
    def plot_shm_usage(self):
        dir = os.path.dirname(__file__)
        path = os.path.join(dir,'plots/general/entry_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        num_nodes = len(self.data_rates)
        used = []
        sending = []
        freeing = []
        free = []
        for time_stmp in self.time_stmps:
            used_avg = 0
            sending_avg = 0
            freeing_avg = 0
            free_avg = 0
            #print(self.shm_usages)
            for shm_dict in self.shm_usages.values():
                if time_stmp in shm_dict:
                    val = shm_dict[time_stmp]
                    used_avg += val['used']
                    sending_avg += val['sending']
                    freeing_avg += val['freeing']
                    free_avg += val['free']
            used.append(used_avg/num_nodes)
            sending.append(sending_avg/num_nodes)
            freeing.append(freeing_avg/num_nodes)
            free.append(free_avg/num_nodes)
        plt.figure(figsize=(10, 6))
        plt.plot(self.time_stmps, used, marker='o', linestyle='-', color='red', label='used')
        plt.plot(self.time_stmps, sending, marker='o', linestyle='-', color='green', label='sending')
        plt.plot(self.time_stmps, freeing, marker='o', linestyle='-', color='orange', label='freeing')
        plt.plot(self.time_stmps, free, marker='o', linestyle='-', color='purple', label='free')
        plt.xlabel("Timestamp")
        plt.ylabel("Shm usage in %")
        plt.title("Average Shm usage")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        #plt.show()
        plt.legend()
        plt.savefig(path + 'shm_usage_avg.png')        


    def plot_shm_usage_single(self):
        dir = os.path.dirname(__file__)
        path = os.path.join(dir,'plots/nodes/entry_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        for key, shm_dict in self.shm_usages.items():
            used = []
            sending = []
            freeing = []
            free = []
            for time_stmp in self.time_stmps:
                if time_stmp in shm_dict:
                    val = shm_dict[time_stmp]
                    used.append(val['used'])
                    sending.append(val['sending'])
                    freeing.append(val['freeing'])
                    free.append(val['free'])
                else:
                    used.append(0)
                    sending.append(0)
                    freeing.append(0)
                    free.append(0)
            plt.figure(figsize=(10, 6))
            plt.plot(self.time_stmps, used, marker='o', linestyle='-', color='red', label='used')
            plt.plot(self.time_stmps, sending, marker='o', linestyle='-', color='green', label='sending')
            plt.plot(self.time_stmps, freeing, marker='o', linestyle='-', color='orange', label='freeing')
            plt.plot(self.time_stmps, free, marker='o', linestyle='-', color='purple', label='free')
            plt.xlabel("Timestamp")
            plt.ylabel("Shm usage in %")
            plt.title(f"Shm usage for node {key}")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            #plt.show()
            plt.legend()
            plt.savefig(path + f'shm_usage_{key}.png') 
            


class create_plots_build_nodes:
     
     def __init__(self,data_rates,shm_usages):
         self.time_stmps = []
         self.data_rates = data_rates
         self.shm_usages = shm_usages
         self.get_time_stmps()
         
     
     def get_time_stmps(self):
         largest_key = max(self.data_rates, key=lambda k: len(self.data_rates[k]))
         largest_dict = self.data_rates[largest_key]
         self.time_stmps = [key for key in largest_dict.keys()]
     
     def plot_total_data_rate(self):
         #print('test')
         dir = os.path.dirname(__file__)
         path = os.path.join(dir,'plots/general/build_nodes')
         if not os.path.exists(path):
             os.makedirs(path)
         path = path + '/'
         total_data_rate = []
         for time_stmp in self.time_stmps:
             total_data_rate_tmp = 0
             for val in self.data_rates.values():
                 if time_stmp in val:
                     total_data_rate_tmp += val[time_stmp]
             total_data_rate.append(total_data_rate_tmp)   
         plt.figure(figsize=(10, 6))
         plt.plot(self.time_stmps, total_data_rate, marker='o', linestyle='-', color='b')
         plt.xlabel("Timestamp")
         plt.ylabel("Data rate in GB")
         plt.title("Total data rate")
         plt.xticks(rotation=45)
         plt.grid(True)
         plt.tight_layout()
         #plt.show()
         plt.savefig(path + 'total_data_rate.png')
         
     def plot_avg_data_rate(self):
         dir = os.path.dirname(__file__)
         path = os.path.join(dir,'plots/general/build_nodes')
         if not os.path.exists(path):
             os.makedirs(path)
         path = path + '/'
         num_nodes = len(self.data_rates)
         avg_data_rate = []
         for time_stmp in self.time_stmps:
             avg_data_rate_tmp = 0
             for val in self.data_rates.values():
                 if time_stmp in val:
                     avg_data_rate_tmp += val[time_stmp]
             avg_data_rate.append(avg_data_rate_tmp/num_nodes)   
         plt.figure(figsize=(10, 6))
         plt.plot(self.time_stmps, avg_data_rate, marker='o', linestyle='-', color='b')
         plt.xlabel("Timestamp")
         plt.ylabel("Data rate in GB")
         plt.title("Average data rate")
         plt.xticks(rotation=45)
         plt.grid(True)
         plt.tight_layout()
         #plt.show()
         plt.savefig(path + 'avg_data_rate.png')
         
     def plot_data_rate_single(self):
         dir = os.path.dirname(__file__)
         path = os.path.join(dir,'plots/nodes/build_nodes')
         if not os.path.exists(path):
             os.makedirs(path)
         path = path + '/'
         for key,val in self.data_rates.items():
             total_data_rate = []
             for time_stmp in self.time_stmps:
                 if time_stmp in val:
                     total_data_rate.append(val[time_stmp])   
                 else:
                     total_data_rate.append(0)
             plt.figure(figsize=(10, 6))
             plt.plot(self.time_stmps, total_data_rate, marker='o', linestyle='-', color='b')
             plt.xlabel("Timestamp")
             plt.ylabel("Data rate in GB")
             plt.title(f"data rate for node {key}")
             plt.xticks(rotation=45)
             plt.grid(True)
             plt.tight_layout()
             #plt.show()
             plt.savefig(path + f'data_rate_{key}.png')

       
     def plot_shm_usage_assemble(self):
        dir = os.path.dirname(__file__)
        path = os.path.join(dir,'plots/general/build_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        num_nodes = len(self.data_rates)
        used = []
        freeing = []
        free = []
        for time_stmp in self.time_stmps:
            used_avg = 0
            freeing_avg = 0
            free_avg = 0
            #print(self.shm_usages)
            for build_node in self.shm_usages.values():
                for shm_dict in build_node.values():
                    if time_stmp in shm_dict:
                        val = shm_dict[time_stmp]
                        used_avg += val['used']
                        freeing_avg += val['freeing']
                        free_avg += val['free']
            used.append(used_avg/num_nodes)
            freeing.append(freeing_avg/num_nodes)
            free.append(free_avg/num_nodes)
        plt.figure(figsize=(10, 6))
        plt.plot(self.time_stmps, used, marker='o', linestyle='-', color='red', label='used')
        plt.plot(self.time_stmps, freeing, marker='o', linestyle='-', color='orange', label='freeing')
        plt.plot(self.time_stmps, free, marker='o', linestyle='-', color='purple', label='free')
        plt.xlabel("Timestamp")
        plt.ylabel("Shm usage in %")
        plt.title("Average Shm usage")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        #plt.show()
        plt.legend()
        plt.savefig(path + 'shm_usage_avg.png')        
        
     def plot_shm_usage_single_node_avg(self):
        dir = os.path.dirname(__file__)
        path = os.path.join(dir,'plots/nodes/build_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        num_nodes = len(self.data_rates)
        for key, entry_node in self.shm_usages.items():
            used = []
            freeing = []
            free = []
            for time_stmp in self.time_stmps:
                for shm_dict in entry_node.values():
                    used_avg = 0
                    freeing_avg = 0
                    free_avg = 0
                    if time_stmp in shm_dict:
                        val = shm_dict[time_stmp]
                        used_avg += val['used']
                        freeing_avg += val['freeing']
                        free_avg += val['free']
                    else:
                        used.append(0)
                        freeing.append(0)
                        free.append(0)
                        break
                used.append(used_avg/num_nodes)
                freeing.append(freeing_avg/num_nodes)
                free.append(free_avg/num_nodes)
            plt.figure(figsize=(10, 6))
            plt.plot(self.time_stmps, used, marker='o', linestyle='-', color='red', label='used')
            plt.plot(self.time_stmps, freeing, marker='o', linestyle='-', color='orange', label='freeing')
            plt.plot(self.time_stmps, free, marker='o', linestyle='-', color='purple', label='free')
            plt.xlabel("Timestamp")
            plt.ylabel("Shm usage in %")
            plt.title(f"Shm usage for node {key}")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            #plt.show()
            plt.legend()
            plt.savefig(path + f'shm_usage_{key}.png') 
            
     def plot_shm_usage_single_node_single_entry_node(self):
        dir = os.path.dirname(__file__)
        path = os.path.join(dir,'plots/nodes/build_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        for key_build_node, build_node in self.shm_usages.items():
            for key_entry_node, shm_dict in build_node.items():
                used = []
                freeing = []
                free = []
                for time_stmp in self.time_stmps:
                    if time_stmp in shm_dict:
                        val = shm_dict[time_stmp]
                        used.append(val['used'])
                        freeing.append(val['freeing'])
                        free.append(val['free'])
                    else:
                        used.append(0)
                        freeing.append(0)
                        free.append(0)
                plt.figure(figsize=(10, 6))
                plt.plot(self.time_stmps, used, marker='o', linestyle='-', color='red', label='used')
                plt.plot(self.time_stmps, freeing, marker='o', linestyle='-', color='orange', label='freeing')
                plt.plot(self.time_stmps, free, marker='o', linestyle='-', color='purple', label='free')
                plt.xlabel("Timestamp")
                plt.ylabel("Shm usage in %")
                plt.title(f"Shm usage for build node {key_build_node} and entry node {key_entry_node}")
                plt.xticks(rotation=45)
                plt.grid(True)
                plt.tight_layout()
                #plt.show()
                plt.legend()
                plt.savefig(path + f'shm_usage_{key_build_node}_{key_entry_node}.png')             


    
def main():
    Logfile_reader_cls_e1 = LR.Logfile_reader("../logs/flesnet/entry_nodes/entry_node_htc-cmp505.log", "entry_node")
    Logfile_reader_cls_e2 = LR.Logfile_reader("../logs/flesnet/entry_nodes/entry_node_htc-cmp506.log", "entry_node")
    data_rates = {
            'entry node 505' : Logfile_reader_cls_e1.data_rate,
            'entry node 506' : Logfile_reader_cls_e2.data_rate
        }
    shm_usages = {
            'entry node 505' : Logfile_reader_cls_e1.data_shms,
            'entry node 506' : Logfile_reader_cls_e2.data_shms,
        }
    cp_cls = create_plots_entry_nodes(data_rates, shm_usages)
    cp_cls.plot_total_data_rate()
    cp_cls.plot_avg_data_rate()
    cp_cls.plot_data_rate_single()
    cp_cls.plot_shm_usage()
    cp_cls.plot_shm_usage_single()

    
    
if __name__ == '__main__':
    main()
