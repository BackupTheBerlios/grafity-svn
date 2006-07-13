#!/usr/bin/env python
import sys

from PyQt4.Qt import *
from PyQt4 import Qwt5 as qwt

from grafity.ui.worksheet import Ui_Form

from pkg_resources import resource_stream

class GraphView(QWidget, Ui_Form):
    def __init__(self, parent, graph):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.graph = graph
        self.plot = qwt.QwtPlot(self)

        self.bg_color = QColor('white')


        self.plot.setCanvasBackground(self.bg_color)
#        self.plot.setPaletteBackgroundColor(self.bg_color)
#        font = QFont('/home/daniel/grafito/data/fonts/bakoma-cm/cmr10.ttf')
#        font = QFont('FreeMono',9)
        font = QFont('GentiumAlt')
        self.plot.setAxisFont(self.plot.xBottom, font)
        self.plot.setAxisFont(self.plot.yLeft, font)
#        self.plot.enableGridX(True)
#        self.plot.enableGridY(True)
#        self.plot.setGridPen(QPen(QColor('gray'), 0, Qt.DotLine))
#        self.plot.setMargin(15)
        self.plot.setAutoReplot(False)
        self.plot.canvas().setLineWidth(1)
        self.plot.canvas().setFrameStyle(QFrame.Box|QFrame.Plain)
        self.plot.plotLayout().setAlignCanvasToScales(True)


        for i in range(qwt.QwtPlot.axisCnt):
            scaleWidget = self.plot.axisWidget(i)
            if scaleWidget:
                scaleWidget.setMargin(0)
            scaleDraw = self.plot.axisScaleDraw(i)
            if scaleDraw:
                scaleDraw.enableComponent(qwt.QwtAbstractScaleDraw.Backbone, False)


#        self.plot.setAxisScaleDraw(qwt.QwtPlot.xBottom, ScaleDraw())
#        self.plot.setAxisScaleDraw(qwt.QwtPlot.yLeft, ScaleDraw())
#        self.plot.axisWidget(self.plot.xBottom).setBaselineDist(0)
#        self.plot.axisWidget(self.plot.yLeft).setBaselineDist(0)
#        self.plot.axisWidget(self.plot.yLeft).scaleDraw().setOptions(qwt.QwtScaleDraw.None)
#        self.plot.axisWidget(self.plot.xBottom).scaleDraw().setOptions(qwt.QwtScaleDraw.None)

#        self.plot.canvas().setFocusPolicy(QWidget.StrongFocus)

