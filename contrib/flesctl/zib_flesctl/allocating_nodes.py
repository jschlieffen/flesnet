#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#Created on Thu Dec 19 15:04:17 2024

#@author: jschlieffen


"""Usage:
    allocating_nodes.py <allocating_nodes>
    allocating_nodes.py (-h | --help)

Options:
    -h --help  Show this message.
"""

# =============================================================================
# TODO: write new file with better structuring
# =============================================================================

import subprocess
import sys
import os
import time
import docopt
import re
import monitoring as mon
import curses

class slurm_commands:
    
    def __init__(self):
        None
        
    def alloc_nodes(self,node_numbers):
        #command = ['srun', 
        #           '--nodelist=%s'%(node_list),
        #           '--time-min=00:15:00',
        #           '--time=00:30:00',
        #           'ip a']
        #command = ['salloc',
        #           '--nodes=%s'%(node_numbers),
        #           '--time=00:05:00',
        #           '--ntasks=1',
        #           '&']
        command = 'salloc --nodes=%s -p big --constraint=Infiniband --time=00:20:00'%(node_numbers)
        allocation = subprocess.run(command,shell=True)
        print(allocation.returncode)
        return allocation.returncode
    
    def sbatch(self,node_numbers):
        command = 'sbatch'
    
    # DO NOT USE: Ask for password auth.
    def ssh_to_node(self,node_id):
        command = 'ssh %s' % (node_id)
        ssh = subprocess.run(command, shell=True)
        return ssh.returncode
    
    #Todo: try-except for all slurm-commands
    def pids(self,node_id):
        command = 'ps aux | grep %s' % (node_id) 
        try:
            #result = subprocess.Popen(command, capture_output=True, text=True, check=True, shell=True)
            #result = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
            result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout,stderr = result.communicate()
            return stdout
        except subprocess.CalledProcessError as e:
            print('Error')
            sys.exit(1)
        return None
    
    def kill_process(self,pid):
        return None
    
    # =============================================================================
    #  TODO:
    #       1. take care that the message may change
    #       2. make sure that the message 
    # =============================================================================
    def ethernet_ip(self,node_id):
        command = 'srun --nodelist=%s -N 1 --ntasks 1 ip a' % (node_id)
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout,stderr = result.communicate()
        match = re.search(r'eth0:(.*?)scope global eth0',stdout,re.DOTALL)
        content = match.group(1)
        match2 = re.search(r'inet (.*?)/23',content,re.DOTALL)
        #print(repr(content))
        content2 = match2.group(1)
        #print(repr(content2))
        #print(type(content))
        #print(result.stdout)
        return content2
    
    def infiniband_ip(self,node_id):
        command = 'srun --nodelist=%s -N 1 --ntasks 1 ip a' % (node_id)
        #print('test')
        #print('test_inf_id')
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        #result = subprocess.run(command, shell=True)
        #print('test_inf_id2')
        result.wait()
        stdout,stderr = result.communicate()
        #stdout = result.returncode
        #print(stdout)
        #print('test_inf_id3')
        #print(stdout)
        match = re.search(r'ib0:(.*?)scope global ib0',stdout,re.DOTALL)
        #print(match)
        content = match.group(1)
        match2 = re.search(r'inet (.*?)/23',content,re.DOTALL)
        #print(repr(content))
        content2 = match2.group(1)
        #print(repr(content2))
        #print(type(content))
        #print(result.stdout)
        return content2
        
    # =============================================================================
    #  TODOs:
    #   1. get the log message.
    #   2. make this a parallel process.
    # =============================================================================
    def start_customize_program(self,program_name,node_id):
        #command = 'srun --nodelist=%s %s &> /dev/null &' %(node_id,program_name)
        command = '%s &> /dev/null &' %(program_name)
        #result = subprocess.run(command,capture_output=True, text=True, check=True, shell=True)
        #command = 'sbatch --nodelist=%s %s &> /dev/null &' % (node_id,program_name)
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        #try:
            #print('test')
            #result = subprocess.Popen(command, capture_output=True, text=True, check=True, shell=True)
            #return result.stdout
        #except subprocess.CalledProcessError as e:
            #print('Error')
            #sys.exit(1)
        print('test1')
        #log_variable = ""
        #print(result.stdout)
        print('test2')
        #print(result.stderr)
        print(result)
        #stdout, stderr = result.communicate()
        print('test3')
        #print(stderr)
        print(result.poll())
        return None
    
    def srun_test(self,file, node_id):
        command ='srun --nodelist=%s python3 %s' % (node_id,file)
        print(os.path.exists(file))
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result)
        #stdout, stderr = result.communicate()
        #print('test3')
        #print(stderr)
        print(result.poll())
        return None
    
    #Funktioniert nicht wie es soll.
    def exit_node(self,node_id):
        command = 'exit'
        subprocess.run(command, shell=True)
        

class Entry_nodes(slurm_commands):
    
    def __init__(self,node_list,build_nodes_ips,build_nodes_eth_ips):
        super().__init__()
        self.node_list = node_list
        self.build_nodes_ips = build_nodes_ips
        self.build_nodes_eth_ips = build_nodes_eth_ips
        self.pids = []
    
    #TODO: remove node id from the functioninput
    def start_mstool(self,node_id):
        program_string = '../../../build/./mstool -i ../../../build/500GB.dmsa -O fles_in -D 1 -L mstool.log'
        self.start_customize_program(program_string, node_id)
    
    def start_flesnet_old(self,node_id):
        program_string = '../../../build/./flesnet -L ttt.log -t zeromq -i 0 -I shm:/fles_in/0 -o 0 -O shm:/fles_out/0 --timeslice-size 1 --processor-instances 0 -e "_"'
        self.start_customize_program(program_string, node_id)
        time.sleep(5)
        with open('ttt.log', 'r') as file:
            print(file.read())
            file.seek(0,2)
            while(True):
                line = file.readline()
                if line:
                    print(line.strip())
                else:
                    #print('test')
                    time.sleep(0.1)
        return None
    
    def start_flesnet(self):
        file = 'input.py'
        print(os.path.exists(file))
        for node in self.node_list.keys():
            logfile = "logs/entry_node_%s.log" % node
            print('test123: ', self.build_nodes_ips)
            command = 'srun --nodelist=%s -N 1 %s %s %s' % (node,file,logfile,self.build_nodes_ips)
            result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(result.poll())    
            time.sleep(5)
            #stdout,stderr = result.communicate()
            #result.stdin.write('foobar')
            self.pids += [result]
            #for stdout_line in iter(result.stdout.readline, ''):
                #print(stdout_line, end='')
        return None
    
    def start_flesnet_zeromq(self):
        file = 'input_zeromq.py'
        print(os.path.exists(file))
        for node in self.node_list.keys():
            command = 'srun --nodelist=%s -N 1 %s %s' % (node,file,self.build_nodes_eth_ips)
            result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(result.poll())        
        return None
    
    def stop_flesnet(self):
        for pid in self.pids:
            pid.stdin.write('stop')
            stdout, stderr = pid.communicate()
            print('Output: ',stdout)
            print('Error: ', stderr)
            print('\n')
    
class Build_nodes(slurm_commands):
    
    def __init__(self,node_list,entry_nodes_ips,entry_nodes_eth_ips):
        super().__init__()
        self.node_list = node_list
        self.entry_node_ips = entry_nodes_ips
        self.entry_node_eth_ips = entry_nodes_eth_ips
        self.pids = []
        
    def start_flesnet(self):
        file = 'output.py'
        print(os.path.exists(file))
        for node in self.node_list.keys():
            logfile = 'logs/build_node_%s.log' % (node)
            print('test12234', self.entry_node_ips)
            command = 'srun --nodelist=%s -N 1 %s %s %s' % (node,file,logfile,self.entry_node_ips)
            result = subprocess.Popen(command, shell=True,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print('start_build_nodes')
            print(result.poll())        
            self.pids += [result]
        return None
    
    def start_flesnet_zeromq(self):
        file = 'output_zeromq.py'
        print(os.path.exists(file))
        for node in self.node_list.keys():
            command = 'srun --nodelist=%s -N 1 %s %s' % (node,file,self.entry_node_eth_ips)
            result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print('start_build_nodes')
            print(result.poll())        
        return None

    def stop_flesnet(self):
        for pid in self.pids:
            pid.stdin.write('stop')
            stdout, stderr = pid.communicate()
            print('Output: ',stdout)
            print('Error: ', stderr)
            print('\n')
    
     
class execution(slurm_commands):
    
    def __init__(self,num_entrynodes, num_buildnodes):
        super().__init__()
        self.num_entrynodes = num_entrynodes 
        self.num_buildnodes = num_buildnodes
        self.entry_nodes = {}
        self.build_nodes = {} 
        self.schedule_nodes()
        self.entry_nodes_ips = ""
        self.build_nodes_ips = ""
        self.get_ips()
        self.entry_nodes_eth_ips = ""
        self.build_nodes_eth_ips = ""
        self.get_eth_ips()
        self.entry_nodes_cls = Entry_nodes(self.entry_nodes,self.build_nodes_ips,self.build_nodes_eth_ips)
        self.build_nodes_cls = Build_nodes(self.build_nodes, self.entry_nodes_ips,self.entry_nodes_eth_ips)
        
    
    def get_node_list(self):
        node_str = os.environ.get('SLURM_NODELIST')
        nodes_numbers = re.findall(r'\d+',node_str)
        node_list = [f"htc-cmp{num}" for num in nodes_numbers]
        return node_list
    
    def get_eth_ips(self):
        for key, val in self.entry_nodes.items():
            self.entry_nodes_eth_ips += 'shm://' + val['eth_ip'] + '/0'
        for key, val in self.build_nodes.items():
            self.build_nodes_eth_ips += 'shm://' + val['eth_ip'] + '/0'
        print(self.entry_nodes_eth_ips)
        print(self.build_nodes_eth_ips)
            
        
    def get_ips(self):
        for key,val in self.entry_nodes.items():
            print(key)
            print(val['inf_ip'])
            self.entry_nodes_ips += val['inf_ip'] + "sep"
        for key,val in self.build_nodes.items():
            print(key)
            print(val['inf_ip'])
            self.build_nodes_ips += val['inf_ip'] + "sep"
            
    # =============================================================================
    # Ich habe keine Ahnung ob sich hier eventuell durch sbatch was aendert.
    # =============================================================================
    def schedule_nodes(self):
        node_list = self.get_node_list()
        print(node_list)
        entry_nodes_cnt = 0
        build_nodes_cnt = 0
        if node_list is None:
            print("Error: SLURM_NODELIST is not set.")
            sys.exit(1)
        elif len(node_list) != self.num_entrynodes + self.num_buildnodes:
            print('Incorrect number of nodes')
            sys.exit(1)
        for node in node_list:
            node_ip = self.infiniband_ip(node)
            node_eth_ip = self.ethernet_ip(node)
            time.sleep(1)
            print(node)
            print(node_ip)
            if entry_nodes_cnt < self.num_entrynodes:
                self.entry_nodes[node] = {
                    'node' : node,
                    'inf_ip' : node_ip,
                    'eth_ip' : node_eth_ip}
                    #'allocated_build_node' : ''} #to be inserted later
                entry_nodes_cnt += 1
            elif build_nodes_cnt < self.num_buildnodes:
                self.build_nodes[node] = {
                    'node' : node,
                    'inf_ip' : node_ip,
                    'eth_ip' : node_eth_ip}
                    #'allocated_entry_node' : ''} #to be inserted later
                build_nodes_cnt += 1
            else:
                print('unexpected error with the number of nodes')
                sys.exit(1)
            #self.bijectiv_mapping()
     
    def bijectiv_mapping(self):
        for entry_node, build_node in zip(self.entry_nodes.keys(), self.build_nodes.keys()):
            self.entry_nodes[entry_node]['allocated_build_node'] = build_node
            self.build_nodes[build_node]['allocated_entry_node'] = entry_node
    
    
    def start_Flesnet(self):
        #file = 'input.py %s' (self.build_nodes_ips)
        #node_list = os.environ.get('SLURM_NODELIST')
        self.entry_nodes_cls.start_flesnet()
        self.build_nodes_cls.start_flesnet()
            
    def start_Flesnet_zeromq(self):
        #file = 'input.py %s' (self.build_nodes_ips)
        #node_list = os.environ.get('SLURM_NODELIST')
        self.entry_nodes_cls.start_flesnet_zeromq()
        self.build_nodes_cls.start_flesnet_zeromq()
            
    #def start_build_nodes(self):
    
    def stop_via_ctrl_c(self):
        try: 
            self.monitoring()
        except KeyboardInterrupt:
            print('Interrupting')
            self.build_nodes_cls.stop_flesnet()
            self.entry_nodes_cls.stop_flesnet()

        return None
        
    # =============================================================================
    # TODO: make log file depend on node id
    # maybe TODO: function also calls for output nodes
    # =============================================================================
    def monitoring(self):
        file_names = []
        for entry_node in self.entry_nodes.keys():
            logfile = 'logs/entry_node_%s.log' % (entry_node)
            total_data = 1000
            file_names.append((logfile,total_data))
        for build_node in self.build_nodes.keys():
            logfile = 'logs/build_node_%s.log' % (build_node)
            total_data = 2000
            file_names.append((logfile,total_data))
            #print('test')
            #mon.sequential_monitoring(['logs/flesnet_input_file.log','logs/flesnet_output_file.log'],[500,1000])
        #curses.wrapper(mon.main,[('logs/flesnet_input_file.log',1000), ('logs/flesnet_output_file.log',2000)])
        curses.wrapper(mon.main,file_names)
        
def main():
    arg = docopt.docopt(__doc__, version='0.2')
    
    allocating_nodes = arg["<allocating_nodes>"]
    
    s = slurm_commands()
    #print(type(allocating_nodes))
    #s.alloc_nodes('htc-cmp507')
    #print('test3')
    if allocating_nodes != '0':
        s.alloc_nodes(4)
        #s.exit_node('jsdfbjkwebf')
    else:
        """
        node = os.environ.get('SLURM_NODELIST')
        print(node)
        print(type(node))
        if node is None:
            print("Error: SLURM_NODELIST is not set. Did you run this within a SLURM job allocation?")
        else:
            print(f"Allocated node: {node}")
        print('test1')
        print(s.pids(node))
        print('test2')
        print(node)
        #inf_id = s.infiniband_ip(node)
        #print(inf_id)
        #eth_id = s.ethernet_ip(node)
        #print(eth_id)
        #program_string = '../../build/./mstool -i ../../build/500GB.dmsa -O fles_in -D 1 -L test.log'
        #s.start_customize_program(program_string, node)
        print(s.pids(node))%
        #e = Entry_nodes(1, 1)
        #e.start_mstool(node)
        #time.sleep(5)
        #e.start_flesnet(node)
        #print(s.ssh_to_node(node))
        s.srun_test('input.py 87325', node)
        # s.exit_node('jkfeb')
        """
        print('test')
        exec_ = execution(2, 2)
        #exec_.schedule_nodes()
        print('Entry nodes: ', exec_.entry_nodes)
        print('Build nodes: ', exec_.build_nodes)
        #exec_.get_ips()
        print('Build nodes ips: ' + exec_.entry_nodes_ips)
        print('Entry Nodes ips: ' + exec_.build_nodes_ips)
        exec_.start_Flesnet()
        exec_.stop_via_ctrl_c()
        #exec_.start_Flesnet_zeromq()
    print('test5')

    
if __name__ == '__main__':
    main()
        
    
    