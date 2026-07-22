#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 14:23:28 2026

@author: jschlieffen
"""
import subprocess
import os 
import time
from logging_lib.log_msg import *


class Slurm_starter:
    
    def __init__(self, node_types):
        self.processes = {}
        for node_type in node_types:
            self.processes[node_type] = {}
    
    def start_process(self, node_type, node, num_cpus, memory ,file,params):
        command = (
            f"srun --nodelist={node} -N 1 -n 1 -c {num_cpus} --mem={memory} {file} {params}"    
        )
        try:
            result = subprocess.Popen(command,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            return False
        self.processes[node_type][node] = {
                'result' : result,
                'command' : f"{file} {params}"
            }
        return True
    
    def kill_process(self,node_type, node):
        with open('tmp/communication/central_manager.txt', 'w') as f:
            f.write(f"{node_type} {node}: kill")
            f.flush()
            os.fsync(f.fileno())
            f.close()
        msg = ""
        cnt = 0
        retries = 0
        while msg != f"{node_type} {node}: done kill":

            try:
                with open(f"tmp/communication/{node_type}_{node}.txt","r") as f:
                    msg = f.read().strip()
            except FileNotFoundError:
                msg = ""
            time.sleep(0.5)
            if cnt > 2:
                logger.debug(f"Could not communicate with node: {node_type} {node}, retry: {cnt} max 10")
            if cnt > 10:
                if retries == 3:
                    logger.debug("max number of reties reached, cancel job")
                    self.cancel_job_step(node_type, node)
                    logger.debug(f"Job for node: {node_type} {node} canceled")
                logger.debug(f"Could not communicate with node: {node_type} {node}, checking if process still active")
                if self.check_process_still_active(node_type, node):
                    retries += 1
                else:
                    self.cancel_job_step(node_type, node)
                    logger.debug(f"Job for node: {node_type} {node} canceled")
                    return False
        return True
        
    def revieve_process(self,node_type, node):
        with open('tmp/communication/central_manager.txt', 'w') as f:
            f.write(f"{node_type} {node}: revieve")
            f.flush()
            os.fsync(f.fileno())
            f.close()
        msg = ""
        cnt = 0
        retries = 0
        while msg != f"{node_type} {node}: done revieve":
            if retries < 3:
                try:
                    with open(f"tmp/communication/{node_type}_{node}.txt","r") as f:
                        msg = f.read().strip()
                except FileNotFoundError:
                    msg = ""
            time.sleep(0.5)
            if cnt > 2:
                logger.debug(f"Could not communicate with node: {node_type} {node}, retry: {cnt} max 10")
            if cnt > 10:
                if retries == 3:
                    logger.debug("max number of reties reached, cancel job")
                    self.cancel_job_step(node_type, node)
                    logger.debug(f"Job for node: {node_type} {node} canceled")
                    return False
                logger.debug(f"Could not communicate with node: {node_type} {node}, checking if process still active")
                if self.check_process_still_active(node_type, node):
                    retries += 1
                else:
                    self.cancel_job_step(node_type, node)
                    logger.debug(f"Job for node: {node_type} {node} canceled")
                    return False
        return True
        
    def stop_process(self,node_type, node, is_subprocess):
        retries = 0
        with open('tmp/communication/central_manager.txt', "w") as f:
            f.write(f"{node_type} {node}: stop")
            f.flush()
            os.fsync(f.fileno())
            f.close()
        if is_subprocess:
            msg = ""
            cnt = 0
            
            while msg != f"{node_type} {node}: done stop":
                try:
                    with open(f"tmp/communication/{node_type}_{node}.txt","r") as f:
                        msg = f.read().strip()
                except FileNotFoundError:
                    msg = ""
                time.sleep(0.5)
                cnt += 1
                if cnt > 2:
                    logger.debug(f"Could not communicate with node: {node_type} {node}, retry: {cnt} max 20")
                if cnt > 20:
                    if retries > 3:
                        logger.debug("max number of retries reached, skipping job")
                        return "",""
                    else:
                        cnt = 0
                        retries += 1
            return "1","1"
        else:
            while retries < 3:
                try:
                    stdout, stderr = self.processes[node_type][node]['result'].communicate(timeout=60)
                    break
                except subprocess.TimeoutExpired:
                    logger.debug(f"Could not communicate with node: {node_type} {node}, checking if process still active")
                    if self.check_process_still_active(node_type, node):
                        retries += 1
                    else:
                        self.cancel_job_step(node_type, node)
                        logger.debug(f"Job for node: {node_type} {node} canceled")
                        return "",""
            return stdout,stderr
                        
    def check_process_still_active(self,node_type,node):
        process_command = self.processes[node_type][node]['command']
        command = (f"srun --nodelist=node -N 1 -n 1 pgrep -af {process_command}")
        try:
            res = subprocess.Popen(command,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            logger.debug('communication failed due to: ',e)
        try:
            stdout,stderr = res.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            logger.debug('communication failed. Node not reachable. Cancel Slurm job step')
            return False
        if process_command in stdout:
            logger.debug('process still active. Retry action')
            return True
        else:
            logger.debug('process probably not active anymore. Try cancel Slurm job step ')
            return False
    
    def cancel_job_step(self,node_type,node):
        try:
            with open('tmp/job_ids/{node_type}_{node}', 'r') as f:
                lines = f.read().splitlines()
        except FileNotFoundError:
            logger.debug('couldnot find job id')
        Slurm_jobstep_id = f"{lines[0]}.{lines[1]}"
        command = (f"scancel {Slurm_jobstep_id}")
        try:
            res = subprocess.Popen(command,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            logger.debug('communication failed due to: ',e)
        try:
            stdout,stderr = res.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            logger.debug('cancelation failed. Maybe node is not reachable at all')
        
        
        
                