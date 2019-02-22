#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Compare AF annotated dataframes.
AF_ann_compare.py 

    Compares hdf files in structure like below the same format as the Computing in Cardiology AF detection algorithm.
            0
    0       N
    2000    ~
    3500    A
    5000    O
    
    where N=normal, ~=noise, A=AF, O=other wave

    MAJOR DEPENDICIES:
        bokeh
        pandas
        helpers.py        helper functions written for this script

    TO RUN:
        bokeh serve --show afib_annotator.py --port 5100

    TO DO:
    1. Return non-overlapping ranges for each dataframe - or if there are any
    2. determine what the set the 'end' variable as?? arbitrarilly large number or the actual end of the file?

    FUNCTIONALITY:
    Currently only concerned with AF detection at same points
    1. Get where AF is annotated in both dataframes (df1 = gold standard, df2 = what were comparing too - machine?)
    2. Format as range()
    3. Get intersection from the ranges
    4. Return [[df1range, df2range], etc..] for all overlapping AF labelled segments

'''

import numpy as np
import pandas as pd
import time
import datetime
import os
import sys
import itertools

'''
find indexes of AF in annotator's df - beginning and end for each ~2min segment (tuple)
use tuples to find encompassing indexes in the machine df
return yes if AF is detected in both cases
'''
# def get_indicies_tuples(df):
#     lst = []
#     inds = list(df.index)
#     for i in range(len(inds)):
#         if i < len(inds)-1:
#             lst.append((inds[i],inds[i+1])) #what to do about last index
#         else:
#             lst.append((inds[i],'end'))
#     return lst
 
def get_AF_indicies(df,str_lbl):
    lstaf = []
    inds = list(df.index)
    for i in range(len(inds)):
        index = inds[i]
        if df[0].iloc[i] == str_lbl and i < len(inds)-1:
            lstaf.append((index,inds[i+1]))
        elif df[0].iloc[i] == str_lbl and i == len(inds)-1:
            lstaf.append((index,1000000)) #arbitary number??
    return lstaf

def comp_AF_ann(df1,df2,str_lbl):
    lstAFoverlap = []
    lst1af = get_AF_indicies(df1,str_lbl)
    lst2af = get_AF_indicies(df2,str_lbl)
    lstAF1not = lst1af
    lstAF2not = lst2af
    for tpl1 in lst1af:
        rng1 = range(tpl1[0], tpl1[1])
        for tpl2 in lst2af:
            rng2 = range(tpl2[0], tpl2[1])
            set1 = set(rng1)
            intersec = set1.intersection(rng2)
            if bool(intersec):
                lstAFoverlap.append([(rng1[0],rng1[-1]),(rng2[0],rng2[-1])])
                #if tuple is matched then remove from not matched list
                if tpl1 in lstAF1not:
                    lstAF1not.remove(tpl1)
                if tpl2 in lstAF2not:
                    lstAF2not.remove(tpl2)
    return lstAFoverlap, lstAF1not, lstAF2not


''' ********************** SAMPLE DATA *********************** '''
df1 = pd.DataFrame(['N','~','A','N','A','O','A'],columns=[0],index=[0,100,150,300,450,500,560])
df2 = pd.DataFrame(['N','~','A','N','A','O'],columns=[0],index=[0,80,170,290,460,500])
comp_AF_ann(df1,df2,'A')

''' ********************** REAL AF DATA ********************** '''
af2_path = '/mnt/data04/Conduit/afib/testAFAnn1.hdf'
af1_path = '/mnt/data04/Conduit/afib/testAFAnn2.hdf'
df1 = pd.read_hdf(af1_path)
df2 = pd.read_hdf(af2_path)
comp_AF_ann(df1,df2,'A')
