
from qtpy.QtWidgets import qApp
from qtpy import uic
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor
import pyqtgraph as pg
import pyqtgraph.exporters
import time, codecs, shutil, subprocess, json, re, nd2reader, datetime
import os.path
import numpy as np
from skimage.io import imread, imsave
from flika.window import Window
import flika.global_vars as g
from flika.core import tifffile
from flika.app.terminal_widget import ScriptEditor
from flika.app.BaseProcess import BaseDialog
from flika.utils import getOpenFileName, getSaveFileName


__all__ = ['open_file_gui', 'open_file', 'save_file_gui', 'save_file', 'save_movie', 'save_movie_gui', 'load_metadata','save_metadata', 'close', 'load_points', 'save_points', 'save_current_frame', 'save_recent_file']

def save_recent_file(fname):
    if fname in g.settings['recent_files']:
        g.settings['recent_files'].remove(fname)
    if os.path.exists(fname):
        g.settings['recent_files'].append(fname)
        if len(g.settings['recent_files']) > 8:
            g.settings['recent_files'] = g.settings['recent_files'][-8:]
    return fname

def open_file_gui(func, filetypes, prompt='Open File', kargs={}):
    '''
    Open a file selection dialog to pass to open_file

    Parameters:
        | func (function) -- once the file is loaded, run this function with the data array as the first parameter
        | filetypes (str) -- QFileDialog representation of acceptable filetypes eg (Text Files (\*.txt);;Images(\*.tif, \*.stk, \*.nd2))
        | prompt (str) -- prompt shown at the top of the dialog
        | kargs (dict) -- any excess arguments to be passed to func
    '''
    filename=g.settings['filename'] if g.settings['filename'] != None and os.path.isfile(g.settings['filename']) else ''
    filename=getOpenFileName(g.m, prompt, filename, filetypes)

    if filename != '':
        save_recent_file(filename)
        return func(filename, **kargs)
    else:
        g.m.statusBar().showMessage('No File Selected')

def save_file_gui(func, filetypes, prompt = 'Save File', kargs={}):
    '''
    Open a dialog to choose a filename to save to via save_file

    Parameters:
        | func (function) -- once the file is selected, run this function with the data array as the first parameter
        | filetypes (str) -- QFileDialog representation of acceptable filetypes eg (Text Files (\*.txt);;Images(\*.tif, \*.stk, \*.nd2))
        | prompt (str) -- prompt shown at the top of the dialog
        | kargs (dict) -- any excess arguments to be passed to func
    '''
    filename=g.settings['filename']
    try:
        directory=os.path.dirname(filename)
    except:
        directory=''
    filename= getSaveFileName(g.m, prompt, initial=directory, filters=filetypes)
    
    if filename != '':
        func(filename, **kargs)
    else:
        g.m.statusBar().showMessage('Save Cancelled')

def save_roi_traces(filename):
    g.m.statusBar().showMessage('Saving traces to {}'.format(os.path.basename(filename)))
    to_save = [roi.getTrace() for roi in g.m.currentWindow.rois]
    np.savetxt(filename, np.transpose(to_save), header='\t'.join(['ROI %d' % i for i in range(len(to_save))]), fmt='%.4f', delimiter='\t', comments='')
    g.settings['filename'] = filename
    g.m.statusBar().showMessage('Successfully saved traces to {}'.format(os.path.basename(filename)))

def get_metadata_tiff(Tiff):
    metadata = {}
    if hasattr(Tiff[0], 'is_micromanager') and Tiff[0].is_micromanager:
        imagej_tags_unpacked = {}
        if hasattr(Tiff[0],'imagej_tags'):
            imagej_tags = Tiff[0].imagej_tags
            imagej_tags['info']
            imagej_tags_unpacked = json.loads(imagej_tags['info'])
        micromanager_metadata = Tiff[0].tags['micromanager_metadata']
        metadata = {**micromanager_metadata.value, **imagej_tags_unpacked}
        if 'Frames' in metadata and metadata['Frames'] > 1:
            timestamps = [c.tags['micromanager_metadata'].value['ElapsedTime-ms'] for c in Tiff]
            metadata['timestamps'] = timestamps
            metadata['timestamp_units'] = 'ms'
        keys_to_remove = ['NextFrame', 'ImageNumber', 'Frame', 'FrameIndex']
        for key in keys_to_remove:
            metadata.pop(key)
    else:
        try:
            metadata = Tiff[0].image_description
            metadata = txt2dict(metadata)
        except AttributeError:
            metadata = dict()
    metadata['is_rgb'] = Tiff[0].is_rgb
    return metadata

def get_metadata_nd2(nd2):
    metadata = dict()
    metadata['channels'] = nd2.channels
    metadata['date'] = nd2.date
    metadata['fields_of_view'] = nd2.fields_of_view
    metadata['frames'] = nd2.frames
    metadata['height'] = nd2.height
    metadata['width'] = nd2.width
    metadata['z_levels'] = nd2.z_levels
    return metadata

def open_file(filename=None):
        """ open_file(filename)
        Opens an image or movie file (.tif, .stk, .nd2) into a newWindow.
        Or opens a script (.py, .txt)
        
        Parameters:
            | filename (str) -- Address of file to open. If no filename is provided, the last opened file is used.
        Returns:
            newWindow
        """
        if filename is None:
            filename=g.settings['filename']
            if filename is None:
                g.alert('No filename selected')
                return
        if filename not in g.settings['recent_files']:
            save_recent_file(filename)
        g.m.statusBar().showMessage('Loading {}'.format(os.path.basename(filename)))
        t=time.time()       
        metadata=dict()     
        ext = os.path.splitext(filename)[1]     
        if ext in ['.tif', '.stk', '.tiff', '.ome']:        
            try:        
                Tiff = tifffile.TiffFile(filename)      
            except Exception as s:      
                g.alert("Unable to open {}. {}".format(filename, s))        
                return None     
            metadata = get_metadata_tiff(Tiff)      
            A=Tiff.asarray()#.astype(g.settings['internal_data_type'])      
            Tiff.close()        
            axes=[tifffile.AXES_LABELS[ax] for ax in Tiff.pages[0].axes]       
            #print("Original Axes = {}".format(axes)) #sample means RBGA, plane means frame, width means X, height means Y      
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
        elif ext=='.nd2':
            nd2 = nd2reader.Nd2(filename)
            mt,mx,my=len(nd2),nd2.width,nd2.height
            A=np.zeros((mt,mx,my))
            percent = 0
            for frame in range(mt):
                A[frame]=nd2[frame].T
                if percent<int(100*float(frame)/mt):
                    percent=int(100*float(frame)/mt)
                    g.m.statusBar().showMessage('Loading file {}%'.format(percent))
                    qApp.processEvents()
            metadata = get_metadata_nd2(nd2)
        elif ext == '.py' or ext == '.txt':
            ScriptEditor.importScript(filename)
            return
        else:
            msg = "Could not open.  Filetype for '{}' not recognized".format(filename)      
            g.alert(msg)        
            if filename in g.settings['recent_files']:      
                g.settings['recent_files'].remove(filename)     
            return      
        g.m.statusBar().showMessage('{} successfully loaded ({} s)'.format(os.path.basename(filename), time.time()-t))      
        g.settings['filename']=filename     
        commands = ["open_file('{}')".format(filename)]     
        newWindow=Window(A,os.path.basename(filename),filename,commands,metadata)
        return newWindow

def JSONhandler(obj):
    if isinstance(obj,datetime.datetime):
        return obj.isoformat()
    else:
        json.JSONEncoder().default(obj)
    
def save_file(filename):
    """ save_file(filename)
    Save the image in the currentWindow to a .tif file.
    
    Parameters:
        | filename (str) -- Address to save the video to.
    """
    if os.path.dirname(filename)=='': #if the user didn't specify a directory
        directory=os.path.normpath(os.path.dirname(g.settings['filename']))
        filename=os.path.join(directory,filename)
    g.m.statusBar().showMessage('Saving {}'.format(os.path.basename(filename)))
    A=g.currentWindow.image#.astype(g.settings['internal_data_type'])
    metadata=g.currentWindow.metadata
    try:
        metadata=json.dumps(metadata,default=JSONhandler)
    except TypeError as e:
        msg = "Error saving metadata.\n{}\nContinuing to save file".format(e)
        g.alert(msg)

    if len(A.shape)==3:
        A=np.transpose(A,(0,2,1)) # This keeps the x and the y the same as in FIJI
    elif len(A.shape)==2:
        A=np.transpose(A,(1,0))
    tifffile.imsave(filename, A, description=metadata) #http://stackoverflow.com/questions/20529187/what-is-the-best-way-to-save-image-metadata-alongside-a-tif-with-python
    g.m.statusBar().showMessage('Successfully saved {}'.format(os.path.basename(filename)))

def save_current_frame(filename):
    """ save_current_frame(filename)
    Save the current single frame image of the currentWindow to a .tif file.
    
    Parameters:
        | filename (str) -- Address to save the frame to.
    """
    if os.path.dirname(filename)=='': #if the user didn't specify a directory
        directory=os.path.normpath(os.path.dirname(g.settings['filename']))
        filename=os.path.join(directory,filename)
    g.m.statusBar().showMessage('Saving {}'.format(os.path.basename(filename)))
    A=np.average(g.currentWindow.image, 0)#.astype(g.settings['internal_data_type'])
    metadata=json.dumps(g.currentWindow.metadata)
    if len(A.shape)==3:
        A = A[g.currentWindow.currentIndex]
        A=np.transpose(A,(0,2,1)) # This keeps the x and the y the same as in FIJI
    elif len(A.shape)==2:
        A=np.transpose(A,(1,0))
    tifffile.imsave(filename, A, description=metadata) #http://stackoverflow.com/questions/20529187/what-is-the-best-way-to-save-image-metadata-alongside-a-tif-with-python
    g.m.statusBar().showMessage('Successfully saved {}'.format(os.path.basename(filename)))    

def save_points(filename):
    g.m.statusBar().showMessage('Saving Points in {}'.format(os.path.basename(filename)))
    p_out=[]
    p_in=g.currentWindow.scatterPoints
    for t in np.arange(len(p_in)):
        for p in p_in[t]:
            p_out.append(np.array([t,p[0],p[1]]))
    p_out=np.array(p_out)
    np.savetxt(filename,p_out)
    g.m.statusBar().showMessage('Successfully saved {}'.format(os.path.basename(filename)))
        
def load_points(filename):
    g.m.statusBar().showMessage('Loading points from {}'.format(os.path.basename(filename)))
    pts=np.loadtxt(filename)
    nCols = pts.shape[1]
    pointSize = g.settings['point_size']
    pointColor = QColor(g.settings['point_color'])
    if nCols == 3:
        for pt in pts:
            t=int(pt[0])
            if g.currentWindow.mt==1:
                t=0
            g.currentWindow.scatterPoints[t].append([pt[1],pt[2], pointColor, pointSize])
        t=g.currentWindow.currentIndex
        g.currentWindow.scatterPlot.setPoints(pos=g.currentWindow.scatterPoints[t])
    elif nCols == 2:
        t = 0
        for pt in pts:
            g.currentWindow.scatterPoints[t].append([pt[0], pt[1], pointColor, pointSize])
        t = g.currentWindow.currentIndex
        g.currentWindow.scatterPlot.setPoints(pos=g.currentWindow.scatterPoints[t])
    g.m.statusBar().showMessage('Successfully loaded {}'.format(os.path.basename(filename)))

def save_movie_gui():
    rateSpin = pg.SpinBox(value=50, bounds=[1, 1000], suffix='fps', int=True, step=1)
    rateDialog = BaseDialog([{'string': 'Framerate', 'object': rateSpin}],'Save Movie', 'Set the framerate')
    rateDialog.accepted.connect(lambda : save_file_gui(save_movie, "Movies (*.mp4)", "Save movie to .mp4 file", kargs={'rate': rateSpin.value()}))
    g.dialogs.append(rateDialog)
    rateDialog.show()

def save_movie(filename, rate):
    ''' save_movie(filename)
    Saves the currentWindow video as a .mp4 movie by joining .jpg frames together

    Parameters:
        | filename (str) -- Address to save the movie to, with .mp4

    Notes:
        | Once you've exported all of the frames you wanted, open a command line and run the following:
        |   ffmpeg -r 100 -i %03d.jpg output.mp4
        | -r: framerate
        | -i: input files.  
        | %03d: The files have to be numbered 001.jpg, 002.jpg... etc.
    '''
    #http://ffmpeg.org/releases/ffmpeg-2.8.4.tar.bz2
    win = g.currentWindow
    A = win.image
    if len(A.shape)<3:
        g.alert('Movie not the right shape for saving.')
        return
    try:
        exporter = pg.exporters.ImageExporter(win.imageview.view)
    except TypeError:
        exporter = pg.exporters.ImageExporter.ImageExporter(win.imageview.view)
        
    nFrames = len(A)
    tmpdir = os.path.join(os.path.dirname(g.settings.config_file),'tmp')
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    os.mkdir(tmpdir)
    win.top_left_label.hide()
    for i in np.arange(0,nFrames):
        win.setIndex(i)
        exporter.export(os.path.join(tmpdir,'{:03}.jpg'.format(i)))
        qApp.processEvents()
    win.top_left_label.show()
    olddir = os.getcwd()
    os.chdir(tmpdir)
    subprocess.call(['ffmpeg', '-r', '%d' % rate, '-i', '%03d.jpg', '-vf','scale=trunc(iw/2)*2:trunc(ih/2)*2', 'output.mp4'])
    os.rename('output.mp4', filename)
    os.chdir(olddir)
    g.m.statusBar().showMessage('Successfully saved movie as {}.'.format(os.path.basename(filename)))

    
def load_metadata(filename=None):
    '''This function loads the .txt file corresponding to a file into a dictionary
    The .txt is a file which includes database connection information'''
    meta=dict()
    if filename is None:
        filename=os.path.splitext(g.settings['filename'])[0]+'.txt'
    BOM = codecs.BOM_UTF8.decode('utf8')
    if not os.path.isfile(filename):
        g.alert("'"+filename+"' is not a file.")
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

def save_metadata(meta):
    filename=os.path.splitext(g.settings['filename'])[0]+'.txt'
    f=open(filename, 'w')
    text=''
    for item in meta.items():
        text+="{}={}\n".format(item[0],item[1])
    f.write(text)
    f.close()
    
def close(windows=None):
    '''
    Will close a window or a set of windows.

    Values for windows:
        | 'all' (str) -- closes all windows
        | windows (list) - closes each window in the list
        | (Window) - closes individual window
        | (None) - closes current window
    '''
    if isinstance(windows, str):
        if windows == 'all':
            windows = [window for window in g.m.windows]
            for window in windows:
                window.close()
    elif isinstance(windows, list):
        for window in windows:
            if isinstance(window,Window):
                window.close()
    elif isinstance(windows,Window):
        windows.close()
    elif windows is None:
        if g.currentWindow is not None:
            g.currentWindow.close()