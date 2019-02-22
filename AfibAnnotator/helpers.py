#!/usr/bin/env python3
'''
Last Updated: December 2018
Victoria Tolls

helpers.py
    Helper functions for main file.



'''

import os
import pandas as pd
import itertools

from bokeh.layouts import widgetbox
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import TableColumn
from bokeh.palettes import Category10


#import waveform

#---------------LOAD FILES --------------------#
def get_files(path):  
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            size = round(os.path.getsize(os.path.join(path, file)) / (1024*1024.0),4) #>> 20 #to get in mb
            yield file,path,size

#load in paths for hdf and summary files
def load_file_source(hdf_path, af_path): #--> move to callbacks??
    dict_hdf = {"name": [], "hdf_full_path": [], "hdf_type": [], "annotated": []} #"hdf_size": [], "annotated":[]}
    for file,path,size in get_files(hdf_path):
        if file.endswith(".hd5"):
            base = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            dict_hdf['name'].append(base)
            dict_hdf["hdf_full_path"].append(path)
            dict_hdf["hdf_type"].append(extension)
            dict_hdf["annotated"].append(get_if_annotated(file, af_path))
    result = pd.DataFrame(dict_hdf)
    source = ColumnDataSource(result)
    columns = [
        TableColumn(field="name", title="File"),
        TableColumn(field="hdf_type", title="File Type"),
        TableColumn(field="annotated",title="Annotated"),
    ]
    return source,columns

def get_if_annotated(filename, af_path):
    fname = af_path+filename
    if os.path.isfile(fname):
        return 'Yes'
    else:
        return 'No'

#combine data to get full path
def load_selected_file(source,new):
    data = source.data
    row_selected = new[0]#new['1d']['indices'][0]
    if row_selected == []: #if none are selected use entire dataset
        print("None selected")
        return None
    else:
        hdf_file = data['hdf_full_path'][row_selected] + data['name'][row_selected] + data['hdf_type'][row_selected]
    return hdf_file


def load_annotation_file(source,new,out_path):
    data = source.data
    row_selected = new[0]#new['1d']['indices'][0]
    if row_selected == []: #if none are selected use entire dataset
        print("None selected")
        return None
    else:
        hdf_file = out_path + data['name'][row_selected] + data['hdf_type'][row_selected]
    return hdf_file


#check if file has already been annotated
def check_if_annotated(source,new):
    data = source.data
    row_selected = new[0]#new['1d']['indices'][0]
    return data['annotated'][row_selected]


#readin file then get keys
def load_hd5_file(active_file):
    hdf = pd.HDFStore(active_file)
    return hdf, hdf.keys()

#load hdf5 data
def get_hd5_data_columns(hdfs, key):
    temp_df = hdfs.select(key, start=1, stop=2) #read in one line - all we're looking for is columns
    if isinstance(temp_df,pd.DataFrame): #if it is a df then get the columns
        cols = list(temp_df.columns)
    elif isinstance(temp_df,pd.Series): #if it is a series then take the name
        cols = [temp_df.name]
    else:
        cols = None
    return cols

#read hdfs table using key and select speifified columns, using chunk iteration in case file is too large
def read_in_chunks(hdfs, key, cols):
    chunksize = 100000
    chunks = hdfs.select(key, chunksize=chunksize)
    return chunks
    # for chunk in chunks:
    #     chunk[cols]
    #wf_source = ColumnDataSource(df)
    #df['DateTime'] = wf_source.data['index']
    #ann_source = ColumnDataSource(df)
    #print(wf_source.data)
    #print(ann_source.data)
    #vs_sum = None

def get_data_for_graph(hdfs,key,cols):
    df = None
    try:
        df = hdfs.select(key)[cols] #everything works, read in table
    except KeyError:
        tmp_series = hdfs.select(key)
        if isinstance(tmp_series, pd.Series):
            df = tmp_series.to_frame()
    except MemoryError:
        chunks = read_in_chunks(hdfs, key, cols)
    print("Done")

# Returns the time difference between two datetimes in hours, minutes and seconds respectively
def duration_HMS(start, stop):
    duration = (stop-start).total_seconds()
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod (remainder, 60)
    return hours, minutes, seconds

#Bokeh color iterator
def colour_gen():
    for arg in itertools.cycle(Category10[10]):
        yield arg 

