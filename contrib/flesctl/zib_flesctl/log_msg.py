#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 13:58:56 2025

@author: jschlieffen
"""

import logging
from datetime import datetime

class LogColors:
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"  
    RESET = "\033[0m"

SUCCESS_LEVEL_NUM = 25  
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

def success(self, message, *args, **kws):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kws)

logging.Logger.success = success

class BoostLogFormatter(logging.Formatter):
    def format(self, record):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        levelname = record.levelname
        if levelname == "SUCCESS":
            color = LogColors.GREEN
        elif levelname == "INFO":
            color = LogColors.BLUE
        elif levelname == "WARNING":
            color = LogColors.YELLOW
        elif levelname == "ERROR":
            color = LogColors.RED
        elif levelname == "CRITICAL":
            color = LogColors.MAGENTA
        elif levelname == "DEBUG":
            color = LogColors.CYAN  
        else:
            color = LogColors.RESET
        log_message = f"{LogColors.GREEN}[{timestamp}]{LogColors.RESET} {color}{levelname}{LogColors.RESET}: {record.getMessage()}"
        return log_message

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(BoostLogFormatter())
    logger.addHandler(console_handler)

    return logger



logger = setup_logger()

