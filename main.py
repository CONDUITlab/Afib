#!/usr/bin/env python3
# -*- coding: utf-8 -*-


'''
Last Updated: December 2018
Victoria Tolls

Waveform annotator 

    Based on wf_explore.py code

    Users can view the ECG II lead then can use sliding bars to select a segment, 
    then label that segment.
    This is then saved as a hdf file in the same format as the Computing in Cardiology AF detection algorithm (see below for example)
            AF
    0       N
    2000    ~
    3500    A
    5000    O
    
    where N=normal, ~=noise, A=AF, O=other, -=No signal

    MAJOR DEPENDICIES:
        bokeh
        pandas
        itertools
        helpers.py        helper functions written for this script
    
    OTHER MODULES:
        sys
        os

    TO RUN:
        bokeh serve --show AFAnnotator4
'''

#import numpy as np
import pandas as pd
#import time
#import datetime

import os
from os.path import dirname, join

from bokeh.models import DatetimeTickFormatter
from bokeh.plotting import figure 
from bokeh.palettes import Category10
from bokeh.io import output_notebook, show, output_file, curdoc
from bokeh.layouts import column, row, layout
from bokeh.models import ColumnDataSource, HoverTool, RadioButtonGroup, Span, LinearAxis, Range1d
from bokeh.layouts import widgetbox
from bokeh.models.widgets import Slider, RangeSlider, CheckboxGroup,  Button, TextInput, Paragraph, Slider
from bokeh.models.widgets import Panel, Tabs, Div
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
from bokeh.events import ButtonClick
from bokeh.models.ranges import Range1d

import sys

from helpers import *

################################## Miscellaneous functions ##################################
'''
####################################### Main Function #######################################
'''
def main():
    #path variables
    #in_path = '/mnt/data04/Conduit/afib/new_files/1hour/'
    #af_outpath = '/mnt/data04/Conduit/afib/AF_annotations/af_ann4/'
    in_path = join(dirname(__file__), "data_in/")
    af_outpath = join(dirname(__file__), "data_out/")
    #Miscellaneous variables
    colours = {'':'black','O':'blue','N':'green','~':'purple','A':'red'}
    #wf_classes = ['AF','Normal','Other','Noise','No Signal']
    wf_classes = ['AF', 'Not AF']
    #global variables remove if you can
    newECG = pd.DataFrame()
    df_ann = pd.DataFrame(columns=[0])

    #widgets to be used as necessary
    rdo_btn_wave_lbls = RadioButtonGroup(labels = wf_classes, active=2)
    date_range_slider = Slider(title="Date Range", step=10)
    table_source, table_columns = load_file_source(in_path, af_outpath)
    file_table = DataTable(source=table_source, columns=table_columns, width=800, height=600)
    pgph_file_loaded = Div(text="Select file from table.", width=1000,height=50)
    pgph_file_loaded.style = {"font-size": '1.2em', 'font-weight': 'bold', 'color': 'SteelBlue'}
    txt_processing = Div(text="Use slider to select segments, label by selecting the wave type and pressing 'Label'. Use the save to save when finished all annotations.",
        width=1000,height=30)
    txt_processing.style = {"font-size": '1.2em', 'font-weight': 'bold', 'color': 'SteelBlue', 'white-space': 'pre'}
    
    btn_lbl = Button(label='Label',button_type='success')
    btn_save = Button(label='Save',button_type='danger')
    btn_load_annotated_graph = Button(label='Load Annotated Graph',button_type='warning')

    #----------------------------- Functions ---------------------------------#
    
    ''' Callback function for the data table ColumnDataSource (table_source).
        Load the hd5 file based on the selected row in the data_table.
        Generate the output file path.
        Update the date range slider according to the new file (date_range_slider).
        Generate a plot of the hd5 ECG lead II data (wave_graph).
        Then combine all into a layout (graph_layout)
        Update the Tab Pane with this new layout.
        Returns: Nothing'''
    def callback_select_file_table(attr,old,new):
        global newECG, out_file
        #clear tabs graphs to reduce overhead
        output_tab.child.children = []
        sel_id = new
        txt_processing.text = "Use slider to select segments, label by selecting the wave type and pressing 'Label'. Use the save button to when done."
        txt_processing.style = {"font-size": '1.2em','color': 'SteelBlue'}
        wave_file_path = load_selected_file(table_source,sel_id)
        out_file = load_annotation_file(table_source, sel_id, af_outpath) #to be used for saving the file
        pgph_file_loaded.text = "Processing..."
        wave_hdfs, hdfs_keys = load_hd5_file(wave_file_path)
        print(hdfs_keys)
        newECG = (wave_hdfs.select(key='Waveforms').II).to_frame() #get lead II from waveforms)
        newECG.reset_index(inplace=True) #move datetime index to column and reset the index
        newECG.columns = ['date', 'II']
        wave_hdfs.close()
        #enable the buttons if disabled
        btn_save.disabled = False
        btn_lbl.disabled = False
        btn_load_annotated_graph.disabled = True
        #check if the file has already been annotated
        annotated = check_if_annotated(table_source, sel_id)
        if annotated == 'Yes':
            txt_processing.text = 'This file has already been annotated. If you save this file again you will overwrite previous data.'
            txt_processing.style = {"font-size": '1.2em','color': 'Red'}
            btn_load_annotated_graph.disabled = False
        #create figure
        print("*********************Creating Figure (in Callback File Select)")
        get_next_graph(0,newECG)
        pgph_file_loaded.text = "File loaded, navigate Label Data Tab to annotate lead II."


    ''' Using the AF annotation file, create a Bokeh figure with annotated data.
        Update the output_tab to show this figure.
        Disable some buttons to keep users on track. '''
    def load_output_graph():
        global newECG
        btn_save.disabled = True
        btn_lbl.disabled = True
        btn_load_annotated_graph.disabled = True
        txt_processing.text = 'Loading Plot...'
        df_AF = pd.read_hdf(out_file)
        noise, normal, other, af, nosig, notAF = load_annotations(0, df_AF.shape[0]-1, newECG, df_AF)
        output_graph = get_graph_annotated(noise, normal, other, af, nosig, notAF)
        output_tab.child.children = [output_graph]
        txt_processing.text = 'Plot loaded, navigate to "Final Annotated Graph" tab to view. &#10 If you save this file again you will overwrite previous data.'
        btn_save.disabled = False
        btn_lbl.disabled = False

    def get_next_graph(sind, df):
        length=20000#7200
        eind = sind+length
        if eind <= list(df.index)[-1] and sind < list(df.index)[-1]: #as long as the end and beginning are less than the end of the dataframe
            sub_df = df.iloc[sind:eind]
            sub_df = sub_df.set_index('date')
            del sub_df.index.name
            source = ColumnDataSource(sub_df)
            wave_graph = get_graph(source)
            start_span, end_span = add_span(source)
            wave_graph.add_layout(start_span)
            wave_graph.add_layout(end_span)
            start_rng = start_span.location
            end_rng = end_span.location
        elif eind < list(df.index)[-1] and sind < list(df.index)[-1]: #if the start is before but the end is after then just use the end of the dataframe
            sub_df = df.iloc[sind:list(df.index)[-1]]
            sub_df = sub_df.set_index('date')
            del sub_df.index.name
            source = ColumnDataSource(sub_df)
            wave_graph = get_graph(source)
            start_span, end_span = add_span(source)
            wave_graph.add_layout(start_span)
            wave_graph.add_layout(end_span)
            start_rng = start_span.location
            end_rng = end_span.location
        else:
            txt_processing.text = 'You have finished annotating this file.'
            return
        end_span.location = start_span.location
        #slider to change date range
        date_range_slider.start=start_rng
        date_range_slider.end=end_rng
        date_range_slider.value=start_rng
        date_range_slider.on_change('value',callback_date_time_slider)
        graph_layout = column(
            widgetbox([txt_processing,btn_load_annotated_graph,btn_save], width=250),
            widgetbox(Div(text="""<hr/>""",
                    style={'display':'block','height': '1px', 'border': '0', 'border-top': '1px solid #css',
                            'margin': '1em 0', 'padding': '0'}),
                    width=1400),
            widgetbox([rdo_btn_wave_lbls,btn_lbl], width=300),
            widgetbox(date_range_slider, width=1350),
            widgetbox(Div(text="""<hr/>""",
                    style={'display':'block','height': '1px', 'border': '0', 'border-top': '1px solid #css',
                            'margin': '1em 0', 'padding': '0'}),
                    width=1400),
            wave_graph
        )
        wf_tab.child.children = [graph_layout]

    ''' Use a ColumnDataSource to plot the ECG lead II waveform data in a line plot.
        Parameters: source a ColumnDataSource
        Returns: p a Bokeh figure '''
    def get_graph(source):
        p = figure(plot_width=1400, plot_height=500,x_axis_type='datetime', tools=['zoom_in','zoom_out', 'xpan', 'ypan'])
        date_range = source.data['II'][0:20000]
        p.y_range = Range1d(start=min(date_range)-1,end=max(date_range)+1)
        dt_axis_format = ["%d-%m-%Y %H:%M"]
        wf_x_axis = DatetimeTickFormatter(
                hours=dt_axis_format,
                days=dt_axis_format,
                months=dt_axis_format,
                years=dt_axis_format,
        )
        p.xaxis.formatter = wf_x_axis
        p.line(x='index', y='II', source=source,line_color='black', line_width=1)
        return p


    ''' Get the first and last time points from the ColumnDataSource (source).
        Utlizes tzlocal to add an offset which modifies the data.
        Returns integer timetuple value for the dates found: start, end '''
    def get_time(source):
        start = pd.to_datetime(min(source.data['index'])).timestamp()*1000
        end = pd.to_datetime(max(source.data['index'])).timestamp()*1000
        return start, end


    ''' Generate two Bokeh Spans based on the ColumnDataSource given (source).
        Spans are at the first and last datetimes in the source data.
        Parameters: source a ColumnDataSource
        Returns: Span, Span '''
    def add_span(source):
        start, end = get_time(source)
        # Start span represents the start of the area of interest
        start_span = Span(location=start,
                    dimension='height', line_color='green',
                    line_dash='dashed', line_width=3)
        # End span represents the end of the area of interest
        end_span = Span(location=end,
                    dimension='height', line_color='red',
                    line_dash='dashed', line_width=3)   
        return start_span, end_span


    ''' Callback function for Bokeh Slider, move the Spans on the specified graph (generated in callback_file_table) to the location specified by the Span.
        Returns: Nothing '''
    def callback_date_time_slider(attr, old, new):
        inds = get_spans()
        wf_tab.child.children[0].children[5].renderers[inds[1]].location = new


    ''' Navigate through the widgets on the wave_graph to find the spans
        Returns the widget indexes of the spans'''
    def get_spans():
        inds = []
        for x in range(len(wf_tab.child.children[0].children[5].renderers)):
            if isinstance(wf_tab.child.children[0].children[5].renderers[x],Span):
                inds.append(x)
        return inds

    ''' Callback function for btn_lbl.
        Get the location of the spans from the wave_graph, then call segment_and_label
        Return: Nothing '''
    def callback_btn_lbl():
        inds = get_spans()
        active = rdo_btn_wave_lbls.labels[rdo_btn_wave_lbls.active]
        start_span = wf_tab.child.children[0].children[5].renderers[inds[0]]
        end_span = wf_tab.child.children[0].children[5].renderers[inds[1]]
        segment_and_label(active, start_span.location, end_span.location)    
        
    ''' Function to get ECG data between two Spans (after modifying the timetuple to timestamp).
        Call apply_annotations using start and end indexes found.
        Modify the global df_ann variable.
        Update slider position (start to end), (end to start).
        Parameters: label a string (AF, Normal, Noise, Other), start a timpletuple integer, end a timetuple integer
        Return: nothing '''
    def segment_and_label(label, start, end):
        global newECG
        print("*********************Segmenting and Labelling")
        try:
            txt_processing.text = "Use slider to select segments, label by selecting the wave type and pressing 'Label'. Use the save button to when done."
            start_dt = pd.Timestamp(start/1000,unit='s')
            end_dt = pd.Timestamp(end/1000, unit='s')
            mask = (newECG['date'] > start_dt) & (newECG['date'] <= end_dt)
            df_sub = newECG.loc[mask] #apply mask
            indexes = list(df_sub.index) #get indexes
            s_ind = indexes[0]  #get first index
            e_ind = indexes[-1] #get last index
            apply_annotations(label,s_ind, e_ind, df_ann) #concatenate dataframe of annotations
            get_next_graph(e_ind, newECG)
        except IndexError:
            txt_processing.text = 'Indexing error. Advance slider.'

    ''' Function to apply annotations to a dataframe structured like that of Computing in Cardiology AF algorithm.
        Parameters: label a string (AF, Normal, Noise, Other), s_ind the index of the start datetime,
                    e_ind the index of the end datetime, df a pandas database to be appended to, columns= 'AF'
        Return: Nothing '''
    def apply_annotations(label, s_ind, e_ind, df):
        #data frame structure like this
        if label == 'AF':
            df.loc[s_ind,0] = 'A'
        elif label == 'Not AF':
            df.loc[s_ind,0] = 'nAF'
        elif label == 'Noise':
            df.loc[s_ind,0] = '~'
        elif label == 'Normal':
            df.loc[s_ind, 0] = 'N'
        elif label == 'Other':
            df.loc[s_ind,0] = 'O'
        elif label == 'No Signal':
            df.loc[s_ind,0] = '-'

    ''' Stream update to ColumnDataSource that the file has been annotated'''
    def mark_as_done(file_path):
        print("*********************Marking as Done")
        table_source = file_table.source
        name = os.path.splitext(os.path.basename(file_path))[0] #get file name
        ind = list(table_source.data['name']).index(name) #get index within the source
        patches = { 'annotated' : [ (ind, 'Yes') ] } #new data to update ColumnDataSource with
        table_source.patch(patches) #update - ***** THROWING ERROR - CHECK!!
        
        
    ''' Callback function for btn_save.
        Utilizes the out_file global variable for the path.
        Appends dataframe to output file. '''
    def callback_save_annotations():
        print("*********************Saving Annotations")
        txt_processing.style = {"font-size": '1.2em','color': 'Red'}
        print("Writting: ", out_file)
        txt_processing.text = 'Saving Annotations...'
        df_ann.to_hdf(out_file,key = 'AF',format='t')
        print("success!")
        btn_save.disabled = True
        btn_lbl.disabled = True
        mark_as_done(out_file)
        nrows = df_ann.shape[0]
        df_ann.drop(df_ann.index[:nrows], inplace=True) #clear dataframe for a new file to be loaded
        btn_load_annotated_graph.disabled = False
        txt_processing.style = {"font-size": '1.2em','color': 'SteelBlue'}
        txt_processing.text = '''Done. Click 'Load Annotated Graph' to view annotations or to "File Management" to select new file to anntoate. You will need to reload this file to make changes.'''

    ''' Load annotations from AF formatted hdf file. '''
    def load_annotations(start,end,df,df_AF):
        # Initialize empty dataframes
        noise = pd.DataFrame()
        normal = pd.DataFrame()
        other = pd.DataFrame()
        af = pd.DataFrame()
        nosig = pd.DataFrame()
        notAF = pd.DataFrame()
        # Read annotations
        for n in range(start,end):
            df_temp = df.iloc[df_AF.index[n]:df_AF.index[n+1]]
            df_temp.index = list(df_temp['date'])
            df_temp.drop(columns='date')
            value = df_AF.iloc[n, 0]
            if value == '~':
                noise = noise.append(df_temp)
            elif value == 'N':
                normal = normal.append(df_temp)
            elif value == 'O':
                other = other.append(df_temp)
            elif value == 'A':
                af = af.append(df_temp)
            elif value == '-':
                nosig = nosig.append(df_temp)
            elif value == 'nAF':
                notAF = notAF.append(df_temp)
        #add the last labelled section (end+1) to end of df
        df_temp = df.iloc[df_AF.index[end]:df.index[-1]]
        df_temp.index = list(df_temp['date'])
        df_temp.drop(columns='date')
        value = df_AF.iloc[end, 0]
        if value == '~':
            noise = noise.append(df_temp)
        elif value == 'N':
            normal = normal.append(df_temp)
        elif value == 'O':
            other = other.append(df_temp)
        elif value == 'A':
            af = af.append(df_temp)
        elif value == '-':
            nosig = nosig.append(df_temp)
        elif value == 'nAF':
            notAF = notAF.append(df_temp)  
        return noise, normal, other, af, nosig, notAF

    ''' Create Bokeh figure from dataframes af, normal, other and noise. '''
    def get_graph_annotated(noise, normal, other, af, nosig, notAF):
        p = figure(plot_width=1400, plot_height=500,x_axis_type='datetime',
                tools=['box_zoom', 'wheel_zoom', 'pan','reset','crosshair'])
        # plot color coded waves (if they exist)
        if noise.empty is False: p.line(x='index', y='II', source=noise, color = 'blue',legend = 'Noise')
        if normal.empty is False: p.line(x='index', y='II', source=normal, color = 'green',legend = 'Normal')
        if other.empty is False: p.line(x='index', y='II', source=other, color = 'purple',legend = 'Other')
        if af.empty is False: p.line(x='index',y='II',source=af, color='red',legend = 'AF')
        if nosig.empty is False: p.line(x='index',y='II',source=nosig, color='black',legend = 'No Signal')
        if notAF.empty is False: p.line(x='index',y='II',source=notAF, color='grey',legend = 'No Signal')
        dt_axis_format = ["%d-%m-%Y %H:%M"]
        wf_x_axis = DatetimeTickFormatter(
                hours=dt_axis_format,
                days=dt_axis_format,
                months=dt_axis_format,
                years=dt_axis_format,
        )
        p.xaxis.formatter = wf_x_axis
        return p

    ############################## Assign Callbacks ##########################################
    #table_source.on_change('selected', callback_select_file_table) #assign callback
    table_source.selected.on_change('indices', callback_select_file_table)
    btn_lbl.on_click(callback_btn_lbl) 
    btn_save.on_click(callback_save_annotations)
    btn_load_annotated_graph.on_click(load_output_graph)


    ################################## Load Document ##########################################
    ####layouts####
    file_layout = column(widgetbox(pgph_file_loaded,file_table,width=1000))
    col_waveforms = column(name="figures", sizing_mode='scale_width')
    col_output = column(name="output", sizing_mode='scale_width')


    ###tabs###
    wf_tab = Panel(child=col_waveforms, title='Label Data')
    file_tab = Panel(child=file_layout, title='File Management')
    output_tab = Panel(child=col_output, title='Final Annotated Graph')
    tab_pane = Tabs(tabs=[file_tab,wf_tab,output_tab],width=1000)
   

    ###combine into document####   
    curdoc().add_root(column(tab_pane))
    curdoc().title = "AF Annotator 4"


##############################Run main function############################
main()
