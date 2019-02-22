#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Based on Phil's slice_hd5 code.
Used to get first hour of waveform data from hd5 file.

"""

import sys
import os
import pandas as pd
import csv

from slice_hd5 import slice_hd5

in_path = sys.argv[1] #to use when the full directory is to be processed
out_path = sys.argv[2]

def get_first_hour(filename, in_dir, out_dir, time_hrs):
    in_full_path = os.path.join(in_dir, filename)
    out_full_path = os.path.join(out_dir, filename)
    if os.path.exists(out_full_path) == False: #skip those already processed
        slice_hd5(in_full_path, out_full_path, None, time_hrs)
        
get_first_hour(filename,in_path,out_path,'1 hours')
