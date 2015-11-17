# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 14:43:19 2014

@author: Kyle Ellefsen
"""
from __future__ import (absolute_import, division,print_function, unicode_literals)
from future.builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, open, pow, round, super, filter, map, zip)

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pyqtgraph as pg
import pyqtgraph.exporters
import time
import os.path
import numpy as np
from skimage.io import imread, imsave
from window import Window
import global_vars as g
from PyQt4 import uic
import codecs
import shutil, subprocess
import tifffile
import json
import re

__all__ = ['open_file_gui','open_file','save_file_gui','save_file','save_movie','load_metadata','save_metadata','close', 'load_points', 'save_points', 'change_internal_data_type_gui', 'save_current_frame']

def open_file_gui(func, filetypes, prompt='Open File'):
    filename=g.m.settings['filename']
    if filename is not None and os.path.isfile(filename):
        filename= QFileDialog.getOpenFileName(g.m, prompt, filename, filetypes)
    else:
        filename= QFileDialog.getOpenFileName(g.m, prompt, '', filetypes)
    filename=str(filename)
    if filename != '':
        func(filename)
    else:
        g.m.statusBar().showMessage('No File Selected')

def save_file_gui(func, filetypes, prompt = 'Save File'):
    filename=g.m.settings['filename']
    try:
        directory=os.path.dirname(filename)
    except:
        directory=''
    if filename is not None and directory != '':
        filename= QFileDialog.getSaveFileName(g.m, prompt, directory, filetypes)
    else:
        filename= QFileDialog.getSaveFileName(g.m, prompt, filetypes)
    filename=str(filename)
    if filename != '':
        func(filename)
    else:
        g.m.statusBar().showMessage('Save Cancelled')

def save_roi_traces(filename):
    g.m.statusBar().showMessage('Saving traces to {}'.format(os.path.basename(filename)))
    to_save = [roi.getTrace() for roi in g.m.currentWindow.rois]
    np.savetxt(filename, np.transpose(to_save), header='\t'.join(['ROI %d' % i for i in range(len(to_save))]), fmt='%.4f', delimiter='\t', comments='')
    g.m.settings['filename'] = filename
    g.m.statusBar().showMessage('Successfully saved traces to {}'.format(os.path.basename(filename)))

            
def open_file(filename):
    g.m.statusBar().showMessage('Loading {}'.format(os.path.basename(filename)))
    t=time.time()
    Tiff=tifffile.TiffFile(filename)
    try:
        metadata=Tiff[0].image_description
        metadata = txt2dict(metadata)
    except AttributeError:
        metadata=dict()
    tif=Tiff.asarray().astype(g.m.settings['internal_data_type'])
    Tiff.close()
    #tif=imread(filename,plugin='tifffile').astype(g.m.settings['internal_data_type'])
    if len(tif.shape)>3: # WARNING THIS TURNS COLOR movies TO BLACK AND WHITE BY AVERAGING ACROSS THE THREE CHANNELS
        if 'channels' in metadata.keys() and 'ImageJ' in metadata.keys():
            tif=np.transpose(tif,(0,3,2,1))
        tif=np.mean(tif,3)
    tif=np.squeeze(tif) #this gets rid of the meaningless 4th dimention in .stk files
    if len(tif.shape)==3: #this could either be a movie or a colored still frame
        if tif.shape[2]==3: #this is probably a colored still frame
            tif=np.mean(tif,2)
            tif=np.transpose(tif,(1,0)) # This keeps the x and y the same as in FIJI. 
        else:
            tif=np.transpose(tif,(0,2,1)) # This keeps the x and y the same as in FIJI. 
    elif len(tif.shape)==2: # I haven't tested whether this preserved the x y and keeps it the same as in FIJI.  TEST THIS!!
        tif=np.transpose(tif,(1,0))
    g.m.statusBar().showMessage('{} successfully loaded ({} s)'.format(os.path.basename(filename), time.time()-t))
    g.m.settings['filename']=filename
    commands = ["open_file('{}')".format(filename)]
    newWindow=Window(tif,os.path.basename(filename),filename,commands,metadata)
    return newWindow
    
def change_internal_data_type_gui():
    change=uic.loadUi("gui/save.ui")
    change.setWindowTitle('Change internal data type')
    old_dtype=np.dtype(g.m.settings['internal_data_type'])
    print(old_dtype)
    idx=change.data_type.findText(str(old_dtype))
    change.data_type.setCurrentIndex(idx)
    change.accepted.connect(lambda: g.m.settings.setInternalDataType(np.dtype(str(change.data_type.currentText()))))
    change.show()
    g.m.dialog=change
        
def save_file(filename):
    if os.path.dirname(filename)=='': #if the user didn't specify a directory
        directory=os.path.normpath(os.path.dirname(g.m.settings['filename']))
        filename=os.path.join(directory,filename)
    g.m.statusBar().showMessage('Saving {}'.format(os.path.basename(filename)))
    tif=g.m.currentWindow.image.astype(g.m.settings['data_type'])
    metadata=json.dumps(g.m.currentWindow.metadata)
    if len(tif.shape)==3:
        tif=np.transpose(tif,(0,2,1)) # This keeps the x and the y the same as in FIJI
    elif len(tif.shape)==2:
        tif=np.transpose(tif,(1,0))
    tifffile.imsave(filename, tif, description=metadata) #http://stackoverflow.com/questions/20529187/what-is-the-best-way-to-save-image-metadata-alongside-a-tif-with-python
    g.m.statusBar().showMessage('Successfully saved {}'.format(os.path.basename(filename)))

def save_current_frame(filename):
    if os.path.dirname(filename)=='': #if the user didn't specify a directory
        directory=os.path.normpath(os.path.dirname(g.m.settings['filename']))
        filename=os.path.join(directory,filename)
    g.m.statusBar().showMessage('Saving {}'.format(os.path.basename(filename)))
    tif=np.average(g.m.currentWindow.image, 0).astype(g.m.settings['data_type'])
    metadata=json.dumps(g.m.currentWindow.metadata)
    if len(tif.shape)==3:
        tif = tif[g.m.currentWindow.currentIndex]
        tif=np.transpose(tif,(0,2,1)) # This keeps the x and the y the same as in FIJI
    elif len(tif.shape)==2:
        tif=np.transpose(tif,(1,0))
    tifffile.imsave(filename, tif, description=metadata) #http://stackoverflow.com/questions/20529187/what-is-the-best-way-to-save-image-metadata-alongside-a-tif-with-python
    g.m.statusBar().showMessage('Successfully saved {}'.format(os.path.basename(filename)))    

def save_points(filename):
    g.m.statusBar().showMessage('Saving Points in {}'.format(os.path.basename(filename)))
    p_out=[]
    p_in=g.m.currentWindow.scatterPoints
    for t in np.arange(len(p_in)):
        for p in p_in[t]:
            p_out.append(np.array([t,p[0],p[1]]))
    p_out=np.array(p_out)
    np.savetxt(filename,p_out)
    g.m.statusBar().showMessage('Successfully saved {}'.format(os.path.basename(filename)))
        
def load_points(filename):
    g.m.statusBar().showMessage('Loading points from {}'.format(os.path.basename(filename)))
    pts=np.loadtxt(filename)
    for pt in pts:
        t=int(pt[0])
        if g.m.currentWindow.mt==1:
            t=0
        g.m.currentWindow.scatterPoints[t].append([pt[1],pt[2]])
    t=g.m.currentWindow.currentIndex
    g.m.currentWindow.scatterPlot.setPoints(pos=g.m.currentWindow.scatterPoints[t])
    g.m.statusBar().showMessage('Successfully loaded {}'.format(os.path.basename(filename)))
        
def save_movie(filename):
    '''
    Once you've exported all of the frames you wanted, open a command line and run the following:
    
        ffmpeg -r 100 -i %03d.jpg output.mp4
        
    -r: framerate
    -i: input files.  
    %03d: The files have to be numbered 001.jpg, 002.jpg... etc.
    '''
    tif=g.m.currentWindow.image
    if len(tif.shape)<3:
        g.m.statusBar().showMessage('Movie not the right shape for saving.')
        return
    try:
        exporter = pg.exporters.ImageExporter(g.m.currentWindow.imageview.view)
    except TypeError:
        exporter = pg.exporters.ImageExporter.ImageExporter(g.m.currentWindow.imageview.view)
        
    nFrames=len(tif)
    tmpdir=os.path.join(os.path.dirname(g.m.settings.config_file),'tmp')
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    os.mkdir(tmpdir)
    for i in np.arange(0,nFrames):
        g.m.currentWindow.imageview.timeLine.setPos(i)
        exporter.export(os.path.join(tmpdir,'{:03}.jpg'.format(i)))
    olddir=os.getcwd()
    os.chdir(tmpdir)
    subprocess.call(['ffmpeg', '-r', '50', '-i', '%03d.jpg', '-vf','scale=trunc(iw/2)*2:trunc(ih/2)*2', 'output.mp4'])
    os.rename('output.mp4',filename)
    os.chdir(olddir)
    g.m.statusBar().showMessage('Successfully saved movie as {}.'.format(os.path.basename(filename)))
    
def txt2dict(metadata):
    meta=dict()
    try:
        metadata=json.loads(metadata.decode('utf-8'))
        return metadata
    except ValueError: #if the metadata isn't in JSON
        pass
    for line in metadata.splitlines():
        line=re.split('[:=]',line.decode())
        if len(line)==1:
            meta[line[0]]=''
        else:
            meta[line[0].lstrip().rstrip()]=line[1].lstrip().rstrip()
    return meta
    
def load_metadata(filename=None):
    '''This function loads the .txt file corresponding to a file into a dictionary
    The .txt is a file which includes database connection information'''
    meta=dict()
    if filename is None:
        filename=os.path.splitext(g.m.settings['filename'])[0]+'.txt'
    BOM = codecs.BOM_UTF8.decode('utf8')
    if not os.path.isfile(filename):
        print("'"+filename+"' is not a file.")
        return dict()
    with codecs.open(filename, encoding='utf-8') as f:
        for line in f:
            line = line.lstrip(BOM)
            line=line.split('=')
            meta[line[0].lstrip().rstrip()]=line[1].lstrip().rstrip()
    for k in meta.keys():
        if meta[k].isdigit():
            meta[k]=int(meta[k])
        else:
            try:
                meta[k]=float(meta[k])
            except ValueError:
                pass
    return meta
    
def save_metadata(meta):
    filename=os.path.splitext(g.m.settings['filename'])[0]+'.txt'
    f=open(filename, 'w')
    text=''
    for item in meta.items():
        text+="{}={}\n".format(item[0],item[1])
    f.write(text)
    f.close()
    
def close(windows=None):
    '''Will close a window or a set of windows.  Takes several types as its argument:
        | 'all' (str) -- closes all windows
        | windows (list) - closes each window in the list
        | (Window) - closes individual window
        | (None) - closes current window
    '''
    if isinstance(windows,basestring):
        if windows=='all':
            windows=[window for window in g.m.windows]
            for window in windows:
                window.close()
    elif isinstance(windows,list):
        for window in windows:
            if isinstance(window,Window):
                window.close()
    elif isinstance(windows,Window):
        windows.close()
    elif windows is None:
        if g.m.currentWindow is not None:
            g.m.currentWindow.close()