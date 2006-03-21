import sys

from grafity.arrays import *

from grafity.extend import register_graph_mode

from grafity.ui.graph_tools import GraphTool
from numarray import argmin, ones, array, argmax
from scipy.interpolate import splrep, splev
from qt import *


#register_graph_mode = sys.modules['grafity.extend'].register_graph_mode

def integrate(x, y):
    dx = x[1:]-x[:-1]
    dy = y[1:]-y[:-1]

    r = y[1:] * dx
    t = dy * dx

    return concatenate([[0], add.accumulate(r+t)])

class AnalyzeGlassTransition(GraphTool):
    def __init__(self, graph, view, plot):
        self.graph, self.view, self.plot = graph, view, plot
    name = "Analyze Tg"
    image = 'tg'

    def activate(self):
        self.foo = self.plot.insertCurve("foo")
        self.foo2 = self.plot.insertCurve("foo")
        self.foom = self.plot.insertCurve("foo")
        self.plot.setCurvePen(self.foo, QPen(Qt.darkGreen))
        self.plot.setCurvePen(self.foo2, QPen(Qt.darkRed))
        self.plot.setCurvePen(self.foom, QPen(Qt.darkCyan))

    def deactivate(self):
        pass

    def mouse_released(self, e):
        self.button = None

    def mouse_pressed(self, e):
        self.button = e.button()

    def mouse_moved(self, e):
        x = self.plot.invTransform(self.plot.xBottom, e.pos().x())
        y = self.plot.invTransform(self.plot.yLeft, e.pos().y())

        if self.graph.datasets == []:
            return

        d = self.view.datasets[0]
        ind = d.active_data()
        dx, dy = d.x[ind], d.y[ind]
        dist = (x-dx)*(x-dx)
        arg = argmin(dist)
        xval, yval = dx[arg], dy[arg]

        w = ones(len(dx))*50./(max(dy)-min(dy))
        spl = splrep(dx, dy, w, s=20)
        deriv = splev(dx, spl, der=1)
        inflarg = argmax(deriv)
        inflx, infly = dx[inflarg], dy[inflarg]

        linex = array([self.graph.xmin, self.graph.xmax])

        #liney = yval + deriv[arg]*(linex-xval)

        if self.button == Qt.LeftButton:
            self._line = 'left'
        elif self.button == Qt.RightButton:
            self._line = 'right'

        if self._line == 'left':
            self.A1 = deriv[arg]
            self.B1 = yval-self.A1*xval
            liney = self.A1*linex + self.B1

            self.plot.setCurveData(self.foo, linex, liney)
        elif self._line == 'right':
            self.A3 = deriv[arg]
            self.B3 = yval-self.A3*xval
            liney = self.A3*linex + self.B3
            self.plot.setCurveData(self.foo2, linex, liney)

        self.A2 = deriv[inflarg]
        self.B2 = infly-self.A2*inflx

        liney = self.A2*linex + self.B2

        #liney = infly + deriv[inflarg]*(linex-inflx)
        self.plot.setCurveData(self.foom, linex, liney)
        if hasattr(self, 'A3') and hasattr(self, 'A1'):
            Ton = -(self.B2-self.B1)/(self.A2-self.A1)
            Tend = -(self.B3-self.B2)/(self.A3-self.A2)
            self.plot.setMarkerLabel(self.texte, 
            "T<sub>f</sub>=%f<br>T<sub>on</sub>=%f, T<sub>end</sub>=%f<br>"%(inflx,Ton,Tend))

        self.view.redraw()

register_graph_mode(AnalyzeGlassTransition)

class Eraser(GraphTool):
    def __init__(self, graph, view, plot):
        self.graph, self.view, self.plot = graph, view, plot
    name = "Erase data points"
    image = 'eraser'

register_graph_mode(Eraser)
