#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  1 17:37:38 2025

@author: jschlieffen
"""


from log_msg import *
import os
import importlib
import stat
import subprocess
import sys
from pathlib import Path
import params as par

class system_checker:
    
    def __init__(self):
        venv_path = Path("flesctrl_venv")
        self.python_exec = venv_path / 'bin' / 'python'
        self.required_libaries = [
                'docopt' , 'plotext' , 'matplotlib', 'seaborn' , 'deepdiff'
            ]
        self.required_files = [
                'central_manager.py',
                'execution.py',
                'input.py',
                'logfile_gen.py',
                'log_msg.py',
                'monitoring.py',
                'output.py',
                'params.py',
                'super_nodes.py',
                'timeslice_forwarding.py'
            ]
        self.files_with_perm = [
                ('input.py',0o755),
                ('output.py',0o755),
                ('super_nodes.py', 0o755),
                ('timeslice_forwarding.py', 0o755)
            ]
        self.setup_ready = True
    
    def check_venv_exists(self):
        if self.python_exec.exists():
            logger.info('venv exists')
        else:
            logger.critical("Python venv not found. Skip check of libaries")
            self.setup_ready = False
    
    def check_libraries(self):
        for lib in self.required_libaries:
            try:
                result = subprocess.run(
                     [str(self.python_exec), '-c', f'import {lib}'],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,
                     timeout=5
                 )
                if result.returncode != 0:
                    logger.critical(f"Libary not installed: {lib}")
                    self.setup_ready = False
            except ImportError:
                logger.critical(f"Libary not installed: {lib}")
                self.setup_ready = False
    
    def check_files_exist(self):
        for file in self.required_files:
            if not Path(file).is_file():
                logger.critical(f"file is missing: {file}")
                self.setup_ready = False
                
    def check_file_permissions(self):
        for file, permission in self.files_with_perm:
            file_path = Path(file)
            if not file_path.exists():
                continue
            mode = file_path.stat().st_mode
            actual_perm = stat.S_IMODE(mode)
            if actual_perm != permission:
                logger.critical(f"file: {file} got wrong permission. Expected: {oct(permission)}, got: {oct(actual_perm)} ")
                self.setup_ready = False
                
def main():
    setup_check = system_checker()
    setup_check.check_venv_exists()
    if setup_check.setup_ready:
        setup_check.check_libraries()
    setup_check.check_files_exist()
    setup_check.check_file_permissions()
    if not setup_check.setup_ready:
        logger.critical('Setup is not ready. Check log messages')
    else:
        logger.success('setup is ready for flesctrl.')  
    Par_ = par.Params('config.cfg')
    if Par_.validation_params(True):
        logger.success(f"Params are valid and ready for start")
    else:
        logger.error("Params invalid. Check logmessages")

if __name__ == '__main__':
    main()
                
                
                
                