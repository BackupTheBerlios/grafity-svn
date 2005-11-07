import sys
import datetime
import os
import sets
import shutil

sys.modules['__main__'].splash_message('loading Graph')

from qt import *
from qwt.qplt import *
from qwt import QwtSymbol
from math import *
from scipy import *

import grafit.lib.ElementTree as xml

from grafit.utils import intersection, all_the_same, pyget, pyset, Page
from grafit.project import project
from grafit.fit import FitWindow, ChangeFitDatasets, ChangeParameterValue
from grafit.utils import Command, CompositeCommand, AutoCommands

def eq_or_none(x, y):
    return (x == y) or (x is None) or (y is None)

class Dataset (object):
    __metaclass__ = AutoCommands

    def __init__ (self, worksheet, colx, coly, rangemin=None, rangemax=None):
        self.wsname = None
        self._rangemin, self._rangemax = None, None
        self.graph = None
        if worksheet is None:
            return
        self.worksheet = worksheet
        self.colx = colx
        self.coly = coly
        self._rangemin, self._rangemax = self.range_limits()
        if rangemin != None: 
            self._rangemin = rangemin
        if rangemax != None: 
            self._rangemax = rangemax
        for prop in self.props:
            self._make_property (prop)
        self.hidefit = False
        self.properties = {}

    def to_element(self):
        # data
        delem = xml.Element ("Dataset")
        delem.tail = '\n'
        pyset (delem, "worksheet", self.worksheet.name)
        pyset (delem, "xcolumn", self.colx)
        pyset (delem, "ycolumn", self.coly)
        pyset (delem, "range", (self.rangemin, self.rangemax))
        # line and symbol style
        for prop in Dataset.props:
            pyset(delem, prop, self.get_curve_style(prop))
        return delem

    def from_element(self, delem, graph, position=None):
        # data
        graph.freeze()
        self.wsname = pyget (delem, "worksheet")
        self.graph = graph
        self.colx = pyget (delem, "xcolumn")
        self.coly = pyget (delem, "ycolumn")
        self._rangemin, self._rangemax = pyget (delem, "range")
        graph.add(project[self.wsname], self.colx, self.coly, self.rangemin, self.rangemax, position=position)
        if position is None:
            position = -1
        # line and symbol styles
        for prop in Dataset.props:
            try:
                graph.datasets[position].set_curve_style(prop, pyget(delem, prop))
            except TypeError:
                pass
        graph.unfreeze()

    def _get_worksheet(self):
        if self.wsname is not None:
            return project[self.wsname]
        else:
            return None
    def _set_worksheet(self, value):
        self.wsname = value.name
    worksheet = property(_get_worksheet, _set_worksheet)

    def _get_graph(self):
        if self.grname is None:
            return None
        else:
            return project.g[self.grname]
    def _set_graph(self, value):
        if value is None:
            self.grname = None
        else:
            self.grname = value.name
    graph = property(_get_graph, _set_graph)

    def _set_range__init(cmd, graph, datasets, oldmin, oldmax, newmin, newmax):
        cmd.datasets = [d.index() for d in datasets]
        cmd.graph = graph
        cmd.oldmin, cmd.oldmax = oldmin, oldmax
        cmd.newmin, cmd.newmax = newmin, newmax
#        self.pixmap = QPixmap(project.datadir + 'pixmaps/range.png')

    def _set_range__do(cmd):
        self = project[cmd.graph]
        for d in cmd.datasets:
            ds = self.datasets[d]
            if cmd.newmin is not None:
                ds._rangemin = cmd.newmin
            if cmd.newmax is not None:
                ds._rangemax = cmd.newmax
            ds.update()
        return cmd
       
    def _set_range__undo(cmd):
        self = project[cmd.graph]
        for d in cmd.datasets:
            ds = self.datasets[d]
            if cmd.oldmin is not None:
                ds._rangemin = cmd.oldmin
            if cmd.oldmax is not None:
                ds._rangemax = cmd.oldmax
            ds.update()
        return cmd


    def _set_rangemin(self, value):
            self.set_range___(self.graph.name, [self], self.rangemin, None, value, None).do().register()
    def _get_rangemin(self):
        return self._rangemin
    rangemin = property(_get_rangemin, _set_rangemin)

    def _set_rangemax(self, value):
            self.set_range___(self.graph.name, [self], None, self.rangemax, None, value).do().register()
    def _get_rangemax(self):
        return self._rangemax
    rangemax = property(_get_rangemax, _set_rangemax)


    props = [ 'symbol_style', 'symbol_fill', 'symbol_size', 'symbol_color',
              'line_type', 'line_style', 'line_width' ]

    def label (self):
        l = "%s: %s(%s)" % (self.worksheet.name, self.coly, self.colx)
        if self in self.graph.fit_datasets():
            l = '[%d] %s' % (self.graph.fit_datasets().index(self), l)
        return l

    def range_limits (self, ignore_range = True):
        x = self.x(ignore_range)
        try:
            return (min(x), max(x))
        except ValueError:
            return (0., 1.)

    def range_limits_y (self, ignore_range = True):
        y = self.y(ignore_range)
        try:
            limits = (min(y), max(y))
        except ValueError:
            return (1.e20, -1.e20)
        else:
            return limits

    def data(self, ignore_range = False): 
        xall = self.worksheet[self.colx].data
        yall = self.worksheet[self.coly].data
        leng = min(len(xall), len(yall))
        xall = xall[:leng]
        yall = yall[:leng]

        mask = isfinite(xall) & isfinite(yall)

        if self._rangemin != None and not ignore_range:
            mask &= greater_equal(xall, self.rangemin) & less_equal(xall, self.rangemax)

        indices = compress(mask, arange(len(xall)))
        return take(xall, indices), take(yall, indices), indices

    def x(self, ignore_range = False): 
        return self.data(ignore_range)[0]
    def y(self, ignore_range = False): 
        return self.data(ignore_range)[1]

    def index (self):
        return self.graph.datasets.index(self)

    def update(self):
        data = self.data()
        self.graph.plot.setCurveData (self.curveid, data[0], data[1])
        self.graph.redraw()

# properties

    line_types = [QwtCurve.NoCurve, QwtCurve.Lines, QwtCurve.Spline]
    line_styles = [Qt.SolidLine, Qt.DashLine, Qt.DotLine, Qt.DashDotLine, Qt.DashDotDotLine]

    def _set_style__init(cmd, graph, datasets, style, old, new):
        cmd.datasets = [d.index() for d in datasets]
        cmd.graph = graph
        cmd.style, cmd.old, cmd.new = style, old, new

    def _set_style__do(cmd):
        import traceback
        project[cmd.graph].freeze()
        for d in cmd.datasets:
            ds = project[cmd.graph].datasets[d]
            ds._set_curve_style(cmd.style, cmd.new)
        project[cmd.graph].unfreeze()
        return cmd

    def _set_style__undo(cmd):
        project[cmd.graph].freeze()
        for d in cmd.datasets:
            ds = project[cmd.graph].datasets[d]
            ds._set_curve_style(cmd.style, cmd.old)
        project[cmd.graph].unfreeze()
        return cmd

    def set_curve_style(self, property, value):
        if self.get_curve_style(property) == value:
            return
        self.set_style___(self.graph.name, [self], property, self.get_curve_style(property),
                                        value).do().register()
 
    def _set_curve_style (self, property, value):
        prev = self.get_curve_style(property)
        print >>sys.stderr, value
        if prev == value:
            return
        if property == 'symbol_style':
            self.graph.plot.curve(self.curveid).symbol().setStyle (QwtSymbol.Style(value))
        elif property == 'symbol_fill':
            self.graph.plot.curve(self.curveid).symbol().brush().setStyle (Qt.BrushStyle(value))
        elif property == 'symbol_size':
            self.graph.plot.curve(self.curveid).symbol().setSize (value)
        elif property == 'symbol_color':
            self.graph.plot.curve(self.curveid).symbol().brush().setColor (colors[value])
            self.graph.plot.curve(self.curveid).symbol().pen().setColor (colors[value])
            self.graph.plot.curve(self.curveid).pen().setColor (colors[value])
        elif property == 'line_type':
            self.graph.plot.curve(self.curveid).setStyle(self.line_types[value])
        elif property == 'line_style':
            self.graph.plot.curve(self.curveid).pen().setStyle (self.line_styles[value])
        elif property == 'line_width':
            self.graph.plot.curve(self.curveid).pen().setWidth (value)
        else:
            raise NameError
        self.graph.redraw()
        self.graph.legend.update()

    def get_curve_style (self, property):
        if property == 'symbol_style':
            return self.graph.plot.curve(self.curveid).symbol().style ()
        elif property == 'symbol_fill':
            return self.graph.plot.curve(self.curveid).symbol().brush().style ()
        elif property == 'symbol_size':
            return self.graph.plot.curve(self.curveid).symbol().size().height()
        elif property == 'symbol_color':
            return colors.index(self.graph.plot.curve(self.curveid).symbol().brush().color())
        elif property == 'line_type':
            return self.line_types.index(self.graph.plot.curve(self.curveid).style())
        elif property == 'line_style':
            return self.line_styles.index(self.graph.plot.curve(self.curveid).pen().style())
        elif property == 'line_width':
            return self.graph.plot.curve(self.curveid).pen().width ()
        else:
            raise NameError

    def _make_property (self, prop):
        def get_property (self): return self.get_curve_style (prop)
        def set_property (self, val): self.set_curve_style (prop, val)
        setattr (self.__class__, prop, property(get_property, set_property))

from grafit.graph_properties import colors
from grafit.utils import EventHandler, connectevents

#
# Axis commands
#

class AxisZoomCommand(Command):
    def __init__(self, axis, oldmin, oldmax, newmin, newmax):
        self.graph = axis.graph.name
        if axis == axis.graph.xaxis:
            self.which = 'x'
        elif axis == axis.graph.yaxis:
            self.which = 'y'
        self.oldmin, self.oldmax = oldmin, oldmax
        self.newmin, self.newmax = newmin, newmax
        self.pixmap = QPixmap(project.datadir + 'pixmaps/zoom.png')

    def do(self):
        self.axis = getattr(project[self.graph], self.which+'axis')

        if self.newmin is not None:
            self.axis.min = self.newmin
        if self.newmax is not None:
            self.axis.max = self.newmax
       
    def undo(self):
        self.axis = getattr(project[self.graph], self.which+'axis')
        if self.oldmin is not None:
            self.axis.min = self.oldmin
        if self.oldmax is not None:
            self.axis.max = self.oldmax

class AxisScaleCommand(Command):
    def __init__(self, axis, value, prev):
        self.axis, self.value, self.prev = axis, value, prev
        self.pixmap = QPixmap(project.datadir + 'pixmaps/zoom.png')

    def do(self):
        self.axis.logscale = self.value

    def undo(self):
        self.axis.logscale = self.prev

class AxisTitleCommand(Command):
    def __init__(self, axis, value, prev):
        self.axis, self.value, self.prev = axis, value, prev
        self.pixmap = QPixmap(project.datadir + 'pixmaps/zoom.png')

    def do(self):
        self.axis.title = self.value

    def undo(self):
        self.axis.title = self.prev

class Axis(object):
    """Axis controls"""
    def __init__(self, graph, qwtaxis):
        self.graph, self.qwtaxis = graph, qwtaxis
        self.graph.plot.axis(qwtaxis).setBaselineDist(0)
        self.graph.plot.axis(qwtaxis).setBorderDist(0,0)

        connectevents(self.graph.plot.axis(self.qwtaxis), self.on_event)

    def _get_min(self): return self.graph.plot.axisScale(self.qwtaxis).lBound()
    def _set_min(self, value): 
        project.undolist.append(AxisZoomCommand(self, self.min, None, value, None))
        self.graph.plot.setAxisScale(self.qwtaxis, value, self.max)
        self.graph.update_function_curves()
        self.graph.redraw()
    min = property(_get_min, _set_min)

    def _get_majstep(self): 
        if self.logscale:
            return 1.0
        else:
            return self.graph.plot.axisScale(self.qwtaxis).majStep()
    majstep = property(_get_majstep)

    def _get_max(self): return self.graph.plot.axisScale(self.qwtaxis).hBound()
    def _set_max(self, value): 
        project.undolist.append(AxisZoomCommand(self, None, self.max, None, value))
        self.graph.plot.setAxisScale(self.qwtaxis, self.min, value)
        self.graph.update_function_curves()
        self.graph.redraw()
    max = property(_get_max, _set_max)

    def _get_logscale(self): return self.graph.plot.axisScale(self.qwtaxis).logScale()
    def _set_logscale(self, logp): 
        project.undolist.append(AxisScaleCommand(self, logp, self.logscale))
        self.graph.plot.changeAxisOptions (self.qwtaxis, Logarithmic, logp)
        self.graph.redraw()
    logscale = property(_get_logscale, _set_logscale)

    def _get_title(self): return str(self.graph.plot.axisTitle(self.qwtaxis))
    def _set_title(self, value): 
        project.undolist.append(AxisTitleCommand(self, value, self.title))
        self.graph.plot.setAxisTitle(self.qwtaxis, value)
    title = property(_get_title, _set_title)
   
    def increment (self):
        if self.logscale:
            incr = 10**((Numeric.log10(self.max) - Numeric.log10(self.min)) / 250.)
        else:
            incr = (self.max - self.min) / 250.
        return incr

    def axis_context_menu_log(self):
        self.logscale = not self.logscale

    def axis_context_menu_properties(self):
        propsdlg = Graph_Properties_Dlg (self.graph)
        propsdlg.tabs.setCurrentPage (2)
        if self.qwtaxis == QwtPlot.xBottom:
            propsdlg.axisselect.setCurrentItem (propsdlg.axisselect.firstItem())
        elif self.qwtaxis == QwtPlot.yLeft:
            propsdlg.axisselect.setCurrentItem (propsdlg.axisselect.lastItem())
        propsdlg.exec_loop()
 
    def on_axis_context_menu_requested(self, x, y):
        menu = QPopupMenu(self.graph.tabs)
        id = menu.insertItem('Logarithmic', self.axis_context_menu_log)
        menu.setItemChecked(id, self.logscale) 
        menu.insertSeparator()
        menu.insertItem('Properties...', self.axis_context_menu_properties)
        menu.insertSeparator()
        menu.popup(QPoint(x, y))

    def on_event (self, event):
        if event.type() == QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton:
            self.axis_context_menu_properties()
            return True
        elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
            self.on_axis_context_menu_requested(event.globalX(), event.globalY())
            return True
        else:
            return False

    def pixel_to_value(self, xp):
        return self.graph.plot.invTransform(self.qwtaxis, xp)

class Legend(QListBox):
    def __init__(self, graph, parent):
        QListBox.__init__(self, parent)
        self.graph = graph

        self.setFrameShadow (QFrame.Plain)
        self.setFrameShape (QFrame.NoFrame)
        self.setSelectionMode(QListBox.Extended)
        self.connect(self, SIGNAL("selectionChanged()"),self.on_legend_select)
        self.connect(self, SIGNAL("doubleClicked(QListBoxItem*)"),self.on_legend_dblclk)
        self.connect(self, SIGNAL("contextMenuRequested(QListBoxItem*, const QPoint&)"), 
                     self.on_legend_context_menu_requested)
        self.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding)

        pal = QPalette(self.palette())
        cg = QColorGroup(pal.active())
        cg.setColor(QColorGroup.Base,cg.color(QColorGroup.Background))
        self.legend_background_color = cg.color(QColorGroup.Background)
        pal.setActive(cg)
        self.setPalette(pal)
        self.needs_updating = False
        self.shifted = False

    def legend_context_menu_remove(self):
        self.graph.remove(self.legend_context_menu_is_for)

    def legend_context_menu_duplicate(self):
        d = self.legend_context_menu_is_for
        d.worksheet[d.colx + '_'] = d.worksheet[d.colx]
        d.worksheet[d.coly + '_'] = d.worksheet[d.coly]
        self.graph.add(d.worksheet[d.colx + '_'], d.worksheet[d.coly + '_'], d.rangemin, d.rangemax)

    def legend_context_menu_hidefit(self, id):
        dataset = self.legend_context_menu_is_for
        if dataset.hidefit:
             dataset.hidefit = False
        else:
             dataset.hidefit = True
        self.graph.update_function_curves()

    def on_legend_context_menu_requested(self, item, point, menu=None):
        self.show_legend_context_menu(self.graph.datasets[self.index(item)], point)

    def show_legend_context_menu(self, dataset, point, menu=None):
        if menu is None:
            menu = QPopupMenu(self)
        menu.insertItem('Remove', self.legend_context_menu_remove)
        menu.insertItem('Duplicate', self.legend_context_menu_duplicate)
        menu.insertSeparator()
        id = menu.insertItem('Hide fit functions', self.legend_context_menu_hidefit)
        menu.setItemChecked(id, dataset.hidefit) 
        self.legend_context_menu_is_for = dataset
        menu.popup(point)

    def on_legend_select (self):
        dsets = self.graph.selected_datasets()
        if dsets != []:
            self.graph.plot.setMarkerXPos (self.graph.rangemin, min ([d.rangemin for d in dsets]))
            self.graph.plot.setMarkerXPos (self.graph.rangemax, max ([d.rangemax for d in dsets]))
            self.graph.redraw()
        dsets = intersection ([self.graph.fit_datasets(), self.graph.selected_datasets ()])
        if len(dsets) > 0:
            self.graph.selected_fit_dataset = dsets[0]
        else:
            self.graph.selected_fit_dataset = None

    def on_legend_dblclk (self, item):
        id = self.index(item)
        self.graph.fitwin.destroy_ui()
        old = self.graph.fitdatasets[:]

        if not self.shifted and len(self.graph.datasets) > 1 \
                and self.graph.datasets[id] not in self.graph.fitdatasets:
            self.graph.fitdatasets = [self.graph.datasets[id]]
        else:
            if self.graph.datasets[id] in self.graph.fitdatasets:
                self.graph.fitdatasets.remove (self.graph.datasets[id])
            else:
                self.graph.fitdatasets.append (self.graph.datasets[id])

        project.undolist.append(ChangeFitDatasets(self.graph, old, self.graph.fitdatasets[:]))
        self.update()

        self.graph.fitwin.build_ui()

    def draw_pixmap(self, dataset):
        p = QPixmap()
        p.resize (20, 10)
        p.fill (self.legend_background_color)

        paint = QPainter()
        paint.begin(p)


        paint.setPen (self.graph.plot.curve(dataset.curveid).pen())
        paint.drawLine (2,5, 18,5)

        self.graph.plot.curve(dataset.curveid).symbol().draw(paint, 10, 5)

        if dataset in self.graph.fit_datasets():
            paint.setPen(QPen(Qt.black, 1))
            paint.setBrush(Qt.NoBrush)
            paint.drawRect(2, 2, 16, 8)
        
        paint.end()
        p.setMask(p.createHeuristicMask())
        return p

    def update(self):
        if self.graph._frozen:
            self.needs_updating = True
            return
        self.needs_updating = False
        selected = [self.isSelected(it) for it in range(self.numRows())]
        current = self.currentItem()

        self.clear()
        self.insertStrList([d.label() for d in self.graph.datasets])
        for n, dset in enumerate(self.graph.datasets):
            self.changeItem(self.draw_pixmap(dset), self.text(n), n)

        for i,on in enumerate (selected):
            self.setSelected (i, on)
        self.setCurrentItem(current)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Control:
            self.shifted = True
        return QListBox.keyPressEvent(self, e)

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Control:
            self.shifted = False
        return QListBox.keyReleaseEvent(self, e)

class RangeCompositeCommand(CompositeCommand):
    def __init__(self, graph, *args, **kwds):
       CompositeCommand.__init__(self, *args, **kwds)
       self.graph = graph.name

    def do(self):
        project[self.graph].freeze()
        CompositeCommand.do(self)
        project[self.graph].unfreeze()

    def undo(self):
        project[self.graph].freeze()
        CompositeCommand.undo(self)
        project[self.graph].unfreeze()

class GraphView(QTabWidget):
    pass


class Graph(object):
    __metaclass__=AutoCommands
    def __init__(self, name = "__new_g", parent = None):
        if parent == None:
            parent = project.mainwin.workspace
        print >>sys.stderr, 'init'
        self.tabs = GraphView(parent)
        print >>sys.stderr, 'inits'
        self.tabs.graph = self
        self.tabs.setTabShape(self.tabs.Triangular)
        self.tabs.setTabPosition(self.tabs.Bottom)
        self.mainpage = QHBox(self.tabs)
        self.tabs.addTab(self.mainpage, 'graph')

        self.postscript = QLabel(self.tabs)
        self.tabs.addTab(self.postscript, 'preview')

        self.notes = QTextEdit(self.tabs)
        self.tabs.addTab(self.notes, 'notes')

        self.tabs.connect(self.tabs, SIGNAL('currentChanged(QWidget*)'), self.tab_changed)
        
        self._explorer_item = None

        self.datasets = []
        self.fitdatasets = []
        self._name = name
        self.name = name
        self._frozen = False

        self.selected_fit_dataset = None

        self.tabs.setIcon (QPixmap(project.datadir + 'pixmaps/graph.png'))
        print >>sys.stderr, 'initsi'
        self.bg_color = QColor('white')

        # plot
        self.plot = QwtPlot (self.mainpage, name)
        print >>sys.stderr, 'initsi3'
        self.plot.setCanvasBackground (self.bg_color)
        self.plot.enableGridX(True)
        self.plot.enableGridY(True)
        self.plot.setOutlineStyle (Qwt.Rect)
        self.plot.setAutoReplot(False)
        self.plot.canvas().setLineWidth(0)

        # plot events
        connectevents(self.plot.canvas(), self.on_canvas_event)
        self.tabs.connect(self.plot, SIGNAL('plotMouseMoved(const QMouseEvent&)'), self.onMouseMoved)
        self.tabs.connect(self.plot, SIGNAL('plotMousePressed(const QMouseEvent&)'), self.onMousePressed)
        self.tabs.connect(self.plot, SIGNAL('plotMouseReleased(const QMouseEvent&)'), self.onMouseReleased)

        # plot markers
        self.rangemin = self.plot.insertLineMarker (None, QwtPlot.xBottom)
        self.rangemax = self.plot.insertLineMarker (None, QwtPlot.xBottom)
        self.reader = self.plot.insertLineMarker (None, QwtPlot.xBottom)
        self.plot.setMarkerLineStyle (self.rangemin, QwtMarker.NoLine)
        self.plot.setMarkerLineStyle (self.rangemax, QwtMarker.NoLine)
        self.plot.setMarkerLineStyle (self.reader, QwtMarker.NoLine)
        self.moving_rangemin = self.moving_rangemax = False

        self.legbox = QVBox(self.mainpage)
        box = QSplitter(QSplitter.Vertical, self.legbox)
        box.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Expanding)
        self.legend = Legend(self, box)
        self.fitwin = FitWindow(self, box)
        self.fitwin.hide()
        self.fitbtn = QPushButton("Fit", self.legbox)
        self.fitbtn.setToggleButton(True)
        self.fitbtn.connect(self.fitbtn, SIGNAL("clicked()"), self.showfitclicked)

        self.xaxis = Axis(self, QwtPlot.xBottom)
        self.yaxis = Axis(self, QwtPlot.yLeft)
    
    def showfitclicked(self):
        if self.fitwin.isVisible():
            self.fitwin.hide()
        else:
            self.fitwin.show()

    def tab_changed(self, widget):
        if widget is self.postscript:
            self.postscript.setText('Hi')
            self.export('/tmp/tmptmptmptmp.png', 'PNG')
            im = QImage()
            im.load('/tmp/tmptmptmptmp.png')
            px = QPixmap()
            px.convertFromImage(im.smoothScale(self.postscript.parent().height(), self.postscript.parent().height()))
            self.postscript.setPixmap(px)

    def to_element (self):
        """an XML element representing the graph"""
        # root
        elem = xml.Element ('Graph')
        pyset (elem, "name", self.name)
        elem.tail = '\n'
        # axes
        for axis in [self.xaxis, self.yaxis]:
            aelem = xml.SubElement (elem, "Axis")
            aelem.tail = '\n'
            pyset (aelem, "id", axis.qwtaxis)
            pyset (aelem, "limits", (axis.min, axis.max)) 
            pyset (aelem, "logscale", axis.logscale)
            pyset (aelem, "title", axis.title) 
        # datasets
        for ds in self.datasets:
            # data
            delem = xml.SubElement (elem, "Dataset")
            delem.tail = '\n'
            pyset (delem, "worksheet", ds.worksheet.name)
            pyset (delem, "xcolumn", ds.colx)
            pyset (delem, "ycolumn", ds.coly)
            pyset (delem, "range", (ds.rangemin, ds.rangemax))
            # line and symbol style
            for prop in Dataset.props:
                pyset(delem, prop, ds.get_curve_style(prop))
        elem.append(self.fitwin.to_element())
        
        pyset(elem, "notes", str(self.notes.text()))
        return elem

    def from_element (self, elem):
        """starting with an empty graph, reconstruct the graph represented by an XML element"""
        # root
        self.freeze()
        self.name = pyget (elem, "name")
        # axes
        prog = project.mainwin.progressbar.progress()
        for aelem in elem.findall ('Axis'):
            axisid = pyget (aelem, "id")
            if axisid == QwtPlot.xBottom:
                axis = self.xaxis
            elif axisid == QwtPlot.yLeft:
                axis = self.yaxis
            else:
                continue
            axis.min, axis.max = pyget (aelem, "limits")
            axis.logscale = pyget (aelem, "logscale")
            axis.title = pyget (aelem, "title")
        # datasets
        for delem in elem.findall ('Dataset'):
            # data
            wsheet = project.w[pyget (delem, "worksheet")]
            colx = pyget (delem, "xcolumn")
            coly = pyget (delem, "ycolumn")
            rangemin, rangemax = pyget (delem, "range")
            ds = self.add(wsheet, colx, coly, rangemin, rangemax)
            # line and symbol styles
            for prop in Dataset.props:
                    ds.set_curve_style(prop, pyget(delem, prop))
        for delem in elem.findall ('FitWindow'):
            self.fitwin.from_element(delem)
        project.mainwin.progressbar.setProgress(prog+len(elem))
        try:
            self.notes.setText(pyget(elem, "notes"))
        except:
            pass
        self.unfreeze()

    def _get_name(self):
        return self._name
    def _set_name(self, name):
        if self not in project.graphs:
            self._name = name
        else:
            self.rename___(self.name, name).do().register()
    name = property(_get_name, _set_name)

    def _rename__init(cmd, wsname, newname):
        cmd.old, cmd.new = wsname, newname

    def _rename__do(cmd):
        self = project[cmd.old]
        name = cmd.new
#        if not re.match('^[a-zA-Z]\w*$', name):
#            raise NameError, "Invalid name for worksheet: %s" % name

        if self in project.graphs:
            try:
                del project.main_dict[self.name]
            except:
                pass
            project.main_dict[name] = self
        self._name = name
        for das in self.datasets:
            das.grname = name

        self.tabs.setName (name)
        self.tabs.setCaption (name)
        if self._explorer_item is not None:
            self._explorer_item.setText (0, name)
        return cmd

    def _rename__undo(cmd):
        cmd.old, cmd.new = cmd.new, cmd.old
        cmd.do()
        cmd.old, cmd.new = cmd.new, cmd.old
        return cmd

    def show(self):
        self.tabs.show()
    def hide(self):
        self.tabs.hide()
        

    def on_canvas_context_menu_requested(self, point):
        def add_export_item(menu, format):
            fmts = self.supported_export_formats()
            if format in fmts:
                menu.insertItem(format+'...', self.make_export_callback(format))

        menu = QPopupMenu(self.tabs)
        menu.insertItem('Preview Postscript...', self.preview_postscript)
        menu.exportmenu = QPopupMenu()
        menu.insertItem('Export', menu.exportmenu)
        add_export_item(menu.exportmenu, 'Gri')
        menu.exportmenu.insertSeparator()
        add_export_item(menu.exportmenu, 'PostScript')
        add_export_item(menu.exportmenu, 'PDF')
        menu.exportmenu.insertSeparator()
        add_export_item(menu.exportmenu, 'TIFF')
        add_export_item(menu.exportmenu, 'PNG')
        menu.popup(point)

    def make_export_callback(self, format):
        def callback():
            qfd = QFileDialog (project.mainwin)
            qfd.setMode (QFileDialog.AnyFile)
            if qfd.exec_loop() != 1:
                return False
            else:
                self.export(str(qfd.selectedFile()), format)

        setattr(self, 'export_'+format+'_callback', callback)

        return callback


    def preview_postscript(self):
        self.export('/tmp/grafit-preview.ps')
        os.system('gv /tmp/grafit-preview.ps')
 
    def on_dataset_context_menu_requested(self, dataset, point):
        menu = QPopupMenu(self.tabs)
        id = menu.insertItem(dataset.label())
        menu.changeItem(id, self.legend.draw_pixmap(dataset))
        menu.setItemEnabled(id, False)
        menu.insertSeparator()
        self.legend.show_legend_context_menu(dataset, point, menu)

    def on_canvas_event (self, event):
#        if event.type() == QEvent.MouseButtonDblClick and  event.button() == Qt.LeftButton:
#                project.undolist.begin_composite(RangeCompositeCommand 
#                                (self, name=('Change Graph %s Options' % self.name),
#                                 pixmap=QPixmap(project.datadir + 'pixmaps/properties.png')))
#                try:
#                    propsdlg = Graph_Properties_Dlg (self)
#                    if len(self.datasets) == 0:
#                        propsdlg.tabs.setCurrentPage (0)
#                    else:
#                        propsdlg.tabs.setCurrentPage (1)
#                    propsdlg.exec_loop()
#                finally:
#                    project.undolist.end_composite()
#                return True

        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton and Graph.graph_mode == 0:
            curve, dist, xval, yval, index = self.plot.closestCurve (event.x(), event.y())
            if dist > 5:
                self.on_canvas_context_menu_requested(QPoint(event.globalX(), event.globalY()))
            else:
                ds = [d for d in self.datasets if d.curveid == curve][0]
                self.on_dataset_context_menu_requested(ds, QPoint(event.globalX(), event.globalY()))
            return True
#        elif event.type() == QEvent.KeyPress
        return False

    def set_mode (self):
        self.plot.enableOutline (Graph.graph_mode == 1)

        if Graph.graph_mode == 2:
            self.plot.setMarkerLineStyle (self.rangemin, QwtMarker.VLine)
            self.plot.setMarkerLineStyle (self.rangemax, QwtMarker.VLine)
        else:
            self.plot.setMarkerLineStyle (self.rangemin, QwtMarker.NoLine)
            self.plot.setMarkerLineStyle (self.rangemax, QwtMarker.NoLine)
        if Graph.graph_mode == 3 or Graph.graph_mode == 4:
            self.plot.setMarkerLineStyle (self.reader, QwtMarker.Cross)
        else:
            self.plot.setMarkerLineStyle (self.reader, QwtMarker.NoLine)
        self.redraw()

    def _add_dataset__init(cmd, graph, ws, x, y, rangemin, rangemax, index):
        cmd.graph, cmd.index = graph, index
        cmd.ws, cmd.x, cmd.y, cmd.index = ws, x, y, index
        cmd.rmin, cmd.rmax = rangemin, rangemax

    def _add_dataset__do(cmd):
        self = project[cmd.graph] 
        d = Dataset(project[cmd.ws], cmd.x, cmd.y, cmd.rmin, cmd.rmax)
        d.graph = self

        d.funcs = []
        d.function = None
        d.curveid = self.plot.insertCurve (d.label())
        d.update()

        if cmd.index is None:
            self.datasets.append(d)
        else:
            self.datasets.insert(cmd.index, d)
        self.legend.update()
        self.redraw()
        self.last_dataset = d
        return cmd

#        project.g[self.graph].add_element(self.dataset, position=self.index)
       
    def _add_dataset__undo(cmd):
        project[cmd.graph].remove(cmd.index)
        return cmd


    def add(self, ws, x, y, rangemin=None, rangemax=None, position=None):
        self.add_dataset___(self.name, ws, x, y, rangemin, rangemax, position).do().register()
        return self.last_dataset

    def _remove_dataset__init(cmd, graph, index):
        cmd.graph, cmd.index = graph, index
        cmd.elem = project[graph].datasets[index].to_element()

    def _remove_dataset__do(cmd):
        self = project[cmd.graph]
        dataset = self.datasets[cmd.index]
        self.plot.removeCurve (dataset.curveid)
        self.datasets.remove(dataset)
        self.legend.update()
        self.redraw()
        return cmd
        
    def _remove_dataset__undo(cmd):
        dataset = Dataset(None, None, None)
        dataset.from_element(cmd.elem, project[cmd.graph], position=cmd.index)
        return cmd

 
    def remove (self, dataset):
        if isinstance(dataset, int):
            dataset = self.datasets[dataset]
        elif dataset is None:
            dataset = self.datasets[-1]
        if dataset in self.fit_datasets():
            QMessageBox.information(self, "grafit", 
                        "<b>Cannot remove</b><p>This dataset is being used in fitting")
            return

        self.remove_dataset___(self.name, dataset.index()).do().register()

       
    def update_function_curves (self):
        if self.xaxis.logscale:
            x = 10.**(Numeric.arange(Numeric.log10(self.xaxis.min),Numeric.log10(self.xaxis.max),
                      (Numeric.log10(self.xaxis.max)-Numeric.log10(self.xaxis.min))/100.))
        else:
            x = Numeric.arange (self.xaxis.min, self.xaxis.max, (self.xaxis.max-self.xaxis.min)/100.)

        for fds in self.fit_datasets ():
            # individual functions
            for i, f in enumerate(self.fitwin.functions):
                f.load(fds.curveid)
                self.plot.setCurveData (fds.funcs[i], x, f.call(x))
                if fds.hidefit:
                    self.plot.curve(fds.funcs[i]).pen().setColor (Qt.white)
                else:
                    self.plot.curve(fds.funcs[i]).pen().setColor (Qt.black)
                if i == self.fitwin.selected_function:
                    width = 2
                else:
                    width = 1
                self.plot.curve(fds.funcs[i]).pen().setWidth (width)

            # total
            if self.fitwin.functions != []:
                y = self.fitwin.call(x)
                self.plot.setCurveData (fds.function, x, y)
                self.plot.curve(fds.function).pen().setColor (Qt.blue)
        self.redraw()

    def fit_datasets (self):
        """Curve id's of datasets selected for fitting"""
        return self.fitdatasets

    def selected_datasets (self):
        """Curve id's of datasets selected in legend"""
        return [self.datasets[n] for n in range(self.legend.count()) if self.legend.isSelected(n)]

    def begin_properties(self):
        project.undolist.begin_composite(RangeCompositeCommand 
                        (self, name=('Change Graph %s Options' % self.name),
                         pixmap=QPixmap(project.datadir + 'pixmaps/properties.png')))

    def end_properties(self):
            project.undolist.end_composite()

    def properties (self):
        if self in project.graphs:
            project.undolist.begin_composite(RangeCompositeCommand 
                            (self, name=('Change Graph %s Options' % self.name),
                             pixmap=QPixmap(project.datadir + 'pixmaps/properties.png')))
        try:
            propsdlg = Graph_Properties_Dlg (self)
            propsdlg.exec_loop()
        finally:
            if self in project.graphs:
                project.undolist.end_composite()
 
#----------------------------------------------------------------------------------------------------
# Mouse events


    def onMouseReleased(self, e):
        if   Graph.graph_mode == 1: self.zoomMouseReleased (e)
        elif Graph.graph_mode == 2: self.rangeMouseReleased (e)
        elif Graph.graph_mode == 5: self.handMouseReleased (e)

    def onMousePressed(self, e):
        self.tabs.setFocus()
        if   Graph.graph_mode == 0: self.arrowMousePressed (e)
        elif Graph.graph_mode == 1: self.zoomMousePressed (e)
        elif Graph.graph_mode == 2: self.rangeMousePressed (e)
        elif Graph.graph_mode == 3: self.drMousePressed (e)
        elif Graph.graph_mode == 4: self.srMouseMoved (e)
        elif Graph.graph_mode == 5: self.handMousePressed (e)
            
    def onMouseMoved(self, e):
        if   Graph.graph_mode == 0: pass
        elif Graph.graph_mode == 2: self.rangeMouseMoved (e)
        elif Graph.graph_mode == 3: self.drMouseMoved (e)
        elif Graph.graph_mode == 4: self.srMouseMoved (e)
        elif Graph.graph_mode == 5: self.handMouseMoved (e)
#----------------------------------------------------------------------------------------------------
# Zooming

    def zoomMousePressed(self, e):
        self.xpos = e.pos().x()
        self.ypos = e.pos().y()
        comm = RangeCompositeCommand(self, name=('Zoom in graph %s' % self.name),
                                pixmap=QPixmap(project.datadir + 'pixmaps/zoom.png'))
        project.undolist.begin_composite(comm)
        if Qt.LeftButton == e.button() or Qt.RightButton == e.button():
            self.plot.enableOutline(1)
            self.plot.setOutlinePen(QPen(Qt.black))
            self.plot.setOutlineStyle(Qwt.Rect)
            self.zooming = 1
        self.onMouseMoved(e)

    def zoomMouseReleased(self, e):
        x1, x2 = self.xaxis.pixel_to_value(self.xpos), self.xaxis.pixel_to_value(e.pos().x())
        y1, y2 = self.yaxis.pixel_to_value(self.ypos), self.yaxis.pixel_to_value(e.pos().y())
        exmin, exmax, eymin, eymax = min(x1, x2), max(x1, x2), min(y1, y2), max (y1, y2)

        def zoomout(x1, x2, x3, x4):
            a = (x2-x1)/(x4-x3); c = x1 - a*x3;
            f1 = a*x1 + c; f2 = a*x2 + c;
            return min(f1, f2), max(f1, f2)

        self.plot.enableOutline(0)

        if Qt.LeftButton == e.button():
            if self.xpos == e.pos().x() or self.ypos == e.pos().y(): 
                project.undolist.end_composite()
                return
            self.xaxis.min, self.xaxis.max = exmin, exmax
            self.yaxis.min, self.yaxis.max = eymin, eymax
        elif Qt.RightButton == e.button():
            if self.xpos == e.pos().x() or self.ypos == e.pos().y(): 
                project.undolist.end_composite()
                return
            if self.xaxis.logscale:
                x1 = log(self.xaxis.min); x2 = log(self.xaxis.max); x3 = log(exmin); x4 = log(exmax)
                self.xaxis.min, self.xaxis.max = [exp(f) for f in zoomout(x1, x2, x3, x4)]
            else:
                self.xaxis.min, self.xaxis.max = zoomout(self.xaxis.min, self.xaxis.max, exmin, exmax)

            if self.yaxis.logscale:
                y1 = log(self.yaxis.min); y2 = log(self.yaxis.max); y3 = log(eymin); y4 = log(eymax)
                self.yaxis.min, self.yaxis.max = [exp(f) for f in zoomout(y1, y2, y3, y4)]
            else:
                self.yaxis.min, self.yaxis.max = zoomout(self.yaxis.min, self.yaxis.max, eymin, eymax)
        elif Qt.MidButton == e.button ():
            if e.state() & Qt.ShiftButton:
                self.autozoom(self.selected_datasets())
            else:
                self.autozoom()
        self.redraw()
        project.undolist.end_composite()

    def autozoom(self, dsets = None):
        if dsets is None:
            dsets = self.datasets
        if dsets == []:
            return
        self.xaxis.min = min ([ds.rangemin for ds in dsets])   
        self.xaxis.max = max ([ds.rangemax for ds in dsets])   
        self.yaxis.min = min ([ds.range_limits_y(False)[0] for ds in dsets])   
        self.yaxis.max = max ([ds.range_limits_y(False)[1] for ds in dsets])   
 
#----------------------------------------------------------------------------------------------------
# Range selection


    def rangeMousePressed(self, e):
        dsets = self.selected_datasets()
        if dsets == []:
            dsets = self.datasets
        if dsets == []:
            return
           
        if Qt.LeftButton == e.button ():
            self.moving_rangemin = True
        elif Qt.RightButton == e.button ():
            self.moving_rangemax = True
        self.rangelimit_l = min ([d.range_limits()[0] for d in dsets])
        self.rangelimit_h = max ([d.range_limits()[1] for d in dsets])
        comm = RangeCompositeCommand(self, name=('Range in graph %s' % self.name),
                                pixmap=QPixmap(project.datadir + 'pixmaps/range.png'))
        if self in project.graphs:
            project.undolist.begin_composite(comm)
        self.rangeMouseMoved(e)

    def rangeMouseReleased(self, e):
        dsets = self.selected_datasets()
        if dsets == []:
            dsets = self.datasets
        self.moving_rangemin = self.moving_rangemax = False

        if Qt.MidButton == e.button ():
            for ds in self.selected_datasets():
                ds.rangemin, ds.rangemax = ds.range_limits()
                ds.update()
            self.plot.setMarkerXPos (self.rangemin, min ([d.rangemin for d in dsets]))
            self.plot.setMarkerXPos (self.rangemax, max ([d.rangemax for d in dsets]))
            self.redraw()
        if self in project.graphs:
            project.undolist.end_composite()

    def rangeMouseMoved(self, e):
        dsets = self.selected_datasets()
        if dsets == []:
            dsets = self.datasets
        if dsets == []:
            return
        xpos = clip (self.xaxis.pixel_to_value(e.pos().x()), 
                     self.rangelimit_l, self.rangelimit_h)

        self.freeze()
        if self.moving_rangemin:
            self.plot.setMarkerXPos (self.rangemin, xpos)
            for ds in dsets:
                ds.rangemin = xpos
        elif self.moving_rangemax:
            self.plot.setMarkerXPos (self.rangemax, xpos)
            for ds in dsets:
                ds.rangemax = xpos
        self.unfreeze()

    def srMouseMoved (self, e):
        xval = self.xaxis.pixel_to_value(e.pos().x())
        yval = self.yaxis.pixel_to_value(e.pos().y())
        self.plot.setMarkerXPos (self.reader, xval)
        self.plot.setMarkerYPos (self.reader, yval)
        project.mainwin.statuslabel.setText ("(%g, %g)" % (xval, yval))
        if e.state() & Qt.ControlButton:
            curve, dist, xval, yval, ind = self.plot.closestCurve (e.pos().x(), e.pos().y())
            dataset = self.datasets[[d.curveid for d in self.datasets].index(curve)]
            if dist<=2:
                index = dataset.data()[2][ind]
                dataset.worksheet[dataset.coly][index] = nan
        project.main_dict['app'].processEvents()
        self.redraw()

    def drMousePressed (self, e):
        self.drMouseMoved(e, True)

    def drMouseMoved (self, e, select=False):
        if self.datasets == []:
            return
        curve, dist, xval, yval, index = self.plot.closestCurve (e.pos().x(), e.pos().y())
        self.dr_dataset = self.datasets[[d.curveid for d in self.datasets].index(curve)]
        self.dr_point = index
        self.plot.setMarkerXPos (self.reader, xval)
        self.plot.setMarkerYPos (self.reader, yval)
        if curve != 0:
            project.mainwin.statuslabel.setText ("%s, point %d (%g, %g)" % 
                                           (self.dr_dataset.label(), index, xval, yval))
            project.main_dict['app'].processEvents()
            if select:
                self.legend.clearSelection()
                self.legend.setSelected(self.dr_dataset.index(), True)
        self.redraw()

    def supported_export_formats(self):
        def command_available(com):
            str = os.popen('which %s' % com).read()
            return str!=''
        formats = []
        formats.append('Gri')

        if command_available('gri'):
            formats.append('PostScript')
            if command_available('ps2pdf'):
                formats.append('PDF')
            if command_available('pstopnm') and command_available('pnmtopng'):
                formats.append('PNG')
            if command_available('pstopnm') and command_available('pnmtotiff'):
                formats.append('TIFF')
        return formats

    def export(self, filename, format='PostScript'):
        gri_shapes = [
            [ None, 'circ', 'filledbox', 'filleddiamond', 'filledtriangleup', 
              'filledtriangledown', 'filledtriangleleft', 'filledtriangleright',
              'plus', 'times'],
            [ None, 'bullet', 'box', 'diamond', 'triangleup',
              'triangledown', 'triangleleft', 'triangleright',
              'plus', 'times' ],
        ]

#        p = Page(None,
#            ('Size', ['Width', 'Height']),
#        )
#        p.win.exec_loop()
#
#        print >>sys.stderr, p['Width'], p['Height']



        gri_linestyles = [ 'off', '', '14', '0.5 0.1 0.1 0.1', '0.5 0.1 0.1 0.1 0.1 0.1']
        
        gricode = []
        gricode.append('# Generated by grafit\n')

        gricode.append('set clip on\n')
        gricode.append('set tics in\n')

        # axes
        if self.xaxis.logscale:
            gricode.append('set x type log\n')
        gricode.append('set x axis %g %g %g\n' % (self.xaxis.min, self.xaxis.max, self.xaxis.majstep))
        gricode.append('set x name "%s"\n' % self.xaxis.title)

        if self.yaxis.logscale:
            gricode.append('set y type log\n')
        gricode.append('set y axis %g %g %g\n' % (self.yaxis.min, self.yaxis.max, self.yaxis.majstep))
        gricode.append('set y name "%s"\n' % self.yaxis.title)

        gricode.append('draw axes\n')
#        gricode.append('set graylevel 0.75\n')
#        gricode.append('set line width 0.5\n')
#        gricode.append('set dash 14\n')

#        linestart = floor(abs(self.xaxis.min) / self.xaxis.majstep) * self.xaxis.majstep * self.xaxis.min / abs(self.xaxis.min)
#        lineend = ceil(abs(self.xaxis.max) / self.xaxis.majstep) * self.xaxis.majstep * self.xaxis.max / abs(self.xaxis.max) 
#        gricode.append('draw lines vertically %g %g %g\n' % (linestart, lineend, self.xaxis.majstep))
#        linestart = round(abs(self.yaxis.min) / self.yaxis.majstep) * self.yaxis.majstep * self.yaxis.min / abs(self.yaxis.min)
#        lineend = round(abs(self.yaxis.max) / self.yaxis.majstep) * self.yaxis.majstep * self.yaxis.max / abs(self.yaxis.max) 
#        gricode.append('draw lines horizontally %g %g %g\n' % (linestart, lineend, self.yaxis.majstep))
#
#        gricode.append('set line width default\n')
#        gricode.append('set graylevel 1\n')
#        gricode.append('set dash 0\n')

        # data
        for ds in self.datasets:
            gricode.append('read columns x y\n')
            z = zip(*ds.data())
            z.sort()
            for x, y, i in z:
                 gricode.append('%g %g\n' %(x, y))
            gricode.append('\n')
            gricode.append('set symbol size %g\n' % (ds.symbol_size / 30.))
            gricode.append('set color rgb %f %f %f\n' % tuple([x/256. for x in colors[ds.symbol_color].getRgb()]))
            if gri_shapes[ds.symbol_fill][ds.symbol_style] is not None:
                gricode.append('draw symbol %s\n' % gri_shapes[ds.symbol_fill][ds.symbol_style])
            if ds.line_type == 2 and not self.xaxis.logscale:
                gricode.append('convert columns to spline\n')
            gricode.append('set dash %s\n' % gri_linestyles[ds.line_style])

            if ds.line_type != 0:
                gricode.append('draw curve\n')
            gricode.append('\n\n')

        if format=='Gri':
            f = open(filename, 'w')
            f.writelines(gricode)
            f.close()
            return

        tmpname = '/tmp/gri_ps'

        gri = os.popen('gri -b -output %s' % tmpname, 'w')
        gri.writelines(gricode)
        gri.close()

        if format=='PostScript':
            shutil.move(tmpname, filename)
            return
        elif format=='PDF':
            os.system('ps2pdf %s %s' % (tmpname, filename))
            os.unlink(tmpname)
            return
        elif format=='PNG':
            os.system('pstopnm %s -xsize 600 -ysize 600 -portrait -stdout | pnmtopng >%s' % (tmpname, filename))
            os.unlink(tmpname)
        elif format=='TIFF':
            os.system('pstopnm %s -xsize 1000 -ysize 1000 -portrait -stdout | pnmtotiff >%s' % (tmpname, filename))
            os.unlink(tmpname)
        else:
            raise NameError

    def arrowMousePressed (self, e):
        pass

    def handMousePressed(self, e):
        pass

    def handMouseReleased(self, e):
        ChangeParameterValue.accumulate = False

    def handMouseMoved (self, e):
        x = self.xaxis.pixel_to_value(e.x())
        y = self.yaxis.pixel_to_value(e.y())

        if self.fitwin == None: return
        if self.selected_fit_dataset == None: return
        if self.fitwin.selected_function == None: return

        prev = self.fitwin.params_func_to_flat()[0]

        f = self.fitwin.functions[self.fitwin.selected_function]
        f.load (self.selected_fit_dataset.curveid)
        try:
            f.move (x, y)
        except ValueError, OverflowError:
            print >>sys.stderr, "ValueError or OverflowError"
            pass
        f.save (self.selected_fit_dataset.curveid)

        flat = self.fitwin.params_func_to_flat()[0]
        if self in project.graphs:
            project.undolist.append(ChangeParameterValue(self.fitwin, flat, prev))
        ChangeParameterValue.accumulate = True

        self.fitwin.params_func_to_ui ()
        self.update_function_curves()

    def keyPressEvent(self, e):
        text  = str(e.text())
        key   = e.key()
        ascii = e.ascii()

        if not e.state() & Qt.ControlButton and text != '':
            keys = 'azrdsh'
            if text in keys:
                modes = [ 'g_arrow', 'g_zoom', 'g_range', 'g_dreader', 'g_sreader', 'g_hand' ]
                project.mainwin.actions[modes[keys.index(text)]].setOn(True)

            keys = '1234567890'
            if text in keys:
                ind = keys.index(text)
                if ind < self.legend.count():
                    self.legend.setSelected(ind, not self.legend.isSelected(ind))

        if Graph.graph_mode == 3: # data reader
            if key == Qt.Key_Delete:
                dataset = self.dr_dataset
                index = dataset.data()[2][self.dr_point]
                dataset.worksheet[dataset.coly][index] = nan
                
            if e.state() & Qt.ShiftButton:
                xincr = self.xaxis.increment ()
                yincr = self.yaxis.increment ()
                dataset = self.dr_dataset
                index = dataset.data()[2][self.dr_point]
                if e.state() & Qt.ControlButton: # move dataset
                    if key == Qt.Key_Up:
                        if self.yaxis.logscale: dataset.worksheet[dataset.coly] *= yincr
                        else: dataset.worksheet[dataset.coly] += yincr
                    elif key == Qt.Key_Down:
                        if self.yaxis.logscale: dataset.worksheet[dataset.coly] /= yincr
                        else: dataset.worksheet[dataset.coly] -= yincr
                    elif key == Qt.Key_R:
                        z = (dataset.x() + 1j*dataset.y()) * exp(-0.1j)
                        dataset.worksheet[dataset.colx] = z.real
                        dataset.worksheet[dataset.coly] = z.imag
                    elif key == Qt.Key_T:
                        z = (dataset.x() + 1j*dataset.y()) * exp(-0.1j)
                        dataset.worksheet[dataset.colx] = z.real
                        dataset.worksheet[dataset.coly] = z.imag
                else:   # move data point
                    if key == Qt.Key_Up:
                        if self.yaxis.logscale: dataset.worksheet[dataset.coly][index] *= yincr
                        else: dataset.worksheet[dataset.coly][index] += yincr
                    elif key == Qt.Key_Down:
                        if self.yaxis.logscale: dataset.worksheet[dataset.coly][index] /= yincr
                        else: dataset.worksheet[dataset.coly][index] -= yincr

        if Graph.graph_mode == 4: # screen reader
            if e.state() & Qt.ShiftButton:
                if key == Qt.Key_Up:
                    print "ShiftUp"
            else:
                xval, yval = self.plot.markerPos (self.reader)
                if self.xaxis.logscale:
                    incr = 10**((Numeric.log10(self.xaxis.max) - Numeric.log10(self.xaxis.min)) / 100.)
                    if key == Qt.Key_Right: 
                        self.plot.setMarkerXPos (self.reader, xval*incr)
                    elif key == Qt.Key_Left: 
                        self.plot.setMarkerXPos (self.reader, xval/incr)
                else:
                    if key == Qt.Key_Right: 
                        self.plot.setMarkerXPos (self.reader, (self.xaxis.max-self.xaxis.min)/100. + xval)
                    elif key == Qt.Key_Left: 
                        self.plot.setMarkerXPos (self.reader, -(self.xaxis.max-self.xaxis.min)/100. + xval)

                if self.yaxis.logscale:
                    incr = 10**((Numeric.log10(self.yaxis.max) - Numeric.log10(self.yaxis.min)) / 100.)
                    if key == Qt.Key_Up: 
                        self.plot.setMarkerYPos (self.reader, yval*incr)
                    elif key == Qt.Key_Down: 
                        self.plot.setMarkerYPos (self.reader, yval/incr)
                else:
                    if key == Qt.Key_Up: 
                        self.plot.setMarkerYPos (self.reader, (self.yaxis.max-self.yaxis.min)/100. + yval)
                    elif key == Qt.Key_Down: 
                        self.plot.setMarkerYPos (self.reader, -(self.yaxis.max-self.yaxis.min)/100. + yval)

                project.mainwin.statuslabel.setText ("(%g, %g)" % (xval, yval))
                project.main_dict['app'].processEvents()
        self.redraw()

# printing

    def Print (self):
        printer = QPrinter ()
        printer.setOutputToFile (True)
        printer.setOutputFileName ('mikou.ps')
        printer.setup()
        printer.newPage()
        self.plot.printPlot (printer)

# updating

    def freeze(self):
        self._frozen += 1

    def unfreeze(self):
        if self._frozen:    
            self._frozen -= 1
        self.redraw()

    def redraw(self):
        if not self._frozen:
            self.plot.replot()
            if self.legend.needs_updating:
                self.legend.update()

    def vogel(self):
        self.tabs.setWFlags(Qt.WDestructiveClose)
        self.tabs.close()

    def __setattr__(self, key, value):
        if key == 'name':
            self._set_name(value)
        else:
            self.__dict__[key] = value

    def __repr__(self):
        return "<Graph '%s'>" %(self.name,)
