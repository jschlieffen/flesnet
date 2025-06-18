#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  6 13:56:06 2025

@author: jschlieffen
"""

import matplotlib.pyplot as plt
import seaborn as sns
import Logfile_reader as LR
import os
from datetime import datetime
from dateutil import parser
import numpy as np


class create_plots_collectl:
    
    def __init__(self,data_rates, cpu_usage, timeslice_forwarding_activated, time_start = "00:00:00" , time_end = "00:00:00" ):
        self.time_stmps = {}
        self.time_stmps_cpu_usage = {}
        self.data_rates = data_rates
        self.cpu_usage = cpu_usage
        self.timeslice_forwarding_activated = timeslice_forwarding_activated
        if time_start != "00:00:00":
            time_start_dt = parser.parse(time_start)
            time_end_dt = parser.parse(time_end)
            self.set_time_stmps_for_node_types(time_start_dt,time_end_dt)
        else:
            self.set_time_stmps_for_node_types()        
            

    def get_time_stmps(self, data_rates, cpu_usage, start_time, end_time):
        def in_interval(ts):
            return (start_time is None or ts.time() >= start_time.time()) and (end_time is None or ts.time() <= end_time.time())
        all_timestamps = set()
        for inner_dict in data_rates.values(): #maybe some things need to be updated
            all_timestamps.update(ts for ts in inner_dict.keys() if in_interval(ts))
        time_stmps = sorted(all_timestamps)
        all_timestamps = set()
        for inner_dict in cpu_usage.values():
            all_timestamps.update(ts for ts in inner_dict.keys() if in_interval(ts))
        time_stmps_cpu_usage = sorted(all_timestamps)
        return time_stmps, time_stmps_cpu_usage
        
    def set_time_stmps_for_node_types(self,time_start_dt=None,time_end_dt=None):
        self.time_stmps['entry_nodes'], self.time_stmps_cpu_usage['entry_nodes'] = self.get_time_stmps(self.data_rates['entry_nodes'], self.cpu_usage['entry_nodes'],time_start_dt, time_end_dt)
        self.time_stmps['build_nodes'], self.time_stmps_cpu_usage['build_nodes'] = self.get_time_stmps(self.data_rates['build_nodes'], self.cpu_usage['build_nodes'],time_start_dt, time_end_dt)
        if self.timeslice_forwarding_activated:
            self.time_stmps['receiving_nodes'], self.time_stmps_cpu_usage['receiving_nodes'] = self.get_time_stmps(self.data_rates['receiving_nodes'], 
                                                                                                             self.cpu_usage['receiving_nodes'],time_start_dt, time_end_dt)
    
    def plot_total_data_rate(self):
        for node_type in self.data_rates.keys():
            dir = os.getcwd()
            path = os.path.join(dir,f'plots/collectl_plots/general/{node_type}')
            if not os.path.exists(path):
                os.makedirs(path)
            path = path + '/'
            total_data_rate = []
            if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                total_data_rate_out = []        
                    
            for time_stmp in self.time_stmps[node_type]:
                total_data_rate_tmp = 0
                total_data_rate_out_tmp = 0
                for val in self.data_rates[node_type].values():
                    if time_stmp in val:
                        if node_type == 'entry_nodes':
                            #print(val[time_stmp])
                            total_data_rate_tmp += val[time_stmp]['KBOut']/1000000
                        elif node_type == 'build_nodes':
                            total_data_rate_tmp += val[time_stmp]['KBIn']/1000000
                            if self.timeslice_forwarding_activated:
                                total_data_rate_out_tmp += val[time_stmp]['KBOut']/1000000
                        elif node_type == 'receiving_nodes':
                            total_data_rate_tmp += val[time_stmp]['KBIn']/1000000
                total_data_rate.append(total_data_rate_tmp)   
                if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                    total_data_rate_out.append(total_data_rate_out_tmp)
            plt.figure(figsize=(10, 6))
            if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                plt.plot(self.time_stmps[node_type], total_data_rate,  linestyle='-', color='b', label='Data rate in')
                plt.plot(self.time_stmps[node_type], total_data_rate_out,  linestyle='-', color='c',  label='Data rate out')
            else:
                plt.plot(self.time_stmps[node_type], total_data_rate,  linestyle='-', color='b')
            plt.xlabel("Timestamp")
            plt.ylabel("Data rate in GB")
            plt.title("Total data rate")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                plt.legend()
            plt.savefig(path + 'collectl_total_data_rate.png')
            plt.close()

    def plot_avg_data_rate(self):
        for node_type in self.data_rates.keys():
            dir = os.getcwd()
            path = os.path.join(dir,f'plots/collectl_plots/general/{node_type}/')
            if not os.path.exists(path):
                os.makedirs(path)
            path = path + '/'
            num_nodes = len(self.data_rates[node_type])
            
            avg_data_rate = []
            if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                avg_data_rate_out = []
            for time_stmp in self.time_stmps[node_type]:
                avg_data_rate_tmp = 0
                avg_data_rate_out_tmp = 0
                for val in self.data_rates[node_type].values():
                    if time_stmp in val:
                        if node_type == 'entry_nodes':
                            #print(val[time_stmp])
                            avg_data_rate_tmp += val[time_stmp]['KBOut']/1000000
                        elif node_type == 'build_nodes':
                            avg_data_rate_tmp += val[time_stmp]['KBIn']/1000000
                            if self.timeslice_forwarding_activated:
                                avg_data_rate_out_tmp += val[time_stmp]['KBOut']/1000000
                        elif node_type == 'receiving_nodes':
                            avg_data_rate_tmp += val[time_stmp]['KBIn']/1000000
                avg_data_rate.append(avg_data_rate_tmp/num_nodes)   
                if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                    avg_data_rate_out.append(avg_data_rate_out_tmp/num_nodes)
            plt.figure(figsize=(10, 6))
            if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                plt.plot(self.time_stmps[node_type], avg_data_rate,  linestyle='-', color='b', label='Data rate in')
                plt.plot(self.time_stmps[node_type], avg_data_rate_out,  linestyle='-', color='c', label='Data rate out')
                plt.legend()
            else:
                plt.plot(self.time_stmps[node_type], avg_data_rate,  linestyle='-', color='b')
            plt.xlabel("Timestamp")
            plt.ylabel("Data rate in GB")
            plt.title("Average data rate")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(path + 'avg_data_rate.png')
            plt.close()

    def plot_data_rate_mean_max_min(self):
        for node_type in self.data_rates.keys():
            dir = os.getcwd()
            path = os.path.join(dir,f'plots/collectl_plots/general/{node_type}')
            if not os.path.exists(path):
                os.makedirs(path)
            path = path + '/'
            num_nodes = len(self.data_rates[node_type])
            avg_data_rate = []
            max_rate = []
            min_rate = []
            if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                avg_data_rate_out = []
                max_rate_out = []
                min_rate_out = []
            for time_stmp in self.time_stmps[node_type]:
                avg_data_rate_tmp = 0
                time_stmp_max = 0
                time_stmp_min = 10000000
                avg_data_rate_tmp_out = 0
                time_stmp_max_out = 0
                time_stmp_min_out = 10000000
                for val in self.data_rates[node_type].values():
                    if time_stmp in val:
                        if node_type == 'entry_nodes':
                            #print(val[time_stmp])
                            data_rate = val[time_stmp]['KBOut']/1000000
                        elif node_type == 'build_nodes':
                            data_rate = val[time_stmp]['KBIn']/1000000
                            if self.timeslice_forwarding_activated:
                                data_rate_out = val[time_stmp]['KBOut']/1000000
                        elif node_type == 'receiving_nodes':
                            data_rate = val[time_stmp]['KBIn']/1000000
                            
                        avg_data_rate_tmp += data_rate
                        if time_stmp_max < data_rate:
                            time_stmp_max = data_rate
                        if time_stmp_min > data_rate:
                            time_stmp_min = data_rate
                        if self.timeslice_forwarding_activated and node_type == 'build_nodes':  
                            avg_data_rate_tmp_out += data_rate_out
                            if time_stmp_max_out < data_rate_out:
                                time_stmp_max_out = data_rate_out
                            if time_stmp_min_out > data_rate_out:
                                time_stmp_min_out = data_rate_out
                avg_data_rate.append(avg_data_rate_tmp/num_nodes) 
                max_rate.append(time_stmp_max)
                min_rate.append(time_stmp_min)
                if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                    avg_data_rate_out.append(avg_data_rate_tmp_out/num_nodes) 
                    max_rate_out.append(time_stmp_max_out)
                    min_rate_out.append(time_stmp_min_out)
            plt.figure(figsize=(10, 6))
            plt.fill_between(self.time_stmps[node_type], min_rate, max_rate, color='lightgrey', label='Range (min data rate-max data rate)')
            plt.plot(self.time_stmps[node_type], max_rate, color='black', linestyle='--', linewidth=1, label='Max rate')
            plt.plot(self.time_stmps[node_type], min_rate, color='black', linestyle='--', linewidth=1, label='Min rate')
            plt.plot(self.time_stmps[node_type], avg_data_rate, linestyle='-', color='k')
            plt.xlabel("Timestamp")
            plt.ylabel("Data rate in GB")
            plt.title("Average data rate with maximum and minium")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(path + 'avg_data_rate_max_min.png')
            plt.close()
            if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                plt.figure(figsize=(10, 6))
                plt.fill_between(self.time_stmps[node_type], min_rate, max_rate, color='lightgrey', label='Range (min data rate-max data rate)')
                plt.plot(self.time_stmps[node_type], max_rate, color='black', linestyle='--', linewidth=1, label='Max rate')
                plt.plot(self.time_stmps[node_type], min_rate, color='black', linestyle='--', linewidth=1, label='Min rate')
                plt.plot(self.time_stmps[node_type], avg_data_rate, linestyle='-', color='k')
                plt.xlabel("Timestamp")
                plt.ylabel("Data rate in GB")
                plt.title("Average data rate with maximum and minium")
                plt.xticks(rotation=45)
                plt.grid(True)
                plt.tight_layout()
                plt.legend()
                plt.savefig(path + 'avg_data_rate_max_min_output.png')
                plt.close()
                
    def bar_plots_data_rates(self):
        for node_type in self.data_rates.keys():
            dir = os.getcwd()
            path = os.path.join(dir, f'plots/collectl_plots/general/{node_type}')
            if not os.path.exists(path):
                os.makedirs(path)
            path = path + '/'
            averages = []
            if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                averages_out = []
            for node in self.data_rates[node_type].values():
                avg = 0
                cnt = 0
                avg_out = 0
                for time_stmp in self.time_stmps[node_type]:
                    if time_stmp in node:
                        if node_type == 'entry_nodes':
                            avg += node[time_stmp]['KBOut']/1000000
                        elif node_type == 'build_nodes':
                            avg += node[time_stmp]['KBIn']/1000000
                            if self.timeslice_forwarding_activated:
                                avg_out += node[time_stmp]['KBOut']/1000000
                        elif node_type == 'receiving_nodes':
                            avg += node[time_stmp]['KBIn']/1000000
                        cnt += 1
                    else:
                        avg += 0
                        cnt += 1
                        
                if cnt != 0:
                    averages.append(avg/cnt)
                    if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                        averages_out.append(avg_out/cnt)
                else:
                    averages.append(avg)
                    if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                        averages_out.append(avg_out)
            
            labels = list(self.data_rates[node_type].keys())
            cmap = plt.get_cmap('viridis')
            colors = [cmap(i / len(labels)) for i in range(len(labels))]
            plt.figure(figsize=(12, 6))
            plt.bar(labels,averages,color=colors)
            plt.title('Bar Plot of data rates')
            plt.ylabel('Data Rate in GB')
            #plt.grid(axis='y')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(path + f'bar_plot_data_rate_{node_type}.png')
            plt.close()
            if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                labels = list(self.data_rates[node_type].keys())
                cmap = plt.get_cmap('viridis')
                colors = [cmap(i / len(labels)) for i in range(len(labels))]
                plt.figure(figsize=(12, 6))
                plt.bar(labels,averages,color=colors)
                plt.title('Bar Plot of data rates')
                plt.ylabel('Data Rate in GB')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(path + f'bar_plot_data_rate_out_{node_type}.png')
                plt.close()
            
    def plot_data_rate_single(self):
        for node_type in self.data_rates.keys():
            dir = os.getcwd()
            path = os.path.join(dir,f'plots/collectl_plots/nodes/{node_type}')
            if not os.path.exists(path):
                os.makedirs(path)
            path = path + '/'
            for key,val in self.data_rates[node_type].items():
                total_data_rate = []
                if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                    total_data_rate_out = []
                for time_stmp in self.time_stmps[node_type]:
                    if time_stmp in val:
                        if node_type == 'entry_nodes':
                            total_data_rate.append(val[time_stmp]['KBOut']/1000000)
                        elif node_type == 'build_nodes':
                            total_data_rate.append(val[time_stmp]['KBIn']/1000000)
                            if self.timeslice_forwarding_activated:
                                total_data_rate_out.append(val[time_stmp]['KBOut']/1000000)
                        elif node_type == 'receiving_nodes':
                            total_data_rate.append(val[time_stmp]['KBIn']/1000000)
                    else:
                        total_data_rate.append(0)
                        if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                            total_data_rate_out.append(0)
                plt.figure(figsize=(10, 6))
                if self.timeslice_forwarding_activated and node_type == 'build_nodes':
                    plt.plot(self.time_stmps[node_type], total_data_rate, linestyle='-', color='b', label='Data rate in')
                    plt.plot(self.time_stmps[node_type], total_data_rate_out, linestyle='-', color='c', label='Data rate out')
                    plt.legend()
                else:
                    plt.plot(self.time_stmps[node_type], total_data_rate, linestyle='-', color='b')
                plt.xlabel("Timestamp")
                plt.ylabel("Data rate in GB")
                plt.title(f"data rate for node {key}")
                plt.xticks(rotation=45)
                plt.grid(True)
                plt.tight_layout()
                plt.savefig(path + f'data_rate_{key}.png')
                plt.close()
                
    def plot_cpu_usage_avg(self):
        for node_type in self.cpu_usage.keys():
            dir = os.getcwd()
            path = os.path.join(dir,f'plots/collectl_plots/cpu_usage/{node_type}')
            if not os.path.exists(path):
                os.makedirs(path)
            path = path + '/'
            for key,val in self.cpu_usage[node_type].items():
                avg_cpu_usage = []
                for time_stmp in self.time_stmps[node_type]:
                    if time_stmp in val:
                        avg_cpu_usage.append(100 - val[time_stmp]['overall_avg'])
                    else:
                        avg_cpu_usage.append(0)
                        
                plt.figure(figsize=(10, 6))
                plt.plot(self.time_stmps[node_type], avg_cpu_usage, linestyle='-', color='b')
                plt.xlabel("Timestamp")
                plt.ylabel("Used cpu in %")
                plt.title(f"CPU usage for all CPUs for node {key}")
                plt.xticks(rotation=45)
                plt.grid(True)
                plt.tight_layout()
                plt.savefig(path + f'overall_avg_cpu_usage_{key}.png')
                plt.close()
                
                    
    def plot_cpu_usage_single(self):
        for node_type in self.cpu_usage.keys():
            dir = os.getcwd()
            path = os.path.join(dir,f'plots/collectl_plots/cpu_usage/{node_type}')
            if not os.path.exists(path):
                os.makedirs(path)
            path = path + '/'
            for key, val in self.cpu_usage[node_type].items():
                first_timestmp = next((item for item in self.time_stmps[node_type] if item in val), None)
                alloc_cpus = [cpu for cpu in val[first_timestmp].keys() if cpu != 'overall_avg']
                cpu_usage = {}
                for timestmp in self.time_stmps[node_type]:
                    if timestmp in val:
                        for cpu in alloc_cpus:
                            if cpu not in cpu_usage:
                                cpu_usage[cpu] = []
                            usg = 100 - val[timestmp][cpu]
                            cpu_usage[cpu].append(usg)
                    else:
                        for cpu in alloc_cpus:
                            if cpu not in cpu_usage:
                                cpu_usage[cpu] = []
                            usg = 0
                            cpu_usage[cpu].append(usg)
                plt.figure(figsize=(10, 6))
                for cpu in alloc_cpus:
                    plt.plot(self.time_stmps[node_type], cpu_usage[cpu], linestyle='-', label=f'CPU: {cpu}')
                plt.xlabel("Timestamp")
                plt.ylabel("Used cpu in %")
                plt.title(f"CPU usage for allocated CPUs for node {key}")
                plt.xticks(rotation=45)
                plt.grid(True)
                plt.tight_layout()
                plt.legend()
                plt.savefig(path + f'cpu_usage_alloc_{key}.png')
                plt.close()
                    
    