import os
import sys
try:
    sys.modules['grafity.ui.start'].splash.message('loading ui_graph_view')
except:
    pass

from qt import *
from qwt import *
import qwt.qplt

from grafity.arrays import nan, arange, log10, isnan, asarray, Float, argmin, argmax, array, ones, sqrt
from grafity.functions import registry, Function
from grafity import Graph, Worksheet, Folder
from grafity.settings import USERDATADIR
from grafity.graph import symbols, fills, colors, linetypes, linestyles, attrs, Text

from grafity.ui.forms.graph_style import GraphStyleUI
from grafity.ui.forms.graph_data import GraphDataUI
from grafity.ui.forms.graph_axes import GraphAxesUI
from grafity.ui.forms.graph_fit import GraphFitUI
from grafity.ui.forms.functions import FunctionsWindowUI
from grafity.ui.forms.fitoptions import FitOptionsUI
from grafity.ui.utils import getimage, connectevents, Page, graph_modes
from grafity.ui.graph_tools import ZoomTool, RangeTool, ArrowTool, HandTool
from grafity.ui.graph_tools import DataReaderTool, ScreenReaderTool

class ErrorBarPlotCurve(QwtPlotCurve):
    def __init__(self, parent,
                 x = [], y = [], dx = None, dy = None,
                 curvePen = QPen(Qt.NoPen),
                 curveStyle = QwtCurve.Lines,
                 curveSymbol = QwtSymbol(),
                 errorPen = QPen(Qt.NoPen),
                 errorCap = 0,
                 errorOnTop = False,
                 ):
        """A curve of x versus y data with error bars in dx and dy.

        Horizontal error bars are plotted if dx is not None.
        Vertical error bars are plotted if dy is not None.

        x and y must be sequences with a shape (N,) and dx and dy must be
        sequences (if not None) with a shape (), (N,), or (2, N):
        - if dx or dy has a shape () or (N,), the error bars are given by
          (x-dx, x+dx) or (y-dy, y+dy),
        - if dx or dy has a shape (2, N), the error bars are given by
          (x-dx[0], x+dx[1]) or (y-dy[0], y+dy[1]).

        curvePen is the pen used to plot the curve
        
        curveStyle is the style used to plot the curve
        
        curveSymbol is the symbol used to plot the symbols
        
        errorPen is the pen used to plot the error bars
        
        errorCap is the size of the error bar caps
        
        errorOnTop is a boolean:
        - if True, plot the error bars on top of the curve,
        - if False, plot the curve on top of the error bars.
        """

        QwtPlotCurve.__init__(self, parent)
        self.setData(x, y, dx, dy)
        self.setPen(curvePen)
        self.setStyle(curveStyle)
        self.setSymbol(curveSymbol)
        self.errorPen = errorPen
        self.errorCap = errorCap
        self.errorOnTop = errorOnTop

    # __init__()

    def setData(self, x, y, dx = None, dy = None):
        """Set x versus y data with error bars in dx and dy.

        Horizontal error bars are plotted if dx is not None.
        Vertical error bars are plotted if dy is not None.

        x and y must be sequences with a shape (N,) and dx and dy must be
        sequences (if not None) with a shape (), (N,), or (2, N):
        - if dx or dy has a shape () or (N,), the error bars are given by
          (x-dx, x+dx) or (y-dy, y+dy),
        - if dx or dy has a shape (2, N), the error bars are given by
          (x-dx[0], x+dx[1]) or (y-dy[0], y+dy[1]).
        """
        
        self.__x = asarray(x, Float)
        if len(self.__x.shape) != 1:
            raise RuntimeError, 'len(asarray(x).shape) != 1'

        self.__y = asarray(y, Float)
        if len(self.__y.shape) != 1:
            raise RuntimeError, 'len(asarray(y).shape) != 1'
        if len(self.__x) != len(self.__y):
            raise RuntimeError, 'len(asarray(x)) != len(asarray(y))' 

        if dx is None:
            self.__dx = None
        else:
            self.__dx = asarray(dx, Float)
            if len(self.__dx.shape) not in [0, 1, 2]:
                raise RuntimeError, 'len(asarray(dx).shape) not in [0, 1, 2]'
            
        if dy is None:
            self.__dy = dy
        else:
            self.__dy = asarray(dy, Float)
            if len(self.__dy.shape) not in [0, 1, 2]:
                raise RuntimeError, 'len(asarray(dy).shape) not in [1, 2]'
        
        QwtPlotCurve.setData(self, self.__x, self.__y)

    # setData()
        
    def boundingRect(self):
        """Return the bounding rectangle of the data, error bars included.
        """
        if self.__dx is None:
            xmin = min(self.__x)
            xmax = max(self.__x)
        elif len(self.__dx.shape) in [0, 1]:
            xmin = min(self.__x - self.__dx)
            xmax = max(self.__x + self.__dx)
        else:
            xmin = min(self.__x - self.__dx[0])
            xmax = max(self.__x + self.__dx[1])

        if self.__dy is None:
            ymin = min(self.__y)
            ymax = max(self.__y)
        elif len(self.__dy.shape) in [0, 1]:
            ymin = min(self.__y - self.__dy)
            ymax = max(self.__y + self.__dy)
        else:
            ymin = min(self.__y - self.__dy[0])
            ymax = max(self.__y + self.__dy[1])

        return QwtDoubleRect(xmin, xmax, ymin, ymax)
        
    # boundingRect()

    def draw(self, painter, xMap, yMap, first, last = -1):
        """Draw an interval of the curve, including the error bars

        painter is the QPainter used to draw the curve

        xMap is the QwtDiMap used to map x-values to pixels

        yMap is the QwtDiMap used to map y-values to pixels
        
        first is the index of the first data point to draw

        last is the index of the last data point to draw. If last < 0, last
        is transformed to index the last data point
        """
        
        if last < 0:
            last = self.dataSize() - 1
        if not self.verifyRange(first, last):
            return

        if self.errorOnTop:
            QwtPlotCurve.draw(self, painter, xMap, yMap, first, last)

        # draw the error bars
        painter.save()
        painter.setPen(self.errorPen)

        # draw the error bars with caps in the x direction
        if self.__dx is not None:
            # draw the bars
            if len(self.__dx.shape) in [0, 1]:
                xmin = (self.__x - self.__dx)[first:last+1]
                xmax = (self.__x + self.__dx)[first:last+1]
            else:
                xmin = (self.__x - self.__dx[0])[first:last+1]
                xmax = (self.__x + self.__dx[1])[first:last+1]
            y = self.__y[first:last+1]
            n, i, j = len(y), 0, 0
            lines = QPointArray(2*n)
            while i < n:
                yi = yMap.transform(y[i])
                lines.setPoint(j, xMap.transform(xmin[i]), yi)
                j += 1
                lines.setPoint(j, xMap.transform(xmax[i]), yi)
                j += 1; i += 1
            painter.drawLineSegments(lines)
            if self.errorCap > 0:
                # draw the caps
                cap = self.errorCap/2
                n, i, j = len(y), 0, 0
                lines = QPointArray(4*n)
                while i < n:
                    yi = yMap.transform(y[i])
                    lines.setPoint(j, xMap.transform(xmin[i]), yi - cap)
                    j += 1
                    lines.setPoint(j, xMap.transform(xmin[i]), yi + cap)
                    j += 1
                    lines.setPoint(j, xMap.transform(xmax[i]), yi - cap)
                    j += 1
                    lines.setPoint(j, xMap.transform(xmax[i]), yi + cap)
                    j += 1; i += 1
            painter.drawLineSegments(lines)

        # draw the error bars with caps in the y direction
        if self.__dy is not None:
            # draw the bars
            if len(self.__dy.shape) in [0, 1]:
                ymin = (self.__y - self.__dy)[first:last+1]
                ymax = (self.__y + self.__dy)[first:last+1]
            else:
                ymin = (self.__y - self.__dy[0])[first:last+1]
                ymax = (self.__y + self.__dy[1])[first:last+1]
            x = self.__x[first:last+1]
            n, i, j = len(x), 0, 0
            lines = QPointArray(2*n)
            while i < n:
                xi = xMap.transform(x[i])
                lines.setPoint(j, xi, yMap.transform(ymin[i]))
                j += 1
                lines.setPoint(j, xi, yMap.transform(ymax[i]))
                j += 1; i += 1
            painter.drawLineSegments(lines)
            # draw the caps
            if self.errorCap > 0:
                cap = self.errorCap/2
                n, i, j = len(x), 0, 0
                lines = QPointArray(4*n)
                while i < n:
                    xi = xMap.transform(x[i])
                    lines.setPoint(j, xi - cap, yMap.transform(ymin[i]))
                    j += 1
                    lines.setPoint(j, xi + cap, yMap.transform(ymin[i]))
                    j += 1
                    lines.setPoint(j, xi - cap, yMap.transform(ymax[i]))
                    j += 1
                    lines.setPoint(j, xi + cap, yMap.transform(ymax[i]))
                    j += 1; i += 1
            painter.drawLineSegments(lines)

        painter.restore()

        if not self.errorOnTop:
            QwtPlotCurve.draw(self, painter, xMap, yMap, first, last)

qsymbols = {
    'none': QwtSymbol.None,
    'circle': QwtSymbol.Ellipse,
    'square': QwtSymbol.Rect,
    'diamond': QwtSymbol.Diamond,
    'triangleup': QwtSymbol.UTriangle, 
    'triangledown': QwtSymbol.DTriangle, 
    'triangleleft': QwtSymbol.LTriangle, 
    'triangleright': QwtSymbol.RTriangle, 
    '+': QwtSymbol.Cross,
    'x': QwtSymbol.XCross,
}

qfills = { 'filled': QBrush(Qt.black), 
           'open': QBrush(), }

qcolors = [QColor(s) for s in colors]

qlinetypes = [QwtCurve.NoCurve, QwtCurve.Lines, QwtCurve.Spline]
qlinestyles = [Qt.SolidLine, Qt.DashLine, Qt.DotLine, Qt.DashDotLine, Qt.DashDotDotLine]



class ListViewItem(QListViewItem):
    def __init__(self, parent, obj):
        QListViewItem.__init__(self, parent, obj.name)
        obj._gd_item = self
        self._object = obj

        pixmap = getimage({Worksheet: 'worksheet', 
                           Graph: 'graph', 
                           Folder: 'folder'}[type(obj)])
        self.setPixmap (0, pixmap)

        self._object.connect('rename', self.on_object_renamed)
        self._object.connect('set-parent', self.on_object_set_parent)

    def on_object_renamed(self, name, item):
        self.setText(0, name)

    def on_object_set_parent(self, parent):
        self.parent().takeItem(self)
        parent._gd_item.insertItem(self)
 

def efloat(f):
    try:
        return float(f)
    except Exception:
        return nan

superscripts = {
#    '-': u'\u00AF',
    '-': u'\u207B',
    '0': u'\u2070',
    '1': u'\u00B9',
    '2': u'\u00B2',
    '3': u'\u00B3',
    '4': u'\u2074',
    '5': u'\u2075',
    '6': u'\u2076',
    '7': u'\u2077',
    '8': u'\u2078',
    '9': u'\u2079',
    }

class ScaleDraw(QwtScaleDraw):
    """A version of QwtScaleDraw that supports rich text in tick labels.
    """
    def __init__(self):
        QwtScaleDraw.__init__(self)
        self.font = QFont('Times New Roman')

    def draw(self, p):
        scldiv = self.scaleDiv()
        minLen, medLen, majLen = self.tickLength()
        step_eps = 1.e-6

        for i in range(scldiv.majCnt()):
            val = scldiv.majMark(i)
            self.drawTick(p, val, majLen)
            self.drawLabel(p, val)

        if scldiv.logScale():
            for i in range(scldiv.minCnt()):
                self.drawTick(p, scldiv.minMark(i), minLen)
        else:
            kmax = scldiv.majCnt() - 1
            if kmax>0:
                majTick = scldiv.majMark(0)
                hval = majTick - 0.5 * scldiv.majStep()

                k = 0
                for i in range(scldiv.minCnt()):
                    val = scldiv.minMark(i)
                    if val > majTick:
                        if k < kmax:
                            k+=1
                            majTick = scldiv.majMark(k)
                        else:
                            majTick = scldiv.majMark(kmax) + scldiv.majStep()
                        hval = majTick - 0.5 * scldiv.majStep()
                    if abs(val-hval) < step_eps*scldiv.majStep():
                        self.drawTick(p, val, medLen)
                    else:
                        self.drawTick(p, val, minLen)

            if self.options() & QwtScaleDraw.Backbone:
                self.drawBackbone(p)

    def maxLabelHeight(self, fm):
        scldiv = self.scaleDiv()
        step_eps = 1e-6

        maxHeight = 0

        for i in range(scldiv.majCnt()):
            val = scldiv.majMark(i)

            # correct rounding errors if val = 0
            if not scldiv.logScale() and abs(val)<step_eps*abs(scldiv.majStep()):
                val = 0.

            h = self.labelBoundingRect(fm, val).height()
            if h>maxHeight:
                maxHeight = h

        return maxHeight

    def maxLabelWidth(self, fm):
        scldiv = self.scaleDiv()
        step_eps = 1e-6

        maxWidth = 0

        for i in range(scldiv.majCnt()):
            val = scldiv.majMark(i)

            # correct rounding errors if val = 0
            if not scldiv.logScale() and abs(val)<step_eps*abs(scldiv.majStep()):
                val = 0.

            h = self.labelBoundingRect(fm, val).width()
            if h>maxWidth:
                maxWidth = h

        return maxWidth

    def drawLabel(self, p, val):
        pos = QPoint()
        alignment, rotation = self.labelPlacement(QFontMetrics(self.font), val, pos)

        if alignment:
            txt = QString(self.label(val, True))
            if not txt.isEmpty():
                m = self.labelWorldMatrix(QFontMetrics(self.font), pos, alignment, rotation, txt)
                p.save()
                p.setWorldMatrix(m, True)
#                QwtPainter.drawText(p, 0, 0, txt)
                qwtxt = QwtText.makeText(txt, alignment, self.font)
                br = qwtxt.boundingRect()
                qwtxt.draw(p, QRect(0, 0, br.width(), br.height()))
                p.restore()

    def qtxt(self, val):
        lbl = self.label(val, True)
        return QwtText.makeText(lbl, self.labelAlignment(), self.font)

    def labelWorldMatrix(self, fm, pos, alignment, rotation, txt):
        ltxt = QwtText.makeText(txt, alignment, self.font)
        br = ltxt.boundingRect()
        w, h = br.width(), br.height()

        if alignment & Qt.AlignLeft: x = -w
        elif alignment & Qt.AlignRight: x = 0 - w%2
        else: x = -w/2
        
        if alignment & Qt.AlignTop: y = -h
        elif alignment & Qt.AlignBottom: y = 0
        else: y = -h/2

        m = QWMatrix()
        m.translate(pos.x(), pos.y())
        m.rotate(rotation)
        m.translate(x, y)

        return m

    def minBorderDist(self, fm):
        print >>sys.stderr, "her"

    def labelBoundingRect(self, fm, val):
        f, prec, fieldwidth = self.labelFormat()
        zeroString = QString()
        zeroString.fill(QChar('0'), fieldwidth)

        lbl = QString(self.label(val, True))

        if fm.width(zeroString) > fm.width(lbl):
            txt = zeroString
        else:
            txt = lbl

        if txt.isEmpty():
            return QRect(0, 0, 0, 0)

        ltxt = self.qtxt(val)
        pos = QPoint()

        alignment, rotation = self.labelPlacement(fm, val, pos)
        if alignment:
            r = ltxt.boundingRect()
            w, h = r.width(), r.height()

            m = self.labelWorldMatrix(fm, pos, alignment, rotation, lbl)

            br = QwtMetricsMap.translate(m, QRect(0, 0, w, h))
            br.moveBy(-pos.x(), -pos.y())
        return br;

    def label(self, value, rich=False):
        mant, exp = ('%e'%value).split('e')
        if float(mant) == 1.:
            mant = ''
        else:
            mant = unicode(QwtScaleDraw.label(self, float(mant)))
        exp = unicode(int(exp))
        if rich:
            return (mant+'x')*bool(mant)+'10<sup>'+exp+'</sup>'
        else:
            return (mant+'x')*bool(mant)+'10'+exp


class LVI(QListViewItem):
    def __init__(self, *args):
        QListView.__init__(self, *args)

    def paintCell(self, painter, cg, column, width, align):
        cg = QColorGroup(cg)
        cg.setColor(QColorGroup.Base, cg.color(QColorGroup.Background))#self.legend_background_color)
        QListViewItem.paintCell(self, painter, cg, column, width, align)


class GraphView(QVBox):
    def __init__(self, parent, mainwin, graph):
        QVBox.__init__(self, parent)
        self.graph = graph
        self.mainwin = mainwin
        self.setIcon(getimage('graph'))
        self.mainpage = QSplitter(QSplitter.Horizontal, self)
        
        self.bg_color = QColor('white')

        self.plot = QwtPlot()
        self.plot.reparent(self.mainpage, 0, QPoint(0,0))
        self.plot.setCanvasBackground(self.bg_color)
        self.plot.setPaletteBackgroundColor(self.bg_color)
#        font = QFont('/home/daniel/grafito/data/fonts/bakoma-cm/cmr10.ttf')
#        font = QFont('FreeMono',9)
        font = QFont('GentiumAlt')
        self.plot.setAxisFont(self.plot.xBottom, font)
        self.plot.setAxisFont(self.plot.yLeft, font)
        self.plot.enableGridX(True)
        self.plot.enableGridY(True)
        self.plot.setGridPen(QPen(QColor('gray'), 0, Qt.DotLine))
        self.plot.setMargin(15)
        self.plot.setAutoReplot(False)
        self.plot.canvas().setLineWidth(1)
        self.plot.canvas().setFrameStyle(QFrame.Box|QFrame.Plain)
        self.plot.setAxisScaleDraw(QwtPlot.xBottom, ScaleDraw())
        self.plot.setAxisScaleDraw(QwtPlot.yLeft, ScaleDraw())
        self.plot.axis(self.plot.xBottom).setBaselineDist(0)
        self.plot.axis(self.plot.yLeft).setBaselineDist(0)
        self.plot.axis(self.plot.yLeft).scaleDraw().setOptions(QwtScaleDraw.None)
        self.plot.axis(self.plot.xBottom).scaleDraw().setOptions(QwtScaleDraw.None)

        self.plot.canvas().setFocusPolicy(QWidget.StrongFocus)

        self.graph.connect('style-changed', self.on_change_style)
        self.graph.connect('zoom-changed', self.on_zoom_changed)
        self.graph.connect('data-changed', self.on_recalc)
        self.graph.connect('rename', self.on_rename)
        self.graph.connect('fullname-changed', self.on_rename)
        self.graph.connect('new-object', self.on_new_object)
        self.graph.connect('remove-object', self.on_remove_object)
        self.graph.connect('text-changed', self.on_text_changed)

        self.graph.connect('add-dataset', self.on_add_dataset)
        self.graph.connect('remove-dataset', self.on_remove_dataset)
        self.graph.connect('set-title', self.on_set_title)
        self.graph.connect('set-scale', self.on_set_scale)
        self.graph.function.connect('add-term', self.on_add_function_term)
        self.graph.function.connect('remove-term', self.on_remove_function_term)
        self.graph.function.connect('modified', self.on_function_modified)

        self.frozen = False
        self.needs_redraw = False
        self.needs_legend_update = False

        self.connect(self.plot, SIGNAL('plotMouseMoved(const QMouseEvent&)'), self.on_mouse_moved)
        self.connect(self.plot, SIGNAL('plotMousePressed(const QMouseEvent&)'), self.on_mouse_pressed)
        self.connect(self.plot, SIGNAL('plotMouseReleased(const QMouseEvent&)'), self.on_mouse_released)

        self.legend = QListView(self.mainpage)
        self.legend.addColumn('foo')
        self.legend.setColumnWidthMode(0, QListView.Maximum)
        self.legend.setSelectionMode(QListView.Extended)

#        pal = QPalette(self.legend.palette())
#        cg = QColorGroup(pal.active())
        self.legend_background_color = Qt.white
#cg.color(QColorGroup.Background)
#        cg.setColor(QColorGroup.Base, Qt.white)#self.legend_background_color)
#        pal.setActive(cg)
#        self.legend.setPalette(pal)
        self.legend.setFrameShape(QFrame.NoFrame)
        f = QFont()
        f.setPointSize(9)
        self.legend.setFont(f)
        self.legend.setTreeStepSize(5)
        self.legend.header().hide()
        self.connect(self.legend, SIGNAL('selectionChanged()'), self.on_legend_select)
        self.connect(self.legend, SIGNAL('contextMenuRequested(QListViewItem *, const QPoint &, int)'), 
                     self.on_legend_cmenu)

        self.freeze()
        for d in self.graph.datasets:
            self.on_add_dataset(d)
        for t in self.graph.function.terms:
            self.on_add_function_term(t)
        self.graph.function._curveid = self.plot.insertCurve('')
        self.plot.curve(self.graph.function._curveid).pen().setColor(Qt.blue)
        self.on_function_modified()
        self.update_legend()
        self.on_set_scale('x', self.graph.xtype)
        self.on_set_scale('y', self.graph.xtype)
        self.on_set_title('x', self.graph.xtitle)
        self.on_set_title('y', self.graph.ytitle)
        self.on_zoom_changed(self.graph.xmin, self.graph.xmax, self.graph.ymin, self.graph.ymax)
        self.unfreeze()

        self.moving_marker = None

        self.tools = {}
        self.tools['zoom'] = ZoomTool(self.graph, self, self.plot)
        self.tools['range'] = RangeTool(self.graph, self, self.plot)
        self.tools['hand'] = HandTool(self.graph, self, self.plot)
        self.tools['sreader'] = ScreenReaderTool(self.graph, self, self.plot)
        self.tools['dreader'] = DataReaderTool(self.graph, self, self.plot)
        self.tools['arrow'] = ArrowTool(self.graph, self, self.plot)

        for tool in graph_modes:
            self.tools[tool.name] = tool(self.graph, self, self.plot)

        self.tool = None
        self._mode = None
        self.mode = 'arrow'
        self.setCaption(self.graph.fullname)
        self.setWFlags(Qt.WDestructiveClose)

        self.graph.project.connect('remove-item', self.on_project_remove_item)
        connectevents(self.plot.canvas(), self.on_canvas_event)
        self.plot.plotLayout().setAlignCanvasToScales(True)

        self.text = {}

    def set_mode(self, mode):
        if mode == self._mode:
            return
        if self.tool is not None:
            self.tool.deactivate()
        self._mode = mode
        if mode in self.tools:
            self.tool = self.tools[self.mode]
            self.tool.activate()
        else:
            self.tool = None
    def get_mode(self):
        return self._mode
    mode = property(get_mode, set_mode)

    def on_text_clicked(self):
        text = self.graph.new_object(Text)
        text.text = 'foo'

    def Print(self):
        line = self.plot.insertCurve('frame')
        self.plot.setCurvePen(line, QPen(Qt.black))
        self.plot.setCurveData(line,
         [self.graph.xmin, self.graph.xmax, self.graph.xmax, self.graph.xmin, self.graph.xmin],
         [self.graph.ymin, self.graph.ymin, self.graph.ymax, self.graph.ymax, self.graph.ymin])

        printer = QPrinter()
        printer.setOutputToFile(True)
        printer.setOutputFileName('mikou.ps')
#        printer.setup()
        printer.newPage()
        self.plot.printPlot(printer)
        self.plot.removeCurve(line)

    def on_new_object(self, obj):
        mark = self.plot.insertMarker()
        self.plot.setMarkerPos(mark, 0, 0)
        self.plot.setMarkerLabel(mark, "Poutsa")
        self.plot.setMarkerLabelAlign(mark, Qt.AlignTop|Qt.AlignRight)
        self.text[mark] = obj
        obj._marker = mark
        self.redraw()

    def on_remove_object(self, obj):
        del self.text[obj._marker]
        self.plot.removeMarker(obj._marker)
        self.redraw()

    def on_text_changed(self, obj):
        self.plot.setMarkerLabel(obj._marker, obj.text)
        self.redraw()

    def on_project_remove_item(self, item):
        if item == self.graph:
            self.close()

    def closeEvent(self, event):
        self.graph._view = None
        event.accept()

    def on_rename(self, *args, **kwds):
        self.setCaption(self.graph.fullname)

    def on_set_title(self, axis, title):
        self.plot

    def on_set_scale(self, axis, scale):
        if axis == 'x':
            self.plot.changeAxisOptions(self.plot.xBottom, qwt.qplt.Logarithmic, scale=='log')
        else:
            self.plot.changeAxisOptions(self.plot.yLeft, qwt.qplt.Logarithmic, scale=='log')
        self.redraw()

    def freeze(self):
        self.frozen = True

    def unfreeze(self):
        self.frozen = False
        if self.needs_redraw:
            self.redraw()
        if self.needs_legend_update:
            self.update_legend()

    def redraw(self):
        if self.frozen:
            self.needs_redraw = True
        else:
            self.plot.replot()
            self.needs_redraw = False

    def update_legend(self):
        if self.frozen:
            self.needs_legend_update = True
        else:
#            selected = [self.legend.isSelected(it) for it in range(self.legend.numRows())]
#            current = self.legend.currentItem()

            selected = [d for d in self.graph.datasets if hasattr(d, '_item') and d._item.isSelected()]

            worksheets = set(d.worksheet for d in self.graph.datasets)

            self.legend.clear()

            for w in worksheets:
                strings = ["%s(%s)"%(d.y.name, d.x.name) for d in self.graph.datasets if d.worksheet == w]

                item = LVI(self.legend, w.name)
                item.setOpen(True)
                item.setSelectable(False)

                for d in self.graph.datasets:
                    if d.worksheet == w:
                        d._item = QListViewItem(item, "%s(%s)"%(d.y.name, d.x.name))
                        d._item.setPixmap(0, self.draw_pixmap(d))
                    
                for d in selected:
                    d._item.setSelected(True)

#                item = QListBoxItem()
#                item.setSelectable(False)
#                item.setText('<'+w.name+'>')
#                self.legend.insertItem(item)

#                self.legend.insertStrList(strings)
#                for n, dset in enumerate(self.graph.datasets):
#                    if hasattr(dset, '_curveid'):
#                        self.legend.changeItem(self.draw_pixmap(dset), self.legend.text(n), n)

#            for i,on in enumerate(selected):
#                self.legend.setSelected(i, on)
#            self.legend.setCurrentItem(current)
            self.needs_legend_update = False

    def on_legend_select(self):
#        self.datasets = [self.graph.datasets[n] for n in range(self.legend.count())
#                                                if self.legend.isSelected(n)]
        self.datasets = [d for d in self.graph.datasets if hasattr(d, '_item') and d._item.isSelected()]
        self.graph.emit('selection-changed', self.datasets)

    def on_context_menu_rename(self):
        self.context_item._tree_item.startRename(0)

    def on_context_menu_delete(self):
        self.project.remove(self.context_item.id)

    def on_legend_cmenu(self, item, point):
        self.context_menu = QPopupMenu(self)
        self.context_menu.insertItem('Hide', self.on_context_menu_delete)
        self.context_menu.insertItem('Full range', self.on_context_menu_delete)
        self.context_menu.insertItem('Show only', self.on_context_menu_rename)
        self.context_menu.insertSeparator ()
#        self.context_menu.insertItem ('Delete', self.wsheet_context_menu_del)
#        self.context_menu.insertItem ('Import ASCII...', self.wsheet_context_menu_importascii)

#        self.context_item = item._object
        self.context_menu.popup(point)
 
    def on_add_function_term(self, term):
        term._curve = curve = ErrorBarPlotCurve(self.plot)
        term._curveid = self.plot.insertCurve(curve)

    def on_remove_function_term(self, term):
        self.plot.removeCurve(term._curveid)

    def on_add_dataset(self, d):
        d._curve = curve = ErrorBarPlotCurve(self.plot, errorPen = QPen(Qt.black))
        d._curveid = self.plot.insertCurve(curve)
        d.recalculate()
        for s in ['symbol', 'color', 'size', 'linetype', 'linestyle', 'linewidth']:
            self.on_change_style([d])#, s, d.get_style(s))
        self.redraw()
        self.update_legend()
     
    def on_remove_dataset(self, d):
        self.plot.removeCurve(d._curveid)
        self.redraw()
        self.update_legend()

    def draw_pixmap(self, dataset):
        p = QPixmap()
        p.resize(20, 10)
        p.fill(self.legend_background_color)
        paint = QPainter()
        paint.begin(p)

        paint.setPen(self.plot.curve(dataset._curveid).pen())
        paint.drawLine(2,5, 18,5)

        self.plot.curve(dataset._curveid).symbol().draw(paint, 10, 5)

#        if dataset in self.graph.fit_datasets():
#            paint.setPen(QPen(Qt.black, 1))
#            paint.setBrush(Qt.NoBrush)
#            paint.drawRect(2, 2, 16, 8)

        paint.end()
        p.setMask(p.createHeuristicMask())
        return p

    def on_zoom_changed(self, xmin, xmax, ymin, ymax):
        self.plot.setAxisScale(self.plot.xBottom, xmin, xmax)
        self.plot.setAxisScale(self.plot.yLeft, ymin, ymax)
        self.graph.function.emit('modified')
        self.redraw()

    def on_mouse_pressed(self, e):
        if self.tool is not None:
            return self.tool.mouse_pressed(e)

        x = self.plot.invTransform(self.plot.xBottom, e.pos().x())
        y = self.plot.invTransform(self.plot.yLeft, e.pos().y())

    def on_mouse_released(self, e):
        if self.tool is not None:
            return self.tool.mouse_released(e)

    def on_mouse_moved(self, e):
        if self.tool is not None:
            return self.tool.mouse_moved(e)


    def hittest(self, marker, x, y):
        """Check if the point (x,y) in pixel coordinates is on the marker label"""
        text = self.plot.markerLabel(marker)
        metrics = QFontMetrics(self.plot.markerFont(marker))
        size = metrics.size(0, text)
        mx, my = self.plot.markerPos(marker)
        mx, my = self.plot.transform(self.plot.xBottom, mx), self.plot.transform(self.plot.yLeft, my)

        return mx <= x <= mx+size.width() and my-size.height() <= y <= my

    def on_canvas_event(self, event):
        if event.type() == QEvent.KeyPress:
            print >>sys.stderr, event, event.key()
        return False

    def on_function_modified(self):
        if self.graph.xtype == 'log':
            x = 10.**arange(log10(self.graph.xmin), log10(self.graph.xmax),
                            log10(self.graph.xmax/self.graph.xmin)/100)
        else:
            x = arange(self.graph.xmin, self.graph.xmax, (self.graph.xmax-self.graph.xmin)/100)

        for term in self.graph.function.terms:
            if term.enabled:
                self.plot.setCurveData(term._curveid, x, term(x))
        self.plot.setCurveData(self.graph.function._curveid, x, self.graph.function(x))
        self.redraw()

    def on_recalc(self, d, x, y):
        d._curve.setData(x, y)#, [1]*len(x), [1]*len(y))
        self.redraw()

    def on_change_style(self, datasets):
        for d in datasets:
            curve = self.plot.curve(d._curveid)

            curve.symbol().setStyle(qsymbols[d.style.symbol])

            if d.style.fill == 'open':
                brush = qfills['open']
            elif d.style.fill == 'filled':
                brush = QBrush(qcolors[colors.index(d.style.color)])
            else:
                brush = QBrush(qcolors[colors.index(d.style.color)])
            curve.symbol().setBrush(brush)

            color = qcolors[colors.index(d.style.color)]
            curve.symbol().brush().setColor(color)
            curve.symbol().pen().setColor(color)
            curve.pen().setColor(color)

            curve.symbol().setSize(d.style.size)
            
            curve.setStyle(qlinetypes[linetypes.index(d.style.linetype)])

            curve.pen().setStyle(qlinestyles[linestyles.index(d.style.linestyle)])

            curve.pen().setWidth(d.style.linewidth)

        self.redraw()
        self.update_legend()
        self.mainwin.graph_style.on_selection_changed()

class FitOptions(FitOptionsUI):
    pass


class FunctionsWindow(FunctionsWindowUI):
    def __init__(self, parent, fitwin):
        FunctionsWindowUI.__init__(self, parent)
        self.fitwin = fitwin
        self.fill()
        self.functions.header().hide()
        self.updating = False
        self.func = None

        self.categories = {}

    def fill(self):
        self.functions.clear()
        categories = {}
        for catname in set(f.name.split('/')[0] for f in registry if '/' in f.name):
            categories[catname] = QListViewItem(self.functions, catname)
            categories[catname].setOpen(True)
            categories[catname].setPixmap(0, getimage('folder'))
            categories[catname].setSelectable(False)
            categories[catname].category = True

        for function in registry:
            if '/' in function.name:
                parent = categories[function.name.split('/')[0]]
            else:
                parent = self.functions
            item = QListViewItem(parent, function.short)
            item.setPixmap(0, getimage('function'))
            item.funcname = function.name

    def on_selection_changed(self):
        item = self.functions.selectedItem()
        if item is None or hasattr(item, 'category'):
            self.func = None
            self.tabs.setEnabled(False)
            self.browse.setText("")
        else:
            self.updating = True
            self.tabs.setEnabled(True)
            func = registry[item.funcname]

            if func.tex.strip() == '':
                pixmap = QPixmap()
            else:
                pixmap = QPixmap()
#                pixmap = mimetex(func.tex)

            QMimeSourceFactory.defaultFactory().setPixmap('mimetex', pixmap)
            if self.func is None or func.name != self.func.name:
                self.name.setText(func.name)
                self.parameters.setText(', '.join(func.parameters))
                self.equation.setText(func.text)
                desc = "<h2>%s</h2><hr><img src='mimetex'>"%(func.short,)
                self.browse.setText(desc)
                self.tex.setText(func.tex)
                self.desc.setText(func.desc)
                self.extra.setText(func.extra)
            self.func = func
            self.updating = False

    def on_delete(self):
        os.remove(self.func.filename)
        registry.rescan()
        self.fill()

    def on_new(self):
        num = 0
        while 'function%d.function'%num in (f.filename.split('/')[-1] for f in registry if f.filename is not None):
            num += 1
        self.function = Function('function%d'%num, [], 'y=f(x)', '')
        open(USERDATADIR+'/functions/function%d.function'%num, 'wb').write(self.function.tostring())
#        self.scan('functions')
        registry.rescan()
        self.fill()
        self.functions.setSelected(self.functions.findItem('function%d'%num, 0), True)

    def on_ui_changed(self):
        if self.func is None or self.updating:
            return
        self.func.name = unicode(self.name.text())
        self.func.parameters = [p.strip() for p in unicode(self.parameters.text()).split(',')]
        self.func.text = unicode(self.equation.text())
        self.func.desc = unicode(self.desc.text())
        self.func.tex = unicode(self.tex.text())
        self.func.extra = unicode(self.extra.text())
        self.func.save()
        registry.rescan()
        self.fill()
        self.functions.setSelected(self.functions.findItem(self.func.name, 0), True)

    def on_add_function_clicked(self):
        self.fitwin.add_function(self.func)

class MyLabel(QLabel):
    def __init__(self, parent, term, n):
        self.term, self.n = term, n
        QLabel.__init__(self, self.term.function.parameters[n], parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            menu = QPopupMenu()
            
            menu.insertItem('Limits', 1)
            id = menu.exec_loop(self.mapToGlobal(event.pos()))
            if id == 1:
                limits = self.term.limits
                fr, to = limits[self.n]
                if fr is None: fr = ''
                if to is None: to = ''
                p = Page(None, ('Limits', ['From', 'To']), **{'From': fr, 'To': to})
                p.run()
                fr, to = efloat(p['From']), efloat(p['To'])
                if isnan(fr): fr = None
                if isnan(to): to = None
                limits[self.n] = (fr, to)
                self.term.limits = limits


class MyButton(QPushButton):
    def __init__(self, parent, term):
        self.term = term
        QPushButton.__init__(self, term.name, parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            menu = QPopupMenu()
            
            menu.insertItem('Rename', 1)
            id = menu.exec_loop(self.mapToGlobal(event.pos()))
            if id == 1:
                p = Page(None, ('Rename', ['Name']), **{'Name': self.term.name})
                p.run()
                self.term.name = p['Name']
                self.setText(self.term.name)
        else:
            QPushButton.mousePressEvent(self, event)



class GraphFit(GraphFitUI):
    def __init__(self, parent, mainwin):
        GraphFitUI.__init__(self, parent)
        self.mainwin = mainwin
        self.graph = None

        self.scrolled = QScrollView(self)
        self.layout().add(self.scrolled)
        self.scrolled.setVScrollBarMode(QScrollView.AlwaysOn)
        self.scrolled.setHScrollBarMode(QScrollView.AlwaysOff)
        self.box = QVBox(self.scrolled)
        self.scrolled.addChild(self.box)

        self.toggling = False
        self.active_term = None

    def on_function_clicked(self):
        FunctionsWindow(self.mainwin, self).exec_loop()

    def on_fitoptions_clicked(self):
        FitOptions(self.mainwin).exec_loop()

    def set_graph(self, graph):
        if self.graph is not None:
            self.function.disconnect('add-term', self.on_add_term)
            self.function.disconnect('remove-term', self.on_remove_term)
            self.function.disconnect('modified', self.on_modified)
            for term in self.function.terms:
                term._box.close()
        self.graph = graph
        if self.graph is not None:
            self.function = self.graph.function
            self.function.connect('add-term', self.on_add_term)
            self.function.connect('remove-term', self.on_remove_term)
            self.function.connect('modified', self.on_modified)
            for term in self.function.terms:
                self.on_add_term(term)

    def on_add_term(self, term):
        term._box = box = QVBox(self.box)
        box.setMaximumSize(QSize(135,3000))
        buttons = QHBox(box)
        term._butt = MyButton(buttons, term)
        term._butt.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed))
        term._butt.setToggleButton(True)
        self.connect(term._butt, SIGNAL("toggled(bool)"), self.on_toggle(term))
        hidebtn = QToolButton(buttons)
        self.connect(hidebtn, SIGNAL("toggled(bool)"), self.on_hide(term))
        hidebtn.setText('^')
        hidebtn.setMinimumSize(QSize(20,0))
        hidebtn.setToggleButton(True)
        hidebtn.setOn(False)
        hidebtn.setAutoRaise(True)
        closebtn = QToolButton(buttons)
        self.connect(closebtn, SIGNAL("clicked()"), self.on_close(term))
        closebtn.setText('x')
        closebtn.setMinimumSize(QSize(20,0))
        closebtn.setAutoRaise(True)

        term._grid = grid = QGrid(3, box)

        term._text = []
        term._lock = []
        for n, par in enumerate(term.function.parameters):
            label = MyLabel(grid, term, n)
            edit = QLineEdit(grid)
            edit.setMinimumSize(QSize(50, 0))
            self.connect(edit, SIGNAL("returnPressed()"), self.on_activate)
            self.connect(edit, SIGNAL("lostFocus()"), self.on_activate)
#            limits = QPushButton('L', grid)
#            limits.setMinimumSize(QSize(15, 0))
            lock = QCheckBox(grid)
            term._text.append(edit)
            term._lock.append(lock)
        box.show()
        self.on_modified()

    def on_close(self, term):
        def close():
            self.function.remove(self.function.terms.index(term))
        term._close = close
        return close

    def on_toggle(self, term):
        def toggle(on):
            if on and not self.toggling:
                self.toggling = True
                for t in self.function.terms:
                    t._butt.setOn(t==term)
                self.toggling = False
                self.active_term = term
        term._toggle = toggle
        return toggle

    def on_hide(self, term):
        def hide(on):
            if on:
                term._grid.hide()
                term.enabled = False
            else:
                term._grid.show()
                term.enabled = True
        term._hide = hide
        return hide

    def on_remove_term(self, term):
        term._box.close()

    def on_modified(self):
        for term in self.function.terms:
            if hasattr(term, '_text'):
                for i, txt in enumerate(term._text):
                    txt.setText(str(term.parameters[i]))

    def on_fit_clicked(self):
        data = self.graph._view.datasets[0]
#        lock = [check.isOn() for term in self.function.terms if term.enabled for check in term._lock]
        for term in self.function.terms:
            term.locks = [check.isOn() for check in term._lock]
        ind = data.active_data()
        self.function.fit(data.x[ind], data.y[ind], None, 50)
        self.function.emit('modified')


    def add_function(self, f):
        n = 0
        while 'f%d'%n in [t.name for t in self.function.terms]:
            n+= 1
        self.function.add(f.name, 'f%d'%n)
    
    def on_activate(self):
        for t in self.function.terms:
            t.parameters = [efloat(unicode(p.text())) for p in t._text]
        self.function.emit('modified')

class GraphAxes(GraphAxesUI):
    def __init__(self, parent, mainwin):
        GraphAxesUI.__init__(self, parent)
        self.mainwin = mainwin
        self.graph = None
        self.updating = False

    def set_graph(self, graph):
        if self.graph is not None:
            self.graph.disconnect('set-title', self.on_set_title)
            self.graph.disconnect('set-scale', self.on_set_scale)
        self.graph = graph
        if self.graph is not None:
            self.graph.connect('set-title', self.on_set_title)
            self.graph.connect('set-scale', self.on_set_scale)

            self.on_set_title('x', self.graph.xtitle)
            self.on_set_title('y', self.graph.ytitle)
            self.on_set_scale('x', self.graph.xtype)
            self.on_set_scale('y', self.graph.ytype)

    def on_set_title(self, axis, title):
        self.updating = True
        {'x':self.xtitle,'y':self.ytitle}[axis].setText(title)
        self.updating = False

    def on_set_scale(self, axis, scale):
        self.updating = True
        {'x':self.xscale,'y':self.yscale}[axis].setCurrentItem(['linear','log'].index(scale))
        self.updating = False

    def on_ui_changed(self):
        if self.updating:
            return
        self.graph.xtype = ['linear','log'][self.xscale.currentItem()]
        self.graph.ytype = ['linear','log'][self.yscale.currentItem()]
        self.graph.xtitle = unicode(self.xtitle.text())
        self.graph.ytitle = unicode(self.ytitle.text())

class GraphStyle(GraphStyleUI):
    def __init__(self, parent, mainwin):
        GraphStyleUI.__init__(self, parent)
        self.mainwin = mainwin

        for c in qcolors:
            p = QPixmap()
            p.resize(30, 10)
            p.fill(c)
            self.color.insertItem(p)

        for l in qlinestyles:
            p = QPixmap()
            p.resize(50, 10)
            paint = QPainter()
            pen = QPen(Qt.black)
            pen.setStyle(l)
            p.fill(Qt.white)
            paint.begin(p)
            paint.setPen(pen)
            paint.drawLine(0,5, 30,5)
            paint.end()
            p.setMask(p.createHeuristicMask())
            self.lstyle.insertItem(p)

        brush = qfills['filled']
        pen = QPen()
        for l in symbols:
            p = QPixmap()
            p.resize(12,12)
            paint = QPainter()
            p.fill(Qt.white)
            paint.begin(p)
            QwtSymbol(qsymbols[l], brush, pen, QSize(10, 10)).draw(paint, 6, 6)
            paint.end()
            p.setMask(p.createHeuristicMask())
            self.shape.insertItem(p)

        self.graph = None

        self.widgets = [self.shape, self.fill, self.size, self.color, 
                        self.ltype, self.lstyle, self.lwidth]

        self.checks = [self.shape_ch, self.fill_ch, self.size_ch, self.color_ch,
                       self.ltype_ch, self.lstyle_ch, self.lwidth_ch]

        self.updating = False
        self.datasets = []

    def set_graph(self, graph):
        if self.graph is not None:
            self.graph.disconnect('selection-changed', self.on_selection_changed)
        self.graph = graph
        if self.graph is not None:
            self.graph.connect('selection-changed', self.on_selection_changed)

    def set_from_dataset(self, dataset):
        """Updates the gui to reflect the style of a dataset"""
        style = dataset.style
        self.shape.setCurrentItem(symbols.index(style.symbol))
        self.fill.setCurrentItem(fills.index(style.fill))
        self.color.setCurrentItem(colors.index(style.color))
        self.size.setValue(style.size)
        self.ltype.setCurrentItem(linetypes.index(style.linetype))
        self.lstyle.setCurrentItem(linestyles.index(style.linestyle))
        self.lwidth.setValue(style.linewidth)

      
    def on_group_changed(self):
        self.on_selection_changed(self.datasets)

    def on_selection_changed(self, datasets=None):
        if datasets == None:
            datasets = self.datasets
        else:
            self.datasets = datasets
        if not hasattr(self.graph, '_view'):
            return
        self.updating = True
        try:
            if self.graph._view.frozen or len(datasets) == 0:
                return

            self.set_from_dataset(datasets[0])

            if len(datasets) == 1: # single
                self.group.setEnabled(False)
                for w in self.checks:
                    w.setChecked(True)
                    w.hide()

                for w in self.widgets:
                    w.setEnabled(True)
            else:
                self.group.setEnabled(True)

                for w in self.checks:
                    w.show()

                if self.group.currentItem() == 0: # identical
                    for prop, widget, check in zip(attrs, self.widgets, self.checks):
                        thesame = len(set(getattr(d.style, prop) for d in datasets))==1
                        check.setChecked(thesame)
                        widget.setEnabled(thesame)
                elif self.group.currentItem() == 1: # series
                    for prop, widget, check in zip(attrs, self.widgets, self.checks):
                        if prop == 'color': # can do series
                            dcolors = [colors.index(d.style.color) for d in datasets]
                            c0 = dcolors[0]
                            series = dcolors==[c % len(colors) for c in range(c0, c0+len(colors))]
                            check.setChecked(series)
                            widget.setEnabled(series)
                        else:
                            check.setChecked(False)
                            check.hide()
                            widget.setEnabled(False)
        finally:
            self.updating = False

    def on_checks_changed(self):
        for prop, widget, check in zip(attrs, self.widgets, self.checks):
            widget.setEnabled(check.isOn())
        self.on_ui_changed()

    def on_ui_changed(self):
        if self.updating:
            return

        cattrs = [attr for attr, check in zip(attrs, self.checks) if check.isOn()]
        series = self.group.currentItem() == 1

        self.graph._view.freeze()
        style = {
            'symbol': symbols[self.shape.currentItem()],
            'fill': fills[self.fill.currentItem()],
            'color': colors[self.color.currentItem()],
            'linetype': linetypes[self.ltype.currentItem()],
            'linestyle': linestyles[self.lstyle.currentItem()],
            'size': self.size.value(),
            'linewidth': self.lwidth.value(),
        }

        for attr in attrs:
            if attr not in cattrs:
                del style[attr]
        self.graph.set_style(self.datasets, cattrs*series, **style)
            
        self.graph._view.unfreeze()


class GraphData(GraphDataUI):
    def __init__(self, parent, mainwin):
        GraphDataUI.__init__(self, parent)
        self.worksheet_list.header().hide()
        self.mainwin = mainwin
        self.project = None
        self.splitter.setSizes([100,100,100])

    def set_graph(self, graph):
        self.graph = graph

    def on_wslist_select(self):
        selected = []
        it = QListViewItemIterator(self.worksheet_list)
        while it.current():
            if it.current().isSelected() and isinstance(it.current()._object, Worksheet):
                selected.append(it.current()._object)
            it += 1
        self.selected = selected
        self.x_list.clear()
        self.y_list.clear()

        if selected == []:
            return

        colnames = list(reduce(set.intersection, (set(w.column_names) for w in selected)))
        colnames.sort(key=selected[0].column_names.index)

        self.x_list.insertStrList(colnames)
        self.y_list.insertStrList(colnames)

    def on_add(self):
        try:
            self.graph._view.freeze()
            xcols = [str(self.x_list.text(a)) for a in range(self.x_list.count()) if self.x_list.isSelected(a)]
            ycols = [str(self.y_list.text(a)) for a in range(self.y_list.count()) if self.y_list.isSelected(a)]

            for w in self.selected:
                for x in xcols:
                    for y in ycols:
                        self.graph.add(w[x], w[y])
        finally:
            self.graph._view.unfreeze()

    def on_remove(self):
        try:
            self.graph._view.freeze()
            for d in self.graph._view.datasets:
                self.graph.remove(d)
        finally:
            self.graph._view.unfreeze()

    def set_project(self, project):
        if self.project is not None:
            self.project.top.disconnect('modified', self.on_mod)
            self.project.disconnect('add-item', self.on_mod)
            self.project.disconnect('remove-item', self.on_mod)
        self.project = project
        if self.project is not None:
            self.project.top.connect('modified', self.on_mod)
            self.project.connect('add-item', self.on_mod)
            self.project.connect('remove-item', self.on_mod)
            self.on_mod()

    def on_mod(self, item=None):
        self.worksheet_list.clear()
        self.on_add_item(self.project.top, parent=self.worksheet_list)
        self.project.top._gd_item.setOpen(True)

    def on_add_item(self, obj, parent):
        item = ListViewItem(parent, obj)
        if isinstance(obj, Folder):
            for child in obj:
                if isinstance(child, (Folder, Worksheet)):
                    self.on_add_item(child, parent=item)
