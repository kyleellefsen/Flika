# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 14:17:38 2014
updated 2015.01.27
@author: Kyle Ellefsen
"""
from __future__ import (absolute_import, division,print_function, unicode_literals)
from dependency_check import check_dependencies
check_dependencies('future','leastsqbound','pyqtgraph','openpyxl', 'PyQt4','numpy','scipy','scikit-image','nd2reader')
from future.builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, open, pow, round, super, filter, map, zip)
import time
tic=time.time()
import os, sys
if sys.version_info.major == 2:
    reload(sys)
    sys.setdefaultencoding('utf8') #http://stackoverflow.com/questions/21129020/how-to-fix-unicodedecodeerror-ascii-codec-cant-decode-byte
    sys.path.insert(0, os.path.expanduser(r'~\Documents\Github\pyqtgraph'))
import numpy as np
from PyQt4.QtCore import * # Qt is Nokias GUI rendering code written in C++.  PyQt4 is a library in python which binds to Qt
from PyQt4.QtGui import *
from PyQt4.QtCore import pyqtSignal as Signal
from pyqtgraph import plot, show
import pyqtgraph as pg
import global_vars as g
from window import Window

from process.stacks import deinterleave, trim, zproject, image_calculator, pixel_binning, frame_binning, resize
from process.math_ import multiply, subtract, power, ratio, absolute_value, subtract_trace
from process.filters import gaussian_blur, butterworth_filter,boxcar_differential_filter, wavelet_filter, difference_filter, fourier_filter, mean_filter, median_filter
from process.binary import threshold, adaptive_threshold, canny_edge_detector, remove_small_blobs, logically_combine, binary_dilation, binary_erosion
from process.roi import set_value
from process.measure import measure
from process.file_ import make_recent_menu, open_file_gui, save_file_gui, open_file, load_metadata, close, save_file, save_movie, save_movie_gui, change_internal_data_type_gui, save_points, load_points, save_current_frame, save_roi_traces
from roi import load_roi, makeROI
from process.overlay import time_stamp,background, scale_bar
from script_editor.ScriptEditor import ScriptEditor
from plugin_manager import PluginManager

try:
    os.chdir(os.path.split(os.path.realpath(__file__))[0])
except NameError:
    pass
def initializeMainGui():
    if g.mainGuiInitialized:
        return 0 
    g.app = QApplication(sys.argv)
    g.init('gui/main.ui')
    g.m.setGeometry(QRect(15, 33, 326, 80))
    g.m.setWindowIcon(QIcon('images/favicon.png'))

    g.m.actionOpen.triggered.connect(lambda : open_file_gui(open_file, prompt='Open File', filetypes='Image Files (*.tif *.stk *.tiff *.nd2);;All Files (*.*)'))
    g.m.actionSaveAs.triggered.connect(lambda : save_file_gui(save_file, prompt='Save File As Tif', filetypes='*.tif'))
    #g.m.actionSave_Movie.triggered.connect(lambda : save_file_gui(save_movie, prompt='Save File as MP4', filetypes='*.mp4'))
    g.m.actionExport_Movie.triggered.connect(save_movie_gui)
    g.m.actionSettings.triggered.connect(g.m.settings.gui)
    
    g.m.actionExport_Points.triggered.connect(lambda : save_file_gui(save_points, prompt='Save Points', filetypes='*.txt'))
    g.m.actionImport_Points.triggered.connect(lambda : open_file_gui(load_points, prompt='Load Points', filetypes='*.txt'))
    g.m.actionImport_ROIs.triggered.connect(lambda : open_file_gui(load_roi, prompt='Load ROIs from file', filetypes='*.txt'))
    g.m.actionChange_Internal_Data_type.triggered.connect(change_internal_data_type_gui)

    g.m.freehand.clicked.connect(lambda: g.m.settings.setmousemode('freehand'))
    g.m.line.clicked.connect(lambda: g.m.settings.setmousemode('line'))
    g.m.rectangle.clicked.connect(lambda: g.m.settings.setmousemode('rectangle'))
    g.m.point.clicked.connect(lambda: g.m.settings.setmousemode('point'))

    g.m.actionScript_Editor.triggered.connect(ScriptEditor.show)
    g.m.actionPlugin_Manager.triggered.connect(PluginManager.show)

    url='file:///'+os.path.join(os.getcwd(),'docs','_build','html','documentation.html')
    g.m.actionDocs.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
    
    g.m.actionDeinterleave.triggered.connect(deinterleave.gui)
    g.m.actionZ_Project.triggered.connect(zproject.gui)
    g.m.actionPixel_Binning.triggered.connect(pixel_binning.gui)
    g.m.actionFrame_Binning.triggered.connect(frame_binning.gui)
    g.m.actionResize.triggered.connect(resize.gui)
    g.m.actionTrim_Frames.triggered.connect(trim.gui)
    g.m.actionMultiply.triggered.connect(multiply.gui)
    g.m.actionSubtract.triggered.connect(subtract.gui)
    g.m.actionPower.triggered.connect(power.gui)
    g.m.actionGaussian_Blur.triggered.connect(gaussian_blur.gui)
    g.m.actionButterworth_Filter.triggered.connect(butterworth_filter.gui)
    g.m.actionMean_Filter.triggered.connect(mean_filter.gui)
    g.m.actionMedian_Filter.triggered.connect(median_filter.gui)
    g.m.actionFourier_Filter.triggered.connect(fourier_filter.gui)
    g.m.actionDifference_Filter.triggered.connect(difference_filter.gui)
    g.m.actionBoxcar_Differential.triggered.connect(boxcar_differential_filter.gui)
    g.m.actionWavelet_Filter.triggered.connect(wavelet_filter.gui)
    g.m.actionRatio.triggered.connect(ratio.gui)
    g.m.actionSubtract_Trace.triggered.connect(subtract_trace.gui)
    g.m.actionAbsolute_Value.triggered.connect(absolute_value.gui)
    g.m.actionThreshold.triggered.connect(threshold.gui)
    g.m.actionAdaptive_Threshold.triggered.connect(adaptive_threshold.gui)
    g.m.actionCanny_Edge_Detector.triggered.connect(canny_edge_detector.gui)
    g.m.actionLogically_Combine.triggered.connect(logically_combine.gui)
    g.m.actionRemove_Small_Blobs.triggered.connect(remove_small_blobs.gui)
    g.m.actionBinary_Erosion.triggered.connect(binary_erosion.gui)
    g.m.actionBinary_Dilation.triggered.connect(binary_dilation.gui)
    g.m.actionSet_Value.triggered.connect(set_value.gui)
    g.m.actionImage_Calculator.triggered.connect(image_calculator.gui)
    g.m.actionTime_Stamp.triggered.connect(time_stamp.gui)
    g.m.actionScale_Bar.triggered.connect(scale_bar.gui)
    g.m.actionBackground.triggered.connect(background.gui)
    g.m.actionMeasure.triggered.connect(measure.gui)
    make_recent_menu()
    
    g.m.installEventFilter(mainWindowEventEater)
    g.m.show()
    qApp.processEvents()

class MainWindowEventEater(QObject):
    def __init__(self,parent=None):
        QObject.__init__(self,parent)
    def eventFilter(self,obj,event):
        if (event.type()==QEvent.DragEnter):
            if event.mimeData().hasUrls():
                event.accept()   # must accept the dragEnterEvent or else the dropEvent can't occur !!!
            else:
                event.ignore()
        if (event.type() == QEvent.Drop):
            if event.mimeData().hasUrls():   # if file or link is dropped
                url = event.mimeData().urls()[0]   # get first url
                filename=url.toString()
                filename=str(filename)
                filename=filename.split('file:///')[1]
                print('filename={}'.format(filename))
                open_file(filename)  #This fails on windows symbolic links.  http://stackoverflow.com/questions/15258506/os-path-islink-on-windows-with-python
                event.accept()
            else:
                event.ignore()
        return False # lets the event continue to the edit
mainWindowEventEater = MainWindowEventEater()
    
if __name__ == '__main__':
    
    initializeMainGui()
    args=sys.argv
    if os.name =='nt' and '-debug' not in args:
        g.closeCommandPrompt()        
    args=[arg for arg in args if 'FLIKA.PY' not in arg.upper() and arg != '-debug']
    if len(args)>0:
        open_file(args[0])
    
    insideSpyder='SPYDER_SHELL_ID' in os.environ
    if not insideSpyder: #if we are running outside of Spyder
        sys.exit(g.app.exec_()) #This is required to run outside of Spyder

    
    
    