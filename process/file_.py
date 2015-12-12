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
import nd2reader
import datetime

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
    metadata=dict()
    ext=os.path.splitext(filename)[1]
    if ext in ['.tif', '.stk', '.tiff']:
        Tiff=tifffile.TiffFile(filename)
        try:
            metadata=Tiff[0].image_description
            metadata = txt2dict(metadata)
        except AttributeError:
            metadata=dict()
        A=Tiff.asarray().astype(g.m.settings['internal_data_type'])
        Tiff.close()
        axes=[tifffile.AXES_LABELS[ax] for ax in Tiff.pages[0].axes]
        print("Original Axes = {}".format(axes)) #sample means RBGA, plane means frame, width means X, height means Y
        if Tiff.is_rgb:
            if A.ndim==3: # still color image.  [X, Y, RBGA]
                A=np.transpose(A,(1,0,2))
            elif A.ndim==4: # movie in color.  [T, X, Y, RGBA]
                A=np.transpose(A,(0,2,1,3))
        else:
            if A.ndim==2: # black and white still image [X,Y]
                A=np.transpose(A,(1,0))
            elif A.ndim==3: #black and white movie [T,X,Y]
                A=np.transpose(A,(0,2,1)) # This keeps the x and y the same as in FIJI. 
            elif A.ndim==4:
                if axes[3]=='sample' and A.shape[3]==1:
                    A=np.squeeze(A) #this gets rid of the meaningless 4th dimention in .stk files
                    A=np.transpose(A,(0,2,1))
        metadata['is_rgb']=Tiff[0].is_rgb
    elif ext=='.nd2':
        nd2 = nd2reader.Nd2(filename)
        mt,mx,my=len(nd2),nd2.width,nd2.height
        A=np.zeros((mt,mx,my))
        for frame in np.arange(mt):
            A[frame]=nd2[frame].T
        metadata['channels']=nd2.channels
        metadata['date']=nd2.date
        metadata['fields_of_view']=nd2.fields_of_view
        metadata['frames']=nd2.frames
        metadata['height']=nd2.height
        metadata['width']=nd2.width
        metadata['z_levels']=nd2.z_levels
    else:
        print('Could not open %s' % filename)
        return
    g.m.statusBar().showMessage('{} successfully loaded ({} s)'.format(os.path.basename(filename), time.time()-t))
    g.m.settings['filename']=filename
    commands = ["open_file('{}')".format(filename)]
    newWindow=Window(A,os.path.basename(filename),filename,commands,metadata)
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

def JSONhandler(obj):
    if isinstance(obj,datetime.datetime):
        return obj.isoformat()
    else:
        json.JSONEncoder().default(obj)
    
def save_file(filename):
    if os.path.dirname(filename)=='': #if the user didn't specify a directory
        directory=os.path.normpath(os.path.dirname(g.m.settings['filename']))
        filename=os.path.join(directory,filename)
    g.m.statusBar().showMessage('Saving {}'.format(os.path.basename(filename)))
    A=g.m.currentWindow.image.astype(g.m.settings['data_type'])
    metadata=g.m.currentWindow.metadata
    metadata=json.dumps(metadata,default=JSONhandler)
    if len(A.shape)==3:
        A=np.transpose(A,(0,2,1)) # This keeps the x and the y the same as in FIJI
    elif len(A.shape)==2:
        A=np.transpose(A,(1,0))
    tifffile.imsave(filename, A, description=metadata) #http://stackoverflow.com/questions/20529187/what-is-the-best-way-to-save-image-metadata-alongside-a-tif-with-python
    g.m.statusBar().showMessage('Successfully saved {}'.format(os.path.basename(filename)))

def save_current_frame(filename):
    if os.path.dirname(filename)=='': #if the user didn't specify a directory
        directory=os.path.normpath(os.path.dirname(g.m.settings['filename']))
        filename=os.path.join(directory,filename)
    g.m.statusBar().showMessage('Saving {}'.format(os.path.basename(filename)))
    A=np.average(g.m.currentWindow.image, 0).astype(g.m.settings['data_type'])
    metadata=json.dumps(g.m.currentWindow.metadata)
    if len(A.shape)==3:
        A = A[g.m.currentWindow.currentIndex]
        A=np.transpose(A,(0,2,1)) # This keeps the x and the y the same as in FIJI
    elif len(A.shape)==2:
        A=np.transpose(A,(1,0))
    tifffile.imsave(filename, A, description=metadata) #http://stackoverflow.com/questions/20529187/what-is-the-best-way-to-save-image-metadata-alongside-a-tif-with-python
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
    A=g.m.currentWindow.image
    if len(A.shape)<3:
        g.m.statusBar().showMessage('Movie not the right shape for saving.')
        return
    try:
        exporter = pg.exporters.ImageExporter(g.m.currentWindow.imageview.view)
    except TypeError:
        exporter = pg.exporters.ImageExporter.ImageExporter(g.m.currentWindow.imageview.view)
        
    nFrames=len(A)
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