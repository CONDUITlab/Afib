#!/usr/bin/env python3
# -*- coding: utf-8 -*-


'''
Example of how to use AF detection algorithm as in afib_peak_detector.py

Major Dependencies:
	afib_peak_detector	-functions that run the Computing in Cardiology detection algorithms
        Python modules (sys, time and os)
'''

in_path = '.'
files = get_files_from_dir(in_path)

for case in files:
    file_path = '/files/'+case
    #rpeaks_out_path = '/mnt/data04/Conduit/afib/new_files/peaks/'+case
    af_out_path = '/af/'+case
    if os.path.exists(af_out_path) == False:    
        print("Processing: ", case)
        AF(file_path, af_out_path)
    else:
        continue
