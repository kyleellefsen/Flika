"""
Flika
version=0.0.7
Latest Update: 2017.03.13
@author: Kyle Ellefsen
@author: Brett Settle
@license: MIT
"""
print('Launching Flika')
import os
import sys
from qtpy import QtCore, QtGui, QtWidgets
import matplotlib.cm

from .import global_vars as g
from .window import Window
from .process.stacks import deinterleave, trim, zproject, image_calculator, pixel_binning, frame_binning, resize, change_datatype, concatenate_stacks, duplicate, generate_random_image
from .process.color import split_channels

from .process.math_ import multiply, subtract, power, ratio, absolute_value, subtract_trace, divide_trace
from .process.filters import gaussian_blur, butterworth_filter,boxcar_differential_filter, wavelet_filter, difference_filter, fourier_filter, mean_filter, median_filter, bilateral_filter
from .process.binary import threshold, adaptive_threshold, canny_edge_detector, remove_small_blobs, logically_combine, binary_dilation, binary_erosion, generate_rois
from .process.roi import set_value
from .process.measure import measure
from .process.file_ import *
from .roi import load_roi, makeROI
from .process.overlay import time_stamp,background, scale_bar
from .app.terminal_widget import ScriptEditor
from .app.plugin_manager import PluginManager
try:
    os.chdir(os.path.split(os.path.realpath(__file__))[0])
except NameError:
    pass

DOCS_URL = 'http://flika-org.github.io/documentation.html'

def initializeMainGui():
    if g.mainGuiInitialized:
        return 0 
    g.app = QtWidgets.QApplication(sys.argv)
    g.init('app/main.ui')
    desktop = QtWidgets.QApplication.desktop()
    width_px=int(desktop.logicalDpiX()*3.4)
    height_px=int(desktop.logicalDpiY()*.9)
    g.m.setGeometry(QtCore.QRect(15, 33, width_px, height_px))
    g.m.setFixedSize(326, 80)
    g.m.setWindowIcon(QtGui.QIcon('images/favicon.png'))
    g.m.actionOpen.triggered.connect(open_file_from_gui)
    g.m.actionSaveAs.triggered.connect(save_window)
    g.m.actionExport_Movie.triggered.connect(export_movie_gui)
    g.m.actionSettings.triggered.connect(g.settings.gui)
    g.m.actionExport_Points.triggered.connect(save_points)
    g.m.actionImport_Points.triggered.connect(load_points)
    g.m.actionImport_ROIs.triggered.connect(load_roi)
    g.m.freehand.clicked.connect(lambda: g.settings.setmousemode('freehand'))
    g.m.line.clicked.connect(lambda: g.settings.setmousemode('line'))
    g.m.rect_line.clicked.connect(lambda: g.settings.setmousemode('rect_line'))
    g.m.rectangle.clicked.connect(lambda: g.settings.setmousemode('rectangle'))
    g.m.point.clicked.connect(lambda: g.settings.setmousemode('point'))
    g.m.point.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    g.m.point.customContextMenuRequested.connect(g.pointSettings)
    g.m.actionScript_Editor.triggered.connect(ScriptEditor.show)
    g.m.actionPlugin_Manager.triggered.connect(PluginManager.show)
    g.m.actionDocs.triggered.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(DOCS_URL)))
    g.m.actionDeinterleave.triggered.connect(deinterleave.gui)
    g.m.actionSplit_Channels.triggered.connect(split_channels.gui)
    g.m.actionZ_Project.triggered.connect(zproject.gui)
    g.m.actionPixel_Binning.triggered.connect(pixel_binning.gui)
    g.m.actionFrame_Binning.triggered.connect(frame_binning.gui)
    g.m.actionResize.triggered.connect(resize.gui)
    g.m.actionDuplicate.triggered.connect(duplicate)
    g.m.actionGenerate_random_image.triggered.connect(generate_random_image.gui)
    g.m.actionTrim_Frames.triggered.connect(trim.gui)
    g.m.actionConcatenate_Stacks.triggered.connect(concatenate_stacks.gui)
    g.m.actionChange_datatype.triggered.connect(change_datatype.gui)
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
    g.m.actionBilateral_Filter.triggered.connect(bilateral_filter.gui)
    g.m.actionRatio.triggered.connect(ratio.gui)
    g.m.actionSubtract_Trace.triggered.connect(subtract_trace.gui)
    g.m.actionDivide_Trace.triggered.connect(divide_trace.gui)
    g.m.actionAbsolute_Value.triggered.connect(absolute_value.gui)
    g.m.actionThreshold.triggered.connect(threshold.gui)
    g.m.actionAdaptive_Threshold.triggered.connect(adaptive_threshold.gui)
    g.m.actionCanny_Edge_Detector.triggered.connect(canny_edge_detector.gui)
    g.m.actionLogically_Combine.triggered.connect(logically_combine.gui)
    g.m.actionRemove_Small_Blobs.triggered.connect(remove_small_blobs.gui)
    g.m.actionBinary_Erosion.triggered.connect(binary_erosion.gui)
    g.m.actionBinary_Dilation.triggered.connect(binary_dilation.gui)
    g.m.menuBinary.addAction("Generate ROIs", generate_rois.gui)
    g.m.actionSet_Value.triggered.connect(set_value.gui)
    g.m.actionImage_Calculator.triggered.connect(image_calculator.gui)
    g.m.actionTime_Stamp.triggered.connect(time_stamp.gui)
    g.m.actionScale_Bar.triggered.connect(scale_bar.gui)
    g.m.actionBackground.triggered.connect(background.gui)
    g.m.actionMeasure.triggered.connect(measure.gui)
    make_recent_menu()
    g.m.actionCheck_For_Updates.triggered.connect(g.checkUpdates)
    g.m.installEventFilter(mainWindowEventEater)
    g.m.show()
    QtWidgets.qApp.processEvents()



class MainWindowEventEater(QtCore.QObject):
    def __init__(self,parent=None):
        QtCore.QObject.__init__(self,parent)

    def eventFilter(self,obj,event):
        type = event.type()
        if type == QtCore.QEvent.DragEnter:
            if event.mimeData().hasUrls():
                event.accept()   # must accept the dragEnterEvent or else the dropEvent can't occur !!!
            else:
                event.ignore()
        elif type == QtCore.QEvent.Drop:
            if event.mimeData().hasUrls():   # if file or link is dropped
                for url in event.mimeData().urls():
                    filename=url.toString()
                    filename=str(filename)
                    filename=filename.split('file:///')[1]
                    print('filename={}'.format(filename))
                    open_file(filename)  # This fails on windows symbolic links.  http://stackoverflow.com/questions/15258506/os-path-islink-on-windows-with-python
                    event.accept()
            else:
                event.ignore()
        elif type == QtCore.QEvent.Close:
            g.settings.save()
            print('Closing Flika')
        return False  # Allows the event to continue to the edit
mainWindowEventEater = MainWindowEventEater()


def start_flika():
    initializeMainGui()
    args = sys.argv[1:]
    if os.name == 'nt':
        g.setConsoleVisible(g.settings['debug_mode'])
    args = [arg for arg in args if 'flika.py' not in arg.lower() and arg != 'python']
    for a in args:
        if 'PYCHARM_HOSTED' not in os.environ:
            w = open_file(a)



if __name__ == '__main__':
    """
    If you would like to run Flika inside an IDE such as PyCharm, run the following commands:

import os, sys; flika_dir = os.path.join(os.path.expanduser('~'),'Documents', 'GitHub', 'flika'); sys.path.append(flika_dir); from flika import *; start_flika()

    """
    start_flika()
    insideSpyder = 'SPYDER_SHELL_ID' in os.environ
    if not insideSpyder:  # if we are running outside of Spyder
        try:
            sys.exit(g.app.exec_())  # This is required to run outside of Spyder or PyCharm
        except Exception as e:
            print(e)


