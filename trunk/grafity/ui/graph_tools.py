from qwt import *
from qt import *

from grafity.arrays import clip
from grafity.actions import CompositeAction, action_list

from grafity.ui.forms.text import TextUI 
class TextOptions(TextUI):
    pass

class GraphTool(object):
    def activate(self):
        """Called when the tool is activated"""

    def deactivate(self):
        """Called when the tool is deactivated"""

    def mouse_moved(self, e):
        """Handle mouse motion events"""

    def mouse_pressed(self, e):
        """Handle mouse press events"""

    def mouse_released(self, e):
        """Handle mouse release events"""

    def key_pressed(self, e):
        """Handle key press events"""


class RangeTool(GraphTool):
    def __init__(self, graph, view, plot):
        self.graph, self.view, self.plot = graph, view, plot

    def activate(self):
        self.rangemin = self.plot.insertLineMarker('', QwtPlot.xBottom)
        self.rangemax = self.plot.insertLineMarker('', QwtPlot.xBottom)
        self.plot.setMarkerLineStyle(self.rangemin, QwtMarker.VLine)
        self.plot.setMarkerLineStyle(self.rangemax, QwtMarker.VLine)
        self.moving_rangemin = self.moving_rangemax = False

    def deactivate(self):
        self.plot.removeMarker(self.rangemin)
        self.plot.removeMarker(self.rangemax)

    def mouse_moved(self, e):
        x = self.plot.invTransform(self.plot.xBottom, e.pos().x())
        xpos = clip(x, self.range_l, self.range_r)
        self.view.freeze()
        action_list.begin_composite(CompositeAction('set-range'))
        if self.moving_rangemin:
            self.plot.setMarkerXPos(self.rangemin, xpos)
            for d in self.view.datasets:
                d.range = (xpos, d.range[1])
        elif self.moving_rangemax:
            self.plot.setMarkerXPos(self.rangemax, xpos)
            for d in self.view.datasets:
                d.range = (d.range[0], xpos)
        action_list.end_composite().register()
        self.view.unfreeze()

    def mouse_released(self, e):
        self.moving_rangemin = self.moving_rangemax = False
        if e.button() == Qt.MidButton:
            for d in self.view.datasets:
                d.range = (self.range_l, self.range_r)
                self.plot.setMarkerXPos(self.rangemin, min(d.range[0] for d in self.view.datasets))
                self.plot.setMarkerXPos(self.rangemax, max(d.range[1] for d in self.view.datasets))

    def mouse_pressed(self, e):
        if e.button() == Qt.LeftButton:
            self.moving_rangemin = True
        elif e.button() == Qt.RightButton:
            self.moving_rangemax = True
        self.range_l = min(d.minx for d in self.view.datasets)
        self.range_r = max(d.maxx for d in self.view.datasets)
        self.mouse_moved(e)

class HandTool(GraphTool):
    def __init__(self, graph, view, plot):
        self.graph, self.view, self.plot = graph, view, plot

    def mouse_pressed(self, e):
        x = self.plot.invTransform(self.plot.xBottom, e.pos().x())
        y = self.plot.invTransform(self.plot.yLeft, e.pos().y())
        self.view.mainwin.graph_fit.active_term.move(x, y)

    def mouse_moved(self, e):
        return self.mouse_pressed(e)

class ZoomTool(GraphTool):
    def __init__(self, graph, view, plot):
        self.graph, self.view, self.plot = graph, view, plot

    def mouse_pressed(self, e):
        self.xpos = self.plot.invTransform(self.plot.xBottom, e.pos().x())
        self.ypos = self.plot.invTransform(self.plot.yLeft, e.pos().y())
        self.plot.enableOutline(True)
        self.plot.setOutlinePen(QPen(Qt.blue, 0, Qt.DotLine))
        self.plot.setOutlineStyle(Qwt.Rect)
        self.mouse_moved(e)

    def mouse_released(self, e):
        x = self.plot.invTransform(self.plot.xBottom, e.pos().x())
        y = self.plot.invTransform(self.plot.yLeft, e.pos().y())
        xmin, xmax, ymin, ymax = min(self.xpos, x), max(self.xpos, x), min(self.ypos, y), max(self.ypos, y)
        if e.button() == Qt.LeftButton:
            self.graph.zoom(xmin, xmax, ymin, ymax)
        elif e.button() == Qt.RightButton:
            self.graph.zoom_out(xmin, xmax, ymin, ymax)
        elif e.button() == Qt.MidButton:
            self.graph.autoscale()
        self.plot.enableOutline(False)

class ArrowTool(GraphTool):
    def __init__(self, graph, view, plot):
        self.graph, self.view, self.plot = graph, view, plot

    def mouse_pressed(self, e):
        for mark in self.view.text:
            if self.view.hittest(mark, e.pos().x(), e.pos().y()):
                if e.button() == Qt.LeftButton:
                    mx, my = self.plot.markerPos(mark)
                    self.moving_marker = mark, e.pos().x(), e.pos().y(), mx, my
                elif e.button() == Qt.RightButton:
                    menu = QPopupMenu()
                    
                    menu.insertItem('Edit...', 1)
                    id = menu.exec_loop(self.plot.canvas().mapToGlobal(e.pos()))
                    if id == 1:
                        e = TextOptions(self.view.mainwin)
                        e.text.setText(self.plot.markerLabel(mark))
                        if e.exec_loop():
                            self.view.text[mark].text = unicode(e.text.text())
                return

    def mouse_released(self, e):
        self.moving_marker = None

    def mouse_moved(self, e):
        if self.moving_marker is not None:
            marker, ix, iy, mx, my = self.moving_marker
            mx, my = self.plot.transform(self.plot.xBottom, mx), self.plot.transform(self.plot.yLeft, my)
            mx += e.pos().x() - ix
            my += e.pos().y() - iy
            mx, my = self.plot.invTransform(self.plot.xBottom, mx), self.plot.invTransform(self.plot.yLeft, my)
            self.plot.setMarkerPos(marker, mx, my)

            self.view.redraw()

class DataReaderTool(GraphTool):
    def __init__(self, graph, view, plot):
        self.graph, self.view, self.plot = graph, view, plot

    def activate(self):
        self.reader = self.plot.insertLineMarker('', QwtPlot.xBottom)
        self.plot.setMarkerLineStyle(self.reader, QwtMarker.Cross)

    def deactivate(self):
        self.plot.removeMarker(self.reader)

    def mouse_pressed(self, e):
        self.mouse_moved(e)

    def mouse_moved(self, e):
        x = self.plot.invTransform(self.plot.xBottom, e.pos().x())
        y = self.plot.invTransform(self.plot.yLeft, e.pos().y())
        curve, dist, xval, yval, index = self.plot.closestCurve(e.pos().x(), e.pos().y())
        self.dr_dataset = self.graph.datasets[[d._curveid for d in self.graph.datasets].index(curve)]
        self.dr_point = index
        self.plot.setMarkerXPos (self.reader, xval)
        self.plot.setMarkerYPos (self.reader, yval)
        self.view.mainwin.statuslabel.setText("(%g, %g)" % (x, y))

        self.view.redraw()


class ScreenReaderTool(GraphTool):
    def __init__(self, graph, view, plot):
        self.graph, self.view, self.plot = graph, view, plot

    def activate(self):
        self.reader = self.plot.insertLineMarker('', QwtPlot.xBottom)
        self.plot.setMarkerLineStyle(self.reader, QwtMarker.Cross)

    def deactivate(self):
        self.plot.removeMarker(self.reader)

    def mouse_pressed(self, e):
        self.mouse_moved(e)

    def mouse_moved(self, e):
        x = self.plot.invTransform(self.plot.xBottom, e.pos().x())
        y = self.plot.invTransform(self.plot.yLeft, e.pos().y())
        self.plot.setMarkerXPos(self.reader, x)
        self.plot.setMarkerYPos(self.reader, y)
        self.view.mainwin.statuslabel.setText("(%g, %g)" % (x, y))
#        if e.state() & Qt.ControlButton:
#            curve, dist, xval, yval, ind = self.plot.closestCurve (e.pos().x(), e.pos().y())
#            dataset = self.datasets[[d.curveid for d in self.datasets].index(curve)]
#            if dist<=2:
#                index = dataset.data()[2][ind]
#                dataset.worksheet[dataset.coly][index] = nan
#        project.main_dict['app'].processEvents()
        self.view.redraw()


