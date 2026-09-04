#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 19:32:49 2026

@author: jschlieffen
"""

import queue
from threading import Thread
import time
import os
import traceback

class commander(Thread):
    def __init__(self,channel):
        self.channel = channel