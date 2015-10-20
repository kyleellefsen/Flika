# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 14:17:38 2014
updated 2015.01.27
@author: Kyle Ellefsen
"""
from __future__ import (absolute_import, division,print_function, unicode_literals)
import dependency_check
from future.builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, open, pow, round, super, filter, map, zip)
import time
tic=time.time()
import os, sys
sys.path.insert(0, "C:/Users/Kyle Ellefsen/Documents/GitHub/pyqtgraph")
sys.path.insert(0, "C:/Users/Medha/Documents/GitHub/pyqtgraph")
import numpy as np
from PyQt4.QtCore import * # Qt is Nokias GUI rendering code written in C++.  PyQt4 is a library in python which binds to Qt
from PyQt4.QtGui import *
from PyQt4.QtCore import pyqtSignal as Signal
from pyqtgraph import plot, show
import pyqtgraph as pg
from scripts import getScriptList
from roi import load_roi_gui, load_roi, makeROI, ROI_rectangle, ROI
import global_vars as g
from window import Window

from process.file_ import open_gui, save_as_gui, open_file, load_metadata, close, save_file, save_movie_gui, save_movie, change_internal_data_type, change_internal_data_type_gui, save_points_gui, load_points_gui
from process.stacks import deinterleave, slicekeeper, zproject, image_calculator, pixel_binning, frame_binning
from process.math_ import multiply, subtract, power, ratio, absolute_value, subtract_trace
from process.filters import gaussian_blur, butterworth_filter,boxcar_differential_filter, wavelet_filter, difference_filter, fourier_filter, mean_filter
from process.binary import threshold, adaptive_threshold, canny_edge_detector, remove_small_blobs, logically_combine, binary_dilation, binary_erosion
from process.roi import set_value
from analyze.measure import measure
from analyze.puffs.frame_by_frame_origin import frame_by_frame_origin
from analyze.puffs.average_origin import average_origin
from analyze.puffs.threshold_cluster import threshold_cluster
from process.voltage_ import *

from process.overlay import time_stamp,background, scale_bar
from pyqtgraph.dockarea import *

try:
    os.chdir(os.path.split(os.path.realpath(__file__))[0])
except NameError:
    pass
 
def showImageTrace(window):
    if g.m.currentWindow == None:
        return
    roi = ROI_rectangle(g.m.currentWindow, 0, 0)
    t, y, x = np.shape(g.m.currentWindow.image)
    roi.extend(x, y)
    roi.drawFinished()
    roi.plot()
    roi.view.removeItem(roi.pathitem)
    roi.contains = lambda f, g: False

def initializeMainGui():
    g.init('gui/GlobalAnalysis.ui', docks=True)
    g.m.setWindowTitle('Global Cell Analysis')
    g.m.setGeometry(QRect(15, 33, 100, 140))

    g.m.actionOpen.triggered.connect(open_gui)
    g.m.actionSave_Movie.triggered.connect(save_movie_gui)
    g.m.actionSaveAs.triggered.connect(save_as_gui)
    g.m.actionChange_Internal_Data_type.triggered.connect(change_internal_data_type_gui)

    g.m.actionImport_ROI_File.triggered.connect(load_roi_gui)
    g.m.actionExport_ROIs.triggered.connect(lambda : g.m.currentWindow.rois[0].save_gui() if len(g.m.currentWindow.rois) > 0 else None)
    g.m.actionSave_Points.triggered.connect(save_points_gui)
    g.m.actionLoad_Points.triggered.connect(load_points_gui)
    g.m.actionSubtract.triggered.connect(subtract.gui)
    g.m.actionRatio.triggered.connect(ratio.gui)
    g.m.actionSubtract_Trace.triggered.connect(subtract_trace.gui)
    g.m.actionAbsolute_Value.triggered.connect(absolute_value.gui)
    g.m.menuScripts.aboutToShow.connect(getScriptList)
    
    g.m.openButton.clicked.connect(open_gui)
    g.m.saveButton.clicked.connect(save_movie_gui)
    g.m.subtractButton.clicked.connect(subtract.gui)
    g.m.ratioButton.clicked.connect(ratio.gui)

    g.m.freehandButton.clicked.connect(lambda: g.m.settings.setmousemode('freehand'))
    g.m.lineButton.clicked.connect(lambda: g.m.settings.setmousemode('line'))
    g.m.rectangleButton.clicked.connect(lambda: g.m.settings.setmousemode('rectangle'))
    g.m.pointButton.clicked.connect(lambda: g.m.settings.setmousemode('point'))
    g.m.importROIButton.clicked.connect(load_roi_gui)
    g.m.exportROIButton.clicked.connect(lambda : g.m.currentWindow.rois[0].save_gui() if len(g.m.currentWindow.rois) > 0 else None)
    g.m.plotAllButton.clicked.connect(lambda : [roi.plot() for roi in g.m.currentWindow.rois])
    g.m.clearButton.clicked.connect(lambda : [roi.delete() for roi in g.m.currentWindow.rois])
    g.m.newWindowCheck.toggled.connect(g.m.settings.setMultipleTraceWindows)

    g.m.lineMeasureButton.clicked.connect(measure.gui)
    g.m.showTraceButton.clicked.connect(showImageTrace)
    g.m.closeButton.clicked.connect(lambda : [w.close() for w in g.m.windows])
    g.m.exitButton.clicked.connect(g.m.close)
    
    g.m.settings.setmousemode('rectangle')
    g.m.menuScripts.aboutToShow.connect(getScriptList)
    #url='file:///'+os.path.join(os.getcwd(),'docs','_build','html','index.html')
    #g.m.actionDocs.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
    g.m.setAcceptDrops(True)

    g.m.show()

    g.widgetCreated = dockCreated
    g.m.outlineCheck.toggled.connect(setIsoVisible)
    g.m.voltageButton.clicked.connect(runVoltage)

def runVoltage():
    img = g.m.currentWindow.imageview.image
    v = np.average(img, (2, 1))
    Vout, corrimg, weight_movie, offsetimg = extractV(img, v)
    Window(corrimg, 'Corrected Image')
    Window(weight_movie, "Weight Movie")
    Window(offsetimg, 'Offset Image')
    print(Vout)
    pg.plot(Vout)
    print(ApplyWeights(img[:], corrimg, weight_movie, offsetimg))

def setIsoVisible(v):
    if g.m.currentWindow != None and hasattr(g.m.currentWindow, 'iso'):
        g.m.currentWindow.iso.setVisible(v)
        g.m.currentWindow.isoLine.setVisible(v)


def dockCreated(widg):
    widgDock = Dock(name = widg.name, widget=widg, closable=True)
    g.m.dockarea.addDock(widgDock)
    widg.closeEvent = lambda ev: g.dockCloseEvent(ev, widg, widgDock)
    widgDock.closeEvent = widg.closeEvent

    if isinstance(widg, Window):
        pass
        #addIsoCurve(widg)

def addIsoCurve(widg):
    lut = widg.imageview.getHistogramWidget().centralWidget
    widg.iso = pg.IsocurveItem(level=0.8, pen='g')
    widg.iso.setParentItem(widg.imageview.getImageItem())
    widg.iso.setZValue(5)
    widg.isoLine = pg.InfiniteLine(angle=0, movable=True, pen='g')
    lut.vb.addItem(widg.isoLine)
    #lut.vb.setMouseEnabled(y=False) # makes user interaction a little easier
    widg.isoLine.setValue(np.average(lut.getLevels()))
    widg.isoLine.setZValue(1000)
    widg.iso.setData(pg.gaussianFilter(widg.image[widg.currentIndex], (2, 2)))
    def updateIsocurve():
        widg.iso.setLevel(widg.isoLine.value())
    updateIsocurve()
    setIsoVisible(False)

    widg.isoLine.sigDragged.connect(updateIsocurve)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    initializeMainGui()
    
    
    insideSpyder='SPYDER_SHELL_ID' in os.environ
    if not insideSpyder: #if we are running outside of Spyder
        sys.exit(app.exec_()) #This is required to run outside of Spyder