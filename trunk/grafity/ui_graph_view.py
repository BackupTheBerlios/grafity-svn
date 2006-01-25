import os
import sys
sys.modules['__main__'].splash.message('loading ui_graph_view')

from qt import *
from qwt import *
import qwt.qplt

from grafity.arrays import clip, nan, arange, log10
from grafity.actions import CompositeAction, action_list
from grafity.functions import registry, Function

from grafity.ui.graph_style import GraphStyleUI
from grafity.ui.graph_data import GraphDataUI
from grafity.ui.graph_axes import GraphAxesUI
from grafity.ui.graph_fit import GraphFitUI
from grafity.ui.functions import FunctionsWindowUI
from grafity.ui.fitoptions import FitOptionsUI

from grafity import Graph, Worksheet, Folder
from grafity.settings import DATADIR, USERDATADIR

def getpixmap(name, pixmaps={}):
    if name not in pixmaps:
        pixmaps[name] = QPixmap(os.path.join(DATADIR, 'data', 'images', '16', name+'.png'))
    return pixmaps[name]

def efloat(f):
    try:
        return float(f)
    except:
        return nan


class EventHandler(QObject):
    def __init__(self, object, callback):
        QObject.__init__(self, object)
        self.object, self.callback = object, callback

    def eventFilter(self, object, event):
        return self.callback(event)

def connectevents(object, callback):
    object.installEventFilter(EventHandler (object, callback))

class GraphView(QTabWidget):
    def __init__(self, parent, mainwin, graph):
        QTabWidget.__init__(self, parent)
        self.graph = graph
        self.mainwin = mainwin
        self.setTabShape(self.Triangular)
        self.setTabPosition(self.Bottom)
        self.setIcon(getpixmap('graph'))
        self.mainpage = QSplitter(QSplitter.Horizontal, self)
        self.addTab(self.mainpage, 'graph')

        self.bg_color = QColor('white')

        self.plot = QwtPlot()
        self.plot.reparent(self.mainpage, 0, QPoint(0,0))
        self.plot.setCanvasBackground (self.bg_color)
        self.plot.enableGridX(True)
        self.plot.enableGridY(True)
        self.plot.setOutlineStyle (Qwt.Rect)
        self.plot.setAutoReplot(False)
        self.plot.canvas().setLineWidth(0)
        self.plot.axis(self.plot.xBottom).setBaselineDist(0)
        self.plot.axis(self.plot.xBottom).setBorderDist(0,0)
        self.plot.axis(self.plot.yLeft).setBaselineDist(0)
        self.plot.axis(self.plot.yLeft).setBorderDist(0,0)

        
        self.graph.connect('style-changed', self.on_change_style)
        self.graph.connect('zoom-changed', self.on_zoom_changed)
        self.graph.connect('data-changed', self.on_recalc)
        self.graph.connect('rename', self.on_rename)

        self.graph.connect('add-dataset', self.on_add_dataset)
        self.graph.connect('remove-dataset', self.on_remove_dataset)
        self.graph.connect('set-title', self.on_set_title)
        self.graph.connect('set-scale', self.on_set_scale)
        self.graph.function.connect('add-term', self.on_add_function_term)
        self.graph.function.connect('remove-term', self.on_remove_function_term)
        self.graph.function.connect('modified', self.on_function_modified)

#        self.graph.connect('add-function', self.on_modified)
        self.frozen = False
        self.needs_redraw = False
        self.needs_legend_update = False

        connectevents(self.plot.canvas(), self.on_canvas_event)
        self.connect(self.plot, SIGNAL('plotMouseMoved(const QMouseEvent&)'), self.on_mouse_moved)
        self.connect(self.plot, SIGNAL('plotMousePressed(const QMouseEvent&)'), self.on_mouse_pressed)
        self.connect(self.plot, SIGNAL('plotMouseReleased(const QMouseEvent&)'), self.on_mouse_released)

        self.legend = QListBox(self.mainpage)
        pal = QPalette(self.legend.palette())
        cg = QColorGroup(pal.active())
        self.legend_background_color = cg.color(QColorGroup.Background)
        cg.setColor(QColorGroup.Base, self.legend_background_color)
        pal.setActive(cg)
        self.legend.setPalette(pal)
        self.legend.setFrameShape(QFrame.NoFrame)
        self.legend.setSelectionMode(QListBox.Extended)
        self.connect(self.legend, SIGNAL('selectionChanged()'), self.on_legend_select)

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

        self.rangemin = self.plot.insertLineMarker(None, QwtPlot.xBottom)
        self.rangemax = self.plot.insertLineMarker(None, QwtPlot.xBottom)
        self.reader = self.plot.insertLineMarker(None, QwtPlot.xBottom)
        self.plot.setMarkerLineStyle(self.rangemin, QwtMarker.VLine)
        self.plot.setMarkerLineStyle(self.rangemax, QwtMarker.VLine)
        self.plot.setMarkerLineStyle(self.reader, QwtMarker.NoLine)
        self.moving_rangemin = self.moving_rangemax = False

        self.mode = 'arrow'
        self.setCaption(self.graph.name)

    def on_rename(self, *args, **kwds):
        self.setCaption(self.graph.name)

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
            selected = [self.legend.isSelected(it) for it in range(self.legend.numRows())]
            current = self.legend.currentItem()

            self.legend.clear()
            self.legend.insertStrList([str(d) for d in self.graph.datasets])
            for n, dset in enumerate(self.graph.datasets):
                if hasattr(dset, '_curveid'):
                    self.legend.changeItem(self.draw_pixmap(dset), self.legend.text(n), n)

            for i,on in enumerate(selected):
                self.legend.setSelected(i, on)
            self.legend.setCurrentItem(current)
            self.needs_legend_update = False

    def on_add_function_term(self, term):
        term._curveid = self.plot.insertCurve('')

    def on_remove_function_term(self, term):
        self.plot.removeCurve(term._curveid)

    def on_add_dataset(self, d):
        d._curveid = self.plot.insertCurve('')
        d.recalculate()
        for s in ['symbol', 'color', 'size', 'linetype', 'linestyle', 'linewidth']:
            self.on_change_style(d, s, d.get_style(s))
        self.redraw()
        self.update_legend()
     
    def on_remove_dataset(self, d):
        self.plot.removeCurve(d._curveid)
        self.redraw()
        self.update_legend()

    def on_legend_select(self):
        self.datasets = [self.graph.datasets[n] for n in range(self.legend.count())
                                                if self.legend.isSelected(n)]
        self.graph.emit('selection-changed', self.datasets)

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
        x = self.plot.invTransform(self.plot.xBottom, e.pos().x())
        y = self.plot.invTransform(self.plot.yLeft, e.pos().y())
        if self.mode == 'zoom':
            self.xpos, self.ypos = x, y
            self.plot.enableOutline(True)
            self.plot.setOutlinePen(QPen(Qt.blue, 0, Qt.DotLine))
            self.plot.setOutlineStyle(Qwt.Rect)
            self.zooming = True
            self.on_mouse_moved(e)
        elif self.mode == 'range':
            if e.button() == Qt.LeftButton:
                self.moving_rangemin = True
            elif e.button() == Qt.RightButton:
                self.moving_rangemax = True
            self.range_l = min(d.minx for d in self.datasets)
            self.range_r = max(d.maxx for d in self.datasets)
            self.on_mouse_moved(e)
        elif self.mode == 'hand':
            pass

    def on_mouse_released(self, e):
        x = self.plot.invTransform(self.plot.xBottom, e.pos().x())
        y = self.plot.invTransform(self.plot.yLeft, e.pos().y())
        if self.mode == 'zoom':
            xmin, xmax, ymin, ymax = min(self.xpos, x), max(self.xpos, x), min(self.ypos, y), max(self.ypos, y)
            if e.button() == Qt.LeftButton:
                self.graph.zoom(xmin, xmax, ymin, ymax)
            elif e.button() == Qt.RightButton:
                self.graph.zoom_out(xmin, xmax, ymin, ymax)
        elif self.mode == 'range':
            self.moving_rangemin = self.moving_rangemax = False
            if e.button() == Qt.MidButton:
                for d in self.datasets:
                    d.range = (self.range_l, self.range_r)
                    self.plot.setMarkerXPos(self.rangemin, min(d.range[0] for d in self.datasets))
                    self.plot.setMarkerXPos(self.rangemax, max(d.range[1] for d in self.datasets))
        elif self.mode == 'hand':
            self.mainwin.graph_fit.active_term.move(x, y)

    def on_mouse_moved(self, e):
        x = self.plot.invTransform(self.plot.xBottom, e.pos().x())
        y = self.plot.invTransform(self.plot.yLeft, e.pos().y())
        if self.mode == 'range':
            xpos = clip(x, self.range_l, self.range_r)
            self.freeze()
            action_list.begin_composite(CompositeAction())
            if self.moving_rangemin:
                self.plot.setMarkerXPos(self.rangemin, xpos)
                for d in self.datasets:
                    d.range = (xpos, d.range[1])
            elif self.moving_rangemax:
                self.plot.setMarkerXPos(self.rangemax, xpos)
                for d in self.datasets:
                    d.range = (d.range[0], xpos)
            action_list.end_composite().register()
            self.unfreeze()
        elif self.mode == 'hand':
            self.mainwin.graph_fit.active_term.move(x, y)

    def on_canvas_event(self, event):
        return False

    def on_function_modified(self):
        if self.graph.xtype == 'log':
            x = 10.**arange(log10(self.graph.xmin), log10(self.graph.xmax),
                            log10(self.graph.xmax/self.graph.xmin)/100)
        else:
            x = arange(self.graph.xmin, self.graph.xmax, (self.graph.xmax-self.graph.xmin)/100)

        for term in self.graph.function.terms:
            self.plot.setCurveData(term._curveid, x, term(x))
        self.plot.setCurveData(self.graph.function._curveid, x, self.graph.function(x))
        self.redraw()

    def on_recalc(self, d, x, y):
        self.plot.setCurveData(d._curveid, x, y)
        self.redraw()

    symbols = {'circle': QwtSymbol.Ellipse,
               'square': QwtSymbol.Rect,
               'diamond': QwtSymbol.Diamond,
               'triangleup': QwtSymbol.UTriangle, }

    symbol_names = ['circle', 'square', 'diamond', 'triangleup']

    fills = { 'filled': QBrush(Qt.black), 
              'open': QBrush(), }
    fill_names = ['filled', 'open']

    colornames = [
        'black', 'red', 'DarkRed', 'green', 'DarkGreen', 'blue', 'DarkBlue', 'cyan', 'DarkCyan',
        'magenta', 'DarkMagenta', 'yellow', 'DarkYellow', 'gray', 'DarkGray', 'LightGray',
        'CadetBlue3', 'CornflowerBlue', 'DarkGoldenrod1', 'DarkOliveGreen2', 'DarkOrange1', 
        'DarkSalmon', 'DarkTurquoise', 'DeepPink2', 'DeepSkyBlue1', 'DodgerBlue3', 'HotPink', 
        'HotPink3', 'IndianRed', 'LightGreen', 'MediumPurple4', 'MediumViloetRed' ]

    qcolors = [QColor(s) for s in colornames]
    colors = [unicode(s.name()) for s in qcolors]

    line_types = [QwtCurve.NoCurve, QwtCurve.Lines, QwtCurve.Spline]
    line_type_names = ['none', 'straight', 'spline']
    line_styles = [Qt.SolidLine, Qt.DashLine, Qt.DotLine, Qt.DashDotLine, Qt.DashDotDotLine]
    line_style_names = ['solid', 'dash', 'dot', 'dashdot', 'dashdotdot']


    def on_change_style(self, d, style, value):
        curve = self.plot.curve(d._curveid)
        if style == 'symbol':
            curve.symbol().setStyle(self.symbols[value])
        elif style == 'fill':
            if value == 'open':
                brush = self.fills['open']
            elif value == 'filled':
                brush = QBrush(self.qcolors[self.colors.index(d.style.color)])
            curve.symbol().setBrush(brush)
        elif style == 'color':
            color = self.qcolors[self.colors.index(value)]
            curve.symbol().brush().setColor(color)
            curve.symbol().pen().setColor(color)
            curve.pen().setColor(color)
        elif style == 'size':
            curve.symbol().setSize(value)
        elif style == 'linetype':
            curve.setStyle(self.line_types[self.line_type_names.index(value)])
        elif style == 'linestyle':
            curve.pen().setStyle(self.line_styles[self.line_style_names.index(value)])
        elif style == 'linewidth':
            curve.pen().setWidth(value)

        self.redraw()
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

    def fill(self):
        self.functions.clear()
        for function in registry:
            item = QListViewItem(self.functions, function.name)

    def on_selection_changed(self):#, item=None):
        item = self.functions.selectedItem()
        if item is None:
            self.func = None
            self.tabs.setEnabled(False)
        else:
            self.updating = True
            self.tabs.setEnabled(True)
            func = registry[unicode(item.text(0))]
            if self.func is None or func.name != self.func.name:
                self.name.setText(func.name)
                self.parameters.setText(', '.join(func.parameters))
                self.equation.setText(func.text)
#            self.extra.setText(func.extra)
            self.func = func
            self.updating = False

    def on_delete(self):
        os.remove(self.func.filename)
        registry.rescan()
        self.fill()

    def on_new(self):
        num = 0
        while 'function%d.function'%num in (f.filename.split('/')[-1] for f in registry):
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
#        self.func.extra = unicode(self.extra.text())
        self.func.save()
        registry.rescan()
        self.fill()
        self.functions.setSelected(self.functions.findItem(self.func.name, 0), True)

    def on_add_function_clicked(self):
        self.fitwin.add_function(self.func)

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
        box.setMaximumSize(QSize(120,3000))
        buttons = QHBox(box)
        term._butt = QPushButton('function', buttons)
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
            label = QLabel(par, grid)
            edit = QLineEdit(grid)
            edit.setMinimumSize(QSize(20, 0))
            self.connect(edit, SIGNAL("returnPressed()"), self.on_activate)
            self.connect(edit, SIGNAL("lostFocus()"), self.on_activate)
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
            else:
                term._grid.show()
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
        lock = [check.isOn() for term in self.function.terms for check in term._lock]
        ind = data.active_data()
        self.function.fit(data.x[ind], data.y[ind], lock, 50)
        self.function.emit('modified')


    def add_function(self, f):
        print >>sys.stderr, 'add-function'
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

        for c in GraphView.qcolors:
            p = QPixmap()
            p.resize(30, 10)
            p.fill(c)
            self.color.insertItem(p)

        for l in GraphView.line_styles:
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

        brush = GraphView.fills['filled']
        pen = QPen()
        for l in GraphView.symbol_names:
            p = QPixmap()
            p.resize(12,12)
            paint = QPainter()
            p.fill(Qt.white)
            paint.begin(p)
            QwtSymbol(GraphView.symbols[l], brush, pen, QSize(10, 10)).draw(paint, 6, 6)
            paint.end()
            p.setMask(p.createHeuristicMask())
            self.shape.insertItem(p)

        self.graph = None

        self.widgets = [self.shape, self.fill, self.size, self.color, 
                        self.ltype, self.lstyle, self.lwidth]

        self.checks = [self.shape_ch, self.fill_ch, self.size_ch, self.color_ch,
                       self.ltype_ch, self.lstyle_ch, self.lwidth_ch]

        self.props = ['symbol', 'fill', 'size', 'color', 'linetype', 'linestyle', 'linewidth']

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
        self.shape.setCurrentItem(GraphView.symbol_names.index(style.symbol))
        self.fill.setCurrentItem(GraphView.fill_names.index(style.fill))
        self.color.setCurrentItem(GraphView.colors.index(style.color))
        self.size.setValue(style.size)
        self.ltype.setCurrentItem(GraphView.line_type_names.index(style.linetype))
        self.lstyle.setCurrentItem(GraphView.line_style_names.index(style.linestyle))
        self.lwidth.setValue(style.linewidth)

    def get_to_dataset(self, dataset, ind=0):
        style = dataset.style

        ind_color = self.color_ch.isOn()*ind
        ind_symbol = ind_fill = ind_linetype = 0

        if self.shape_ch.isOn():
            style.symbol = GraphView.symbol_names[(self.shape.currentItem()+ind_symbol)%len(GraphView.symbol_names)]
        if self.fill_ch.isOn():
            style.fill = GraphView.fill_names[(self.fill.currentItem()+ind_fill)%len(GraphView.fill_names)]
        if self.color_ch.isOn():
            style.color = GraphView.colors[(self.color.currentItem()+ind_color)%len(GraphView.colors)]
        if self.ltype_ch.isOn():
            style.linetype = GraphView.line_type_names[(self.ltype.currentItem()+ind_linetype)%len(GraphView.line_type_names)]

        if self.lstyle_ch.isOn():
            style.linestyle = GraphView.line_style_names[self.lstyle.currentItem()]
        if self.size_ch.isOn():
            style.size = self.size.value()
        if self.size_ch.isOn():
            style.linewidth = self.lwidth.value()

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
                    w.hide()

                for w in self.widgets:
                    w.setEnabled(True)
            else:
                self.group.setEnabled(True)

                for w in self.checks:
                    w.show()

                if self.group.currentItem() == 0: # identical
                    for prop, widget, check in zip(self.props, self.widgets, self.checks):
                        thesame = len(set(getattr(d.style, prop) for d in datasets))==1
                        check.setChecked(thesame)
                        widget.setEnabled(thesame)
                elif self.group.currentItem() == 1: # series
                    for prop, widget, check in zip(self.props, self.widgets, self.checks):
                        if prop == 'color': # can do series
                            colors = [GraphView.colors.index(d.style.color) for d in datasets]
                            c0 = colors[0]
                            series = colors==[c % len(GraphView.colors) for c in range(c0, c0+len(colors))]
                            check.setChecked(series)
                            widget.setEnabled(series)
                        else:
                            check.setChecked(False)
                            check.hide()
                            widget.setEnabled(False)
        finally:
            self.updating = False

    def on_checks_changed(self):
        for prop, widget, check in zip(self.props, self.widgets, self.checks):
            widget.setEnabled(check.isOn())
        self.on_ui_changed()

    def on_ui_changed(self):
        if self.updating:
            return
        series = self.group.currentItem() == 1
        self.graph._view.freeze()
        for i, d in enumerate(self.datasets):
            self.get_to_dataset(d, i*series)
        self.graph._view.unfreeze()


class GraphData(GraphDataUI):
    def __init__(self, parent, mainwin):
        GraphDataUI.__init__(self, parent)
        self.worksheet_list.header().hide()
        self.mainwin = mainwin

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
        self.project = project
        if self.project is not None:
            self.worksheet_list.clear()
            self.on_add_item(self.project.top, recursive=True)
            project.top._gd_item.setOpen(True)

    def on_add_item(self, obj, recursive=False):
        try:
            parent = obj.parent._gd_item
        except AttributeError:
            parent = self.worksheet_list
        item = obj._gd_item = QListViewItem(parent, obj.name)
        pixmap = getpixmap({Worksheet: 'worksheet', 
                            Graph: 'graph', 
                            Folder: 'folder'}[type(obj)])
        item.setPixmap (0, pixmap)
#        item.setOpen (True)
        item._object = obj
        if recursive and isinstance(obj, Folder):
            for child in obj:
                if isinstance(child, (Folder, Worksheet)):
                    self.on_add_item(child, recursive=True)


