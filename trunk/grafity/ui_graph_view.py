import os
import sys

from qt import *
from qwt import *

from grafity.ui.graph_style import GraphStyleUI
from grafity.ui.graph_data import GraphDataUI
from grafity.ui.graph_axes import GraphAxesUI
from grafity.ui.graph_fit import GraphFitUI

from grafity import Graph, Worksheet, Folder, DATADIR

def getpixmap(name, pixmaps={}):
    if name not in pixmaps:
        pixmaps[name] = QPixmap(os.path.join(DATADIR, 'data', 'images', '16', name+'.png'))
    return pixmaps[name]



class EventHandler(QObject):
    def __init__(self, object, callback):
        QObject.__init__(self, object)
        self.object, self.callback = object, callback

    def eventFilter(self, object, event):
        return self.callback(event)

def connectevents(object, callback):
    object.installEventFilter(EventHandler (object, callback))


class GraphStyle(GraphStyleUI):
    def __init__(self, parent, mainwin):
        GraphStyleUI.__init__(self, parent)
        self.mainwin = mainwin

        for c in GraphView.colors:
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

        brushes = {'o': QBrush(), 'f': QBrush(Qt.black) }

        for fill in "of":
            for l in GraphView.symbol_names:
                p = QPixmap()
                p.resize(12,12)
                paint = QPainter()
                p.fill(Qt.white)
                paint.begin(p)
                brush = brushes[fill]
                pen = QPen()
                QwtSymbol(GraphView.symbols[l], brush, pen, QSize(10, 10)).draw(paint, 6, 6)
                paint.end()
                p.setMask(p.createHeuristicMask())
                self.shape.insertItem(p)

        self.graph = None

        self.widgets = [self.shape, self.fill, self.size, self.color, 
                        self.ltype, self.lstyle, self.lwidth]

        self.checks = [self.shape_ch, self.fill_ch, self.size_ch, self.color_ch,
                       self.ltype_ch, self.lstyle_ch, self.lwidth_ch]

    def set_graph(self, graph):
            if self.graph is not None:
                self.graph.disconnect('selection-changed', self.on_selection_changed)
            self.graph = graph
            if self.graph is not None:
                self.graph.connect('selection-changed', self.on_selection_changed)

    def on_selection_changed(self, datasets):
        if self.graph._view.frozen or len(datasets) == 0:
            return

        elif len(datasets) == 1:
            d = datasets[0]
            self.group.setEnabled(False)
            for w in self.checks:
                w.hide()

            for w in self.widgets:
                w.setEnabled(True)

            self.shape.setCurrentItem(GraphView.symbol_names.index(d.get_style('symbol')))


class GraphData(GraphDataUI):
    def __init__(self, parent, mainwin):
        GraphDataUI.__init__(self, parent)
        self.worksheet_list.header().hide()
        self.mainwin = mainwin

    def set_graph(self, graph):
        self.graph = graph
        print >>sys.stderr, self.graph

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


class GraphView(QTabWidget):
    def __init__(self, parent, graph):
        QTabWidget.__init__(self, parent)
        self.graph = graph
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
        
        self.graph.connect('style-changed', self.on_change_style)
        self.graph.connect('zoom-changed', self.on_zoom_changed)
        self.graph.connect('data-changed', self.on_recalc)

        self.graph.connect('add-dataset', self.on_add_dataset)
        self.graph.connect('remove-dataset', self.on_remove_dataset)
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
        self.update_legend()
        self.unfreeze()


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
        self.redraw()

    def on_mouse_pressed(self, e):
        self.xpos, self.ypos = e.pos().x(), e.pos().y()
        self.plot.enableOutline(True)
        self.plot.setOutlinePen(QPen(Qt.blue, 0, Qt.DotLine))
        self.plot.setOutlineStyle(Qwt.Rect)
        self.zooming = True
        self.on_mouse_moved(e)

    def on_mouse_released(self, e):
        x1 = self.plot.invTransform(self.plot.xBottom, self.xpos) 
        x2 = self.plot.invTransform(self.plot.xBottom, e.pos().x())
        y1 = self.plot.invTransform(self.plot.yLeft, self.ypos) 
        y2 = self.plot.invTransform(self.plot.yLeft, e.pos().y())
        exmin, exmax, eymin, eymax = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
        if e.button() == Qt.LeftButton:
            self.graph.zoom(exmin, exmax, eymin, eymax)
        elif e.button() == Qt.RightButton:
            self.graph.zoom_out(exmin, exmax, eymin, eymax)

    def on_mouse_moved(self, e):
        pass

    def on_canvas_event(self, event):
        return False

    def on_recalc(self, d, x, y):
        self.plot.setCurveData(d._curveid, x, y)
        self.redraw()

    symbols = {'circle': QwtSymbol.Ellipse,
               'square': QwtSymbol.Rect,
               'diamond': QwtSymbol.Diamond,
               'triangleup': QwtSymbol.UTriangle, }

    symbol_names = ['circle', 'square', 'diamond', 'triangleup']

    fills = {'open': Qt.NoBrush,
             'filled': QBrush(Qt.black), }
    fill_names = ['open', 'filled']

    colors = [Qt.black, Qt.red, Qt.darkRed, Qt.green, Qt.darkGreen,
              Qt.blue, Qt.darkBlue, Qt.cyan, Qt.darkCyan, Qt.magenta, Qt.darkMagenta,
              Qt.yellow, Qt.darkYellow, Qt.gray, Qt.darkGray, Qt.lightGray, Qt.black]

    extracolornames = [ 'CadetBlue3', 'CornflowerBlue', 'DarkGoldenrod1',
                        'DarkOliveGreen2', 'DarkOrange1', 'DarkSalmon',
                        'DarkTurquoise', 'DeepPink2', 'DeepSkyBlue1',
                        'DodgerBlue3', 'HotPink', 'HotPink3', 'IndianRed',
                        'LightGreen', 'MediumPurple4', 'MediumViloetRed' ]

    colors += [QColor(s) for s in extracolornames]

    line_types = [QwtCurve.NoCurve, QwtCurve.Lines, QwtCurve.Spline]
    line_styles = [Qt.SolidLine, Qt.DashLine, Qt.DotLine, Qt.DashDotLine, Qt.DashDotDotLine]


    def on_change_style(self, d, style, value):
        curve = self.plot.curve(d._curveid)
        try:
            if style == 'symbol':
                curve.symbol().setStyle(self.symbols[value.split('-')[0]])
#            try:
#                curve.symbol().brush().setStyle(self.symbol_brushes[value.split('-')[1]])
#            except IndexError:
#                pass
            elif style == 'color':
                curve.symbol().brush().setColor(self.colors[value])
                curve.symbol().pen().setColor(self.colors[value])
                curve.pen().setColor(self.colors[value])
            elif style == 'size':
                curve.symbol().setSize(value)
            elif style == 'linetype':
                curve.setStyle(self.linetypes[value])
            elif style == 'linestyle':
                curve.pen().setStyle(self.linestyles[value])
            elif style == 'linewidth':
                curve.pen().setWidth(value)

            self.redraw()
        except:
            pass



