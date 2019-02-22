#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 26 21:40:00 2018
AF detection algorithm
    Major Dependencies:
        WFDB (MATLAB):      physionet package for viewing, analyzing, and creating recordings of physiologic signals
        shreyasi-datta-209: Code from 2017 computing in cardiology challenge 2017. https://physionet.org/challenge/2017/sources/shreyasi-datta-209.zip
                            Note: the driving function 'challenge.m' was changed to accomodate passing ECG signal and 
                            time values directly from python. The signature was changed from:
                            'function classifyResult = challenge(recordName)'
                            
                            to:
                            'function classifyResult = challengeKGH(ecg, fs)'
                            
                            and the line:
                            '[~,ecg,fs,~]=rdmat(recordName);'
                            
                            Was replaced with :
                            'try
                                ecg = cell2mat(ecg)';
                                fs = double(fs);
                            catch
                            end'
    
"""

import pandas as pd
import numpy as np
import matlab.engine

from bokeh.models import PointDrawTool

from bokeh.plotting import figure 
from bokeh.io import show, curdoc
from bokeh.layouts import column, row, layout
from bokeh.models import ColumnDataSource, Paragraph

import time

def AF(path,outfile):
    # Start Matlab engine
    print('Starting Matlab engine')
    eng = matlab.engine.start_matlab();
    eng.addpath('/mnt/data04/Conduit/afib/challengeCode');
    n_seconds = 30 # length of segments
    fs = 240 # sampling frequency
    dis_value = -79 # default value when disconnected for bedmaster ICU data
    block_size = 100 # write to df every n blocks
    len_seg = n_seconds*fs # number of indices to select
    WFDBNAN = -128 #https://physionet.org/physiotools/matlab/wfdb-app-matlab/html/mat2wfdb.m 

    results = [] # empty list to hold results
    i = 0 # value to hold index location in hdf5 file
    blocks = 0 # holds number of blocks written so far
    time_start = time.time()
    time_reset = time.time()
    try: 
        ECG = pd.read_hdf(path,key = 'Waveforms',start = len_seg*i,stop = len_seg*(i+1)-1).II
        #print(blocks, ECG)
        ECG = ECG.fillna(WFDBNAN)
        #ECG = ECG_full.II
        while(not ECG.empty):
            print(len(results))
            if min(ECG) <= dis_value: # if value has any non-existant values, list as '-'
                results += '-'
            else:
                results += eng.challengeKGH(list(ECG),fs,nargout=1) # get classification
            i += 1
            time_finished_processing = time.time()
            if len(results) >= block_size:
                print('Sending to df')
                pd.DataFrame(results, index = range(block_size*(blocks)*len_seg, block_size*(blocks+1)*len_seg, len_seg)).to_hdf(outfile,key = 'AF',append=True,format='t')
                results = []
                blocks += 1
                time_block_done = time.time()
                #print("*********************Finished sending to df:",time_block_done-time_reset)
                timr_reset = time.time()
            ECG = pd.read_hdf(path,key = 'Waveforms',start = len_seg*i,stop = len_seg*(i+1)-1).II
            ECG = ECG.fillna(WFDBNAN)
            #ECG = ECG_full.II
        pd.DataFrame(results, index = range(block_size*(blocks)*len_seg, block_size*(blocks)*len_seg+len_seg*len(results), len_seg)).to_hdf(outfile,key = 'AF',append=True,format='t')
    except FileNotFoundError:
        print('File at' + path + 'not found')
        return
    except KeyError:
        print("File has no Waveforms")
        return
    finally:
        print('All Done')
        eng.quit()


# Creates a R_peak key on the hdf file at 'outpath' using the waveforms key from the hdf file at 'path'
def rPeaks(path,outpath):
    print('Starting Matlab engine')
    eng = matlab.engine.start_matlab();
    eng.addpath('/mnt/data04/Conduit/afib/mcode');
    block_size = 10000
    i = 0
    try: 
        store = pd.read_hdf(path, key = 'Waveforms',start = block_size*i,stop = block_size*(i+1)-1)
        while(not store.empty):
            ann, anntype = eng.ecgpuwave_wrapper(list(pd.to_numeric(store.index)),list(store.II*1000),'test',240,nargout=2)
            Q = [int(ann[i][0]) for i, e in enumerate(anntype) if e == 'N']
            P = [int(ann[i][0]) for i, e in enumerate(anntype) if e == 'p']
            T = [int(ann[i][0]) for i, e in enumerate(anntype) if e == 't']
            pd.DataFrame({'Position':store.iloc[Q,:].index, 'Value':store.iloc[Q,:].II}).to_hdf(outpath, 'R_Peaks', append = True, format = 't')
            pd.DataFrame({'Position':store.iloc[P,:].index, 'Value':store.iloc[P,:].II}).to_hdf(outpath, 'P_Peaks', append = True, format = 't')
            pd.DataFrame({'Position':store.iloc[T,:].index, 'Value':store.iloc[T,:].II}).to_hdf(outpath, 'T_Peaks', append = True, format = 't')
            i += 1
            store = pd.read_hdf(path, key = 'Waveforms',start = block_size*i,stop = block_size*(i+1)-1)
    except FileNotFoundError:
        print('File at' + path + 'not found')
        return
    finally:
        print("All Done")
        eng.quit()
        #ECG.close()
