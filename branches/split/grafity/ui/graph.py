#!/usr/bin/env python
import sys

from PyQt4.Qt import *
from PyQt4 import uic
from PyQt4 import Qwt5 as qwt

from pkg_resources import resource_stream

c1, c2 = uic.loadUiType(resource_stream('grafity', 'resources/ui/graph.ui'))
class GraphView(c1, c2):
    def __init__(self, parent, graph):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.graph = graph
        self.plot = qwt.QwtPlot(self)
        self.setCentralWidget(self.plot)

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
        self.plot.setMargin(15)
        self.plot.setAutoReplot(False)
        self.plot.canvas().setLineWidth(1)
        self.plot.canvas().setFrameStyle(QFrame.Box|QFrame.Plain)
#        self.plot.setAxisScaleDraw(qwt.QwtPlot.xBottom, ScaleDraw())
#        self.plot.setAxisScaleDraw(qwt.QwtPlot.yLeft, ScaleDraw())
        self.plot.axis(self.plot.xBottom).setBaselineDist(0)
        self.plot.axis(self.plot.yLeft).setBaselineDist(0)
        self.plot.axis(self.plot.yLeft).scaleDraw().setOptions(qwt.QwtScaleDraw.None)
        self.plot.axis(self.plot.xBottom).scaleDraw().setOptions(qwt.QwtScaleDraw.None)

        self.plot.canvas().setFocusPolicy(QWidget.StrongFocus)

