#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 25 13:43:40 2025

@author: jschlieffen
"""
import matplotlib.pyplot as plt
import seaborn as sns
import Logfile_reader as LR
import os
from datetime import datetime
from dateutil import parser
import numpy as np

class create_plots_entry_nodes:
    
    def __init__(self,data_rates,shm_usages, time_start = "00:00:00" , time_end = "00:00:00" ):
        self.time_stmps = []
        self.time_stmps_shm_usage = []
        self.data_rates = data_rates
        self.shm_usages = shm_usages
        
        if time_start != "00:00:00":
            time_start_dt = parser.parse(time_start)
            time_end_dt = parser.parse(time_end)
            self.get_time_stmps(time_start_dt,time_end_dt)
        else:
            self.get_time_stmps()
        
    
    def get_time_stmps_v2(self):
        largest_key = max(self.data_rates, key=lambda k: len(self.data_rates[k]))
        largest_dict = self.data_rates[largest_key]
        self.time_stmps = [key for key in largest_dict.keys()]
        largest_key = max(self.shm_usages, key=lambda k: len(self.shm_usages[k]))
        largest_dict = self.shm_usages[largest_key]
        self.time_stmps_shm_usage = [key for key in largest_dict.keys()]
    
    def get_time_stmps_v3(self):
        all_timestamps = set()
        for inner_dict in self.data_rates.values():
            all_timestamps.update(inner_dict.keys())
        self.time_stmps = sorted(all_timestamps)
        all_timestamps = set()

        for inner_dict in self.shm_usages.values():
            all_timestamps.update(inner_dict.keys())
        self.time_stmps_shm_usage = sorted(all_timestamps)
        
        
    def get_time_stmps(self, start_time=None, end_time=None):
        def in_interval(ts):
            return (start_time is None or ts.time() >= start_time.time()) and (end_time is None or ts.time() <= end_time.time())
        all_timestamps = set()
        for inner_dict in self.data_rates.values():
            all_timestamps.update(ts for ts in inner_dict.keys() if in_interval(ts))
        self.time_stmps = sorted(all_timestamps)
        all_timestamps = set()
        for inner_dict in self.shm_usages.values():
            all_timestamps.update(ts for ts in inner_dict.keys() if in_interval(ts))
        self.time_stmps_shm_usage = sorted(all_timestamps)
            
    
    def plot_total_data_rate(self):
        print(os.getcwd())
        dir = os.getcwd()
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
        plt.plot(self.time_stmps, total_data_rate,  linestyle='-', color='b')
        plt.xlabel("Timestamp")
        plt.ylabel("Data rate in GB")
        plt.title("Total data rate")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(path + 'total_data_rate.png')
        plt.close()
        
    def plot_avg_data_rate(self):
        dir = os.getcwd()
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
        plt.plot(self.time_stmps, avg_data_rate,  linestyle='-', color='b')
        plt.xlabel("Timestamp")
        plt.ylabel("Data rate in GB")
        plt.title("Average data rate")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(path + 'avg_data_rate.png')
        plt.close()
    
    def plot_data_rate_mean_max_min(self):
        dir = os.getcwd()
        path = os.path.join(dir,'plots/general/entry_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        num_nodes = len(self.data_rates)
        avg_data_rate = []
        max_rate = []
        min_rate = []
        for time_stmp in self.time_stmps:
            avg_data_rate_tmp = 0
            time_stmp_max = 0
            time_stmp_min = 10000000
            for val in self.data_rates.values():
                if time_stmp in val:
                    avg_data_rate_tmp += val[time_stmp]
                    if time_stmp_max < val[time_stmp]:
                        time_stmp_max = val[time_stmp]
                    if time_stmp_min > val[time_stmp]:
                        time_stmp_min = val[time_stmp]
            avg_data_rate.append(avg_data_rate_tmp/num_nodes) 
            max_rate.append(time_stmp_max)
            min_rate.append(time_stmp_min)
            
            
        plt.figure(figsize=(10, 6))
        plt.fill_between(self.time_stmps, min_rate, max_rate, color='lightgrey', label='Range (min data rate-max data rate)')
        plt.plot(self.time_stmps, max_rate, color='black', linestyle='--', linewidth=1, label='Max rate')
        plt.plot(self.time_stmps, min_rate, color='black', linestyle='--', linewidth=1, label='Min rate')
        plt.plot(self.time_stmps, avg_data_rate, linestyle='-', color='k')
        plt.xlabel("Timestamp")
        plt.ylabel("Data rate in GB")
        plt.title("Average data rate with maximum and minium")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(path + 'avg_data_rate_max_min.png')
        plt.close()
        

    def box_plot_data_rates(self):
        dir = os.getcwd()
        path = os.path.join(dir, 'plots/general/entry_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
    
        # Remove outliers using IQR method
        filtered_data = []
        for entry_node_values in self.data_rates.values():
            values = np.array(list(entry_node_values.values()))
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            filtered_values = values[(values >= lower_bound) & (values <= upper_bound)]
            filtered_data.append(filtered_values.tolist())
    
        labels = list(self.data_rates.keys())
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=filtered_data)
        plt.xticks(range(len(labels)), labels, rotation=45)
        plt.title("Boxplot of the data rate for entry nodes (Outliers Removed)")
        plt.xlabel("Entry Nodes")
        plt.ylabel("Data Rate in GB")
        plt.tight_layout()
        plt.xticks(rotation=45)
        plt.savefig(path + 'box_plot_data_rate_entry_nodes.png')
        plt.close()
        
    def bar_plots_data_rates(self):
        dir = os.getcwd()
        path = os.path.join(dir, 'plots/general/entry_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        averages = []
        for entry_node in self.data_rates.values():
            avg_entry_node = 0
            cnt = 0
            for time_stmp in self.time_stmps:
                if time_stmp in entry_node:
                    avg_entry_node += entry_node[time_stmp]
                    cnt += 1
                else:
                    avg_entry_node += 0
                    cnt += 1
            if cnt != 0:
                averages.append(avg_entry_node/cnt)
            else:
                averages.append(avg_entry_node)
        
        labels = list(self.data_rates.keys())
        cmap = plt.get_cmap('viridis')
        colors = [cmap(i / len(labels)) for i in range(len(labels))]
        plt.figure(figsize=(12, 6))
        plt.bar(labels,averages,color=colors)
        plt.title('Bar Plot of data rates')
        plt.ylabel('Data Rate in GB')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(path + 'bar_plot_data_rate_entry_nodes.png')
        plt.close()

    
    def box_plot_data_rates_v2(self):
        dir = os.getcwd()
        path = os.path.join(dir,'plots/general/entry_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        data = [list(entry_node_values.values()) for entry_node_values in self.data_rates.values()]
        labels = list(self.data_rates.keys())
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=data)
        plt.xticks(range(len(labels)), labels, rotation=45) 
        plt.title("Boxplot of the data rate for entry nodes")
        plt.xlabel("entry nodes")
        plt.ylabel("Data rate in GB")
        plt.tight_layout()
        plt.savefig(path + 'box_plot_data_rate_entry_nodes.png')
        plt.close()
        
    def plot_data_rate_single(self):
        dir = os.getcwd()
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
            plt.plot(self.time_stmps, total_data_rate, linestyle='-', color='b')
            plt.xlabel("Timestamp")
            plt.ylabel("Data rate in GB")
            plt.title(f"data rate for node {key}")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(path + f'data_rate_{key}.png')
            plt.close()
    

    
    def plot_shm_usage(self):
        dir = os.getcwd()
        path = os.path.join(dir,'plots/general/entry_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        num_nodes = len(self.data_rates)
        used = []
        sending = []
        freeing = []
        free = []
        for time_stmp in self.time_stmps_shm_usage:
            used_avg = 0
            sending_avg = 0
            freeing_avg = 0
            free_avg = 0
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
        plt.plot(self.time_stmps_shm_usage, used,  linestyle='-', color='red', label='used')
        plt.plot(self.time_stmps_shm_usage, sending,  linestyle='-', color='green', label='sending')
        plt.plot(self.time_stmps_shm_usage, freeing,  linestyle='-', color='orange', label='freeing')
        plt.plot(self.time_stmps_shm_usage, free,  linestyle='-', color='purple', label='free')
        plt.ylim(0,100)
        plt.xlabel("Timestamp")
        plt.ylabel("Shm usage in %")
        plt.title("Average Shm usage")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.legend()
        plt.savefig(path + 'shm_usage_avg.png')        
        plt.close()


    def plot_shm_usage_single(self):
        dir = os.getcwd()
        path = os.path.join(dir,'plots/nodes/entry_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        for key, shm_dict in self.shm_usages.items():
            used = []
            sending = []
            freeing = []
            free = []
            for time_stmp in self.time_stmps_shm_usage:
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
            plt.plot(self.time_stmps_shm_usage, used,  linestyle='-', color='red', label='used')
            plt.plot(self.time_stmps_shm_usage, sending,  linestyle='-', color='green', label='sending')
            plt.plot(self.time_stmps_shm_usage, freeing,  linestyle='-', color='orange', label='freeing')
            plt.plot(self.time_stmps_shm_usage, free,  linestyle='-', color='purple', label='free')
            plt.ylim(0,100)
            plt.xlabel("Timestamp")
            plt.ylabel("Shm usage in %")
            plt.title(f"Shm usage for node {key}")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            plt.legend()
            plt.savefig(path + f'shm_usage_{key}.png') 
            plt.close()


class create_plots_build_nodes:
     
     def __init__(self,data_rates,shm_usages, time_start = "00:00:00" , time_end = "00:00:00"):
         self.time_stmps = []
         self.time_stmps_shm_usage = []
         self.data_rates = data_rates
         self.shm_usages = shm_usages
         if time_start != "00:00:00":
             time_start_dt = parser.parse(time_start)
             time_end_dt = parser.parse(time_end)
             self.get_time_stmps(time_start_dt,time_end_dt)
         else:
             self.get_time_stmps()
         
     
     def get_time_stmps_v2(self):
         largest_key = max(self.data_rates, key=lambda k: len(self.data_rates[k]))
         largest_dict = self.data_rates[largest_key]
         self.time_stmps = [key for key in largest_dict.keys()]
         max_len = 0
         timestamps = []
         for outer_dict in self.shm_usages.values():
             for inner_dict in outer_dict.values():
                 if len(inner_dict) > max_len:
                     max_len = len(inner_dict)
                     self.time_stmps_shm_usage = list(inner_dict.keys())
                     
     def get_time_stmps_v3(self):
        all_timestamps = set()
        for inner_dict in self.data_rates.values():
            all_timestamps.update(inner_dict.keys())
        self.time_stmps = sorted(all_timestamps)
        all_timestamps = set()
        for outer_dict in self.shm_usages.values():
            for inner_dict in outer_dict.values():
                all_timestamps.update(inner_dict.keys())
        
        self.time_stmps_shm_usage = sorted(all_timestamps)
     
        
     def get_time_stmps(self, start_time=None, end_time=None):
         def in_interval(ts):
             return (start_time is None or ts.time() >= start_time.time()) and (end_time is None or ts.time() <= end_time.time())
         all_timestamps = set()
         for inner_dict in self.data_rates.values():
             all_timestamps.update(ts for ts in inner_dict.keys() if in_interval(ts))
         self.time_stmps = sorted(all_timestamps)
         all_timestamps = set()
         for outer_dict in self.shm_usages.values():
             for inner_dict in outer_dict.values():
                 all_timestamps.update(ts for ts in inner_dict.keys() if in_interval(ts))
         self.time_stmps_shm_usage = sorted(all_timestamps)
        
     def plot_total_data_rate(self):
         dir = os.getcwd()
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
         plt.plot(self.time_stmps, total_data_rate,  linestyle='-', color='b')
         plt.xlabel("Timestamp")
         plt.ylabel("Data rate in GB")
         plt.title("Total data rate")
         plt.xticks(rotation=45)
         plt.grid(True)
         plt.tight_layout()
         plt.savefig(path + 'total_data_rate.png')
         plt.close()
         
     def plot_avg_data_rate(self):
         dir = os.getcwd()
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
         plt.plot(self.time_stmps, avg_data_rate,  linestyle='-', color='b')
         plt.xlabel("Timestamp")
         plt.ylabel("Data rate in GB")
         plt.title("Average data rate")
         plt.xticks(rotation=45)
         plt.grid(True)
         plt.tight_layout()
         plt.savefig(path + 'avg_data_rate.png')
         plt.close()
         
     def box_plot_data_rates(self):
        dir = os.getcwd()
        path = os.path.join(dir, 'plots/general/build_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        filtered_data = []
        for entry_node_values in self.data_rates.values():
            values = np.array(list(entry_node_values.values()))
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            filtered_values = values[(values >= lower_bound) & (values <= upper_bound)]
            filtered_data.append(filtered_values.tolist())
    
        labels = list(self.data_rates.keys())
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=filtered_data)
        plt.xticks(range(len(labels)), labels, rotation=45)
        plt.title("Boxplot of the data rate for build nodes (Outliers Removed)")
        plt.xlabel("Build Nodes")
        plt.ylabel("Data Rate in GB")
        plt.tight_layout()
        plt.xticks(rotation=45)
        plt.savefig(path + 'box_plot_data_rate_build_nodes.png')
        plt.close()
         
     def box_plot_data_rates_v2(self):
        dir = os.getcwd()
        path = os.path.join(dir,'plots/general/build_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        data = [list(entry_node_values.values()) for entry_node_values in self.data_rates.values()]
        labels = list(self.data_rates.keys())
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=data)
        plt.xticks(range(len(labels)), labels, rotation=45)
        plt.title("Boxplot of the data rate for build nodes")
        plt.xlabel("entry nodes")
        plt.ylabel("Data rate in GB")
        plt.tight_layout()
        plt.savefig(path + 'box_plot_data_rate_build_nodes.png')
        plt.close()
        
     def plot_data_rate_mean_max_min(self):
        dir = os.getcwd()
        path = os.path.join(dir,'plots/general/build_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        num_nodes = len(self.data_rates)
        avg_data_rate = []
        max_rate = []
        min_rate = []
        for time_stmp in self.time_stmps:
            avg_data_rate_tmp = 0
            time_stmp_max = 0
            time_stmp_min = 10000000
            for val in self.data_rates.values():
                if time_stmp in val:
                    avg_data_rate_tmp += val[time_stmp]
                    if time_stmp_max < val[time_stmp]:
                        time_stmp_max = val[time_stmp]
                    if time_stmp_min > val[time_stmp]:
                        time_stmp_min = val[time_stmp]
            avg_data_rate.append(avg_data_rate_tmp/num_nodes) 
            max_rate.append(time_stmp_max)
            min_rate.append(time_stmp_min)
            
            
        plt.figure(figsize=(10, 6))
        plt.fill_between(self.time_stmps, min_rate, max_rate, color='lightgrey', label='Range (min data rate-max data rate)')
        plt.plot(self.time_stmps, max_rate, color='black', linestyle='--', linewidth=1, label='Max rate')
        plt.plot(self.time_stmps, min_rate, color='black', linestyle='--', linewidth=1, label='Min rate')
        plt.plot(self.time_stmps, avg_data_rate,  linestyle='-', color='k')
        plt.xlabel("Timestamp")
        plt.ylabel("Data rate in GB")
        plt.title("Average data rate with maximum and minium build nodes")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(path + 'avg_data_rate_max_min.png')
        plt.close()
        
     def bar_plots_data_rates(self):
        dir = os.getcwd()
        path = os.path.join(dir, 'plots/general/build_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        averages = []
        for build_node in self.data_rates.values():
            avg_build_node = 0
            cnt = 0
            for time_stmp in self.time_stmps:
                if time_stmp in build_node:
                    avg_build_node += build_node[time_stmp]
                    cnt += 1
                else:
                    avg_build_node += 0
                    cnt += 1
            if cnt != 0:
                averages.append(avg_build_node/cnt)
            else:
                averages.append(avg_build_node)
        
        labels = list(self.data_rates.keys())
        cmap = plt.get_cmap('viridis')
        colors = [cmap(i / len(labels)) for i in range(len(labels))] 
        plt.bar(labels,averages,color=colors)
        plt.title('Bar Plot of data rates')
        plt.ylabel('Data Rate in GB')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(path + 'bar_plot_data_rate_entry_nodes.png')
        plt.close()
        
     def plot_data_rate_single(self):
         dir = os.getcwd()
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
             plt.plot(self.time_stmps, total_data_rate,  linestyle='-', color='b')
             plt.xlabel("Timestamp")
             plt.ylabel("Data rate in GB")
             plt.title(f"data rate for node {key}")
             plt.xticks(rotation=45)
             plt.grid(True)
             plt.tight_layout()
             plt.savefig(path + f'data_rate_{key}.png')
             plt.close()

       
     def plot_shm_usage_assemble(self):
        dir = os.getcwd()
        path = os.path.join(dir,'plots/general/build_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        num_nodes = len(self.data_rates)
        used = []
        freeing = []
        free = []
        for time_stmp in self.time_stmps_shm_usage:
            used_avg = 0
            freeing_avg = 0
            free_avg = 0
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
        plt.plot(self.time_stmps_shm_usage, used,  linestyle='-', color='red', label='used')
        plt.plot(self.time_stmps_shm_usage, freeing,  linestyle='-', color='orange', label='freeing')
        plt.plot(self.time_stmps_shm_usage, free,  linestyle='-', color='purple', label='free')
        plt.ylim(0,100)
        plt.xlabel("Timestamp")
        plt.ylabel("Shm usage in %")
        plt.title("Average Shm usage")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.legend()
        plt.savefig(path + 'shm_usage_avg.png')        
        plt.close()
        
     def plot_shm_usage_single_node_avg(self):
        dir = os.getcwd()
        path = os.path.join(dir,'plots/nodes/build_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        num_nodes = len(self.data_rates)
        for key, entry_node in self.shm_usages.items():
            used = []
            freeing = []
            free = []
            for time_stmp in self.time_stmps_shm_usage:
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
                        break
                used.append(used_avg/num_nodes)
                freeing.append(freeing_avg/num_nodes)
                free.append(free_avg/num_nodes)
            plt.figure(figsize=(10, 6))
            plt.plot(self.time_stmps_shm_usage, used,  linestyle='-', color='red', label='used')
            plt.plot(self.time_stmps_shm_usage, freeing,  linestyle='-', color='orange', label='freeing')
            plt.plot(self.time_stmps_shm_usage, free,  linestyle='-', color='purple', label='free')
            plt.ylim(0,100)
            plt.xlabel("Timestamp")
            plt.ylabel("Shm usage in %")
            plt.title(f"Shm usage for node {key}")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            plt.legend()
            plt.savefig(path + f'shm_usage_{key}.png') 
            plt.close()
            
     def plot_shm_usage_single_node_single_entry_node(self):
        dir = os.getcwd()
        path = os.path.join(dir,'plots/nodes/build_nodes')
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + '/'
        for key_build_node, build_node in self.shm_usages.items():
            for key_entry_node, shm_dict in build_node.items():
                used = []
                freeing = []
                free = []
                for time_stmp in self.time_stmps_shm_usage:
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
                plt.plot(self.time_stmps_shm_usage, used,  linestyle='-', color='red', label='used')
                plt.plot(self.time_stmps_shm_usage, freeing,  linestyle='-', color='orange', label='freeing')
                plt.plot(self.time_stmps_shm_usage, free,  linestyle='-', color='purple', label='free')
                plt.ylim(0,100)
                plt.xlabel("Timestamp")
                plt.ylabel("Shm usage in %")
                plt.title(f"Shm usage for build node {key_build_node} and entry node {key_entry_node}")
                plt.xticks(rotation=45)
                plt.grid(True)
                plt.tight_layout()
                plt.legend()
                plt.savefig(path + f'shm_usage_{key_build_node}_{key_entry_node}.png')     
                plt.close()


    
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
