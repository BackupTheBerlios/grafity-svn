import os
import sys

from qt import *
from qwt import *

import grafity
from grafity.signals import HasSignals
from grafity.actions import undo, redo

from grafity.ui.main import MainWindowUI
from grafity.ui.graph_style import GraphStyleUI
from grafity.ui.graph_data import GraphDataUI
from grafity.ui_console import Console

class EventHandler(QObject):
    def __init__(self, object, callback):
        QObject.__init__(self, object)
        self.object, self.callback = object, callback

    def eventFilter(self, object, event):
        return self.callback(event)

def connectevents(object, callback):
    object.installEventFilter(EventHandler (object, callback))

def getpixmap(name, pixmaps={}):
    if name not in pixmaps:
        pixmaps[name] = QPixmap(os.path.join(grafity.DATADIR, 'data', 'images', '16', name+'.png'))
    return pixmaps[name]

class WorksheetView:
    pass

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
            if it.current().isSelected() and isinstance(it.current()._object, grafity.Worksheet):
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
        xcols = [str(self.x_list.text(a)) for a in range(self.x_list.count()) if self.x_list.isSelected(a)]
        ycols = [str(self.y_list.text(a)) for a in range(self.y_list.count()) if self.y_list.isSelected(a)]

        for w in self.selected:
            for x in xcols:
                for y in ycols:
                    self.graph.add(w[x], w[y])

    def on_remove(self):
        for d in self.graph._view.datasets:
            self.graph.remove(d)

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
        pixmap = getpixmap({grafity.Worksheet: 'worksheet', 
                            grafity.Graph: 'graph', 
                            grafity.Folder: 'folder'}[type(obj)])
        item.setPixmap (0, pixmap)
#        item.setOpen (True)
        item._object = obj
        if recursive and isinstance(obj, grafity.Folder):
            for child in obj:
                if isinstance(child, (grafity.Folder, grafity.Worksheet)):
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

        for d in self.graph.datasets:
            self.on_add_dataset(d)
        self.update_legend()

    def on_add_dataset(self, d):
        d._curveid = self.plot.insertCurve('')
        d.recalculate()
        for s in ['symbol', 'color', 'size', 'linetype', 'linestyle', 'linewidth']:
            self.on_change_style(d, s, d.get_style(s))
        self.plot.replot()
     
    def on_remove_dataset(self, d):
        self.plot.removeCurve(d._curveid)
        self.plot.replot()

    def on_legend_select(self):
        self.datasets = [self.graph.datasets[n] for n in range(self.legend.count())
                                                if self.legend.isSelected(n)]

        self.graph.emit('selection-changed', self.datasets)

    def update_legend(self):
        selected = [self.legend.isSelected(it) for it in range(self.legend.numRows())]
        current = self.legend.currentItem()

        self.legend.clear()
        self.legend.insertStrList([str(d) for d in self.graph.datasets])
        for n, dset in enumerate(self.graph.datasets):
            self.legend.changeItem(self.draw_pixmap(dset), self.legend.text(n), n)

        for i,on in enumerate(selected):
            self.legend.setSelected(i, on)
        self.legend.setCurrentItem(current)


    def draw_pixmap(self, dataset):
        p = QPixmap()
        p.resize(20, 10)
        p.fill(self.legend_background_color)
        paint = QPainter()
        paint.begin(p)

        paint.setPen (self.plot.curve(dataset._curveid).pen())
        paint.drawLine (2,5, 18,5)

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
        self.plot.replot()

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
        self.plot.replot()

    symbols = {'circle': QwtSymbol.Ellipse,
               'square': QwtSymbol.Rect,
               'diamond': QwtSymbol.Diamond,
               'triangleup': QwtSymbol.UTriangle,
              }


    colors = [Qt.black, Qt.red, Qt.darkRed, Qt.green, Qt.darkGreen,
              Qt.blue, Qt.darkBlue, Qt.cyan, Qt.darkCyan, Qt.magenta, Qt.darkMagenta,
              Qt.yellow, Qt.darkYellow, Qt.gray, Qt.darkGray, Qt.lightGray, Qt.black]

    extracolornames = [ 'CadetBlue3', 'CornflowerBlue', 'DarkGoldenrod1',
                        'DarkOliveGreen2', 'DarkOrange1', 'DarkSalmon',
                        'DarkTurquoise', 'DeepPink2', 'DeepSkyBlue1',
                        'DodgerBlue3', 'HotPink', 'HotPink3', 'IndianRed',
                        'LightGreen', 'MediumPurple4', 'MediumViloetRed' ]

    colors += [QColor(s) for s in extracolornames]

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

            self.plot.replot()
        except:
            pass


class Panel(QDockWindow):
    """A panel in the main window similar to IDEAl mode"""
    def __init__(self, mainwin, position):
        QDockWindow.__init__(self, QDockWindow.InDock, mainwin)
        self.setMovingEnabled(False)
        self.setVerticallyStretchable(True)
        mainwin.moveDockWindow(self, position, True, 0)
        self.position = position

        if self.position in [QMainWindow.DockTop, QMainWindow.DockBottom]:
            Box1 = QVBox
            Box2 = QHBox
        elif self.position in [QMainWindow.DockLeft, QMainWindow.DockRight]:
            Box1 = QHBox
            Box2 = QVBox

        self.setResizeEnabled(True)

        box = Box1(self)
        self.setWidget(box)

        if self.position in [QMainWindow.DockLeft, QMainWindow.DockTop]:
            self.buttons0 = Box2(box)

        self.stack = QWidgetStack(box)
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if self.position in [QMainWindow.DockBottom, QMainWindow.DockRight]:
            self.buttons0 = Box2(box)

        self.buttons = Box2(self.buttons0)
        QLabel(self.buttons0)
        self.buttons.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btns = {}
        self.stack.hide()

    def add(self, name, pixmap, widget):
        if self.position in [QMainWindow.DockTop, QMainWindow.DockBottom]:
            orientation = '-'
            btn = self.make_button(self.buttons, pixmap, name, '-')
        elif self.position in [QMainWindow.DockLeft, QMainWindow.DockRight]:
            orientation = '|'
            btn = self.make_button(self.buttons, pixmap, name, '|')
        self.connect(btn, SIGNAL('toggled(bool)'), self.make_callback(name, widget))
        self.btns[name] = btn
        self.stack.addWidget(widget)
   
    def make_callback(self, name, widget):
        def callback(on, height=[150]):
            if on:
                for n, b in self.btns.items():
                    if n != name:
                        b.setOn(False)
                self.stack.raiseWidget(widget)
                if hasattr(widget, 'open'):
                    widget.open()
                self.stack.show()
                if height[0] is not None:
                    if self.position in [QMainWindow.DockLeft, QMainWindow.DockRight]:
                        self.setFixedExtentWidth(height[0])
                    elif self.position in [QMainWindow.DockTop, QMainWindow.DockBottom]:
                        self.setFixedExtentHeight(height[0])
            else:
                self.stack.hide()
                if self.position in [QMainWindow.DockLeft, QMainWindow.DockRight]:
                    height[0] = self.width()
                    self.setFixedExtentWidth(0)
                elif self.position in [QMainWindow.DockTop, QMainWindow.DockBottom]:
                    height[0] = self.height()
                    self.setFixedExtentHeight(0)
        setattr(self, '_%s_callback' % name, callback)
        return callback

    def make_button(self, parent, pixmap, label, orientation):
        btn2 = QPushButton(parent)
        btn2.setToggleButton(True)
        btn2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        pal = QPalette(btn2.palette())
        cg = QColorGroup(pal.active())
        cg.setColor(QColorGroup.Base,cg.color(QColorGroup.Background))
        bgcolor = cg.color(QColorGroup.Background)

        p = QPixmap()
        if orientation == '-':
            p.resize (90, 20)
        elif orientation == '|':
            p.resize (20, 90)
        p.fill (bgcolor)

        paint = QPainter()
        paint.begin(p)
        paint.drawPixmap (0, 0, pixmap)
        r = QRect()
        if orientation == '|':
            paint.rotate(90)
            paint.drawText (22, -2, label)
        else:
            paint.drawText (25, 15, label)
        paint.end()

        p.setMask(p.createHeuristicMask())

        btn2.setPixmap(p)

        return btn2

class ProjectExplorer(HasSignals, QListView):
    def __init__(self, parent):
        QListView.__init__(self, parent)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.setMinimumSize(QSize(150,0))
#        self.setMaximumSize(QSize(150,32767))
        self.header().hide()
        self.addColumn ('Object', 145)
        self.setSelectionMode(QListView.Extended)

        QObject.connect(self, SIGNAL("doubleClicked(QListViewItem *, const QPoint &, int)"), self.on_doubleclick)
        QObject.connect(self, SIGNAL("itemRenamed (QListViewItem *, int, const QString &)"), self.on_rename)
        QObject.connect(self, SIGNAL("contextMenuRequested (QListViewItem *, const QPoint &, int)"),
                      self.on_context_menu_requested)

        self.wsheet_context_menu = QPopupMenu (self)
        self.wsheet_context_menu.insertItem ('Show', self.wsheet_context_menu_show)
        self.wsheet_context_menu.insertSeparator ()
        self.wsheet_context_menu.insertItem ('Delete', self.wsheet_context_menu_del)
        self.wsheet_context_menu.insertItem ('Import ASCII...', self.wsheet_context_menu_importascii)
 
        self.graph_context_menu = QPopupMenu (self)
        self.graph_context_menu.insertItem ('Show', self.graph_context_menu_show)
        self.graph_context_menu.insertSeparator ()
        self.graph_context_menu.insertItem ('Delete', self.graph_context_menu_del)
        self.graph_context_menu.insertItem ('Properties...', self.graph_context_menu_properties)
        self.graph_context_menu.insertItem ('Fit...', self.graph_context_menu_startfit)

        self.project = None

    def set_project(self, project):
        if self.project is not None:
            self.project.disconnect('add-item', self.on_add_item)
            self.project.disconnect('remove-item', self.on_remove_item)
        self.project = project
        self.clear()
        if self.project is not None:
            self.project.connect('add-item', self.on_add_item)
            self.project.connect('remove-item', self.on_remove_item)

#        project.top._tree_item = QListViewItem(self, 'top')
            self.on_add_item(self.project.top, recursive=True)
            project.top._tree_item.setOpen (True)
#        for folder in self.project.top.all_subfolders():
#            self.on_add_item(folder)
            

    def on_add_item(self, obj, recursive=False):
        try:
            parent = obj.parent._tree_item
        except AttributeError:
            parent = self
        item = obj._tree_item = QListViewItem(parent, obj.name)
        pixmap = getpixmap({grafity.Worksheet: 'worksheet', 
                            grafity.Graph: 'graph', 
                            grafity.Folder: 'folder'}[type(obj)])
        item.setPixmap (0, pixmap)
#        item.setOpen (True)
        item._object = obj
        if recursive and isinstance(obj, grafity.Folder):
            for child in obj:
                self.on_add_item(child, recursive=True)

    def on_remove_item(self, obj):
        obj.parent._tree_item.takeItem(obj._tree_item)
        del obj._tree_item

    def on_rename (self, item, column, text):
        if item.parent() == self.wsitem:
            item.obj.name = str(text)
        elif item.parent() == self.gritem:
            item.obj.name = str(text)

    def on_doubleclick(self, item, point, column):
        HasSignals.emit(self, 'activated', item._object)

    def dragObject(self):
        selected_worksheets = [w.name for w in project.worksheets if self.isSelected(w._explorer_item)]
        selected_graphs = [g.name for g in project.graphs if self.isSelected(g._explorer_item)]
        drag = QTextDrag('(' + ', '.join(selected_worksheets) + ' ,' + ', '.join(selected_graphs) + ')', self)
        return drag

    def on_context_menu_requested(self, item, point, column):
        if item is None:
            return
        if isinstance(item._object, grafity.Worksheet):
            self.wscontextitem = item._object
            self.wsheet_context_menu.popup(point)
        elif isinstance(item._object, grafity.Graph):
            self.grcontextitem = item._object
            self.graph_context_menu.popup(point)
            
    def graph_context_menu_show (self):
        self.grcontextitem.show()

    def graph_context_menu_del (self):
        project.remove(self.grcontextitem)

    def graph_context_menu_properties (self):
        self.grcontextitem.properties()

    def graph_context_menu_startfit (self):
        self.grcontextitem.start_fit()
 
    def wsheet_context_menu_show (self):
        v = WorksheetView (self.wscontextitem)
        v.show()
        v._table.horizontalHeader()

    def wsheet_context_menu_del (self):
        project.remove(self.wscontextitem)

    def wsheet_context_menu_importascii (self):
        # do something
        pass

class Cancel(Exception):
    pass

class MainWindow(MainWindowUI):
    def __init__(self):
        MainWindowUI.__init__(self)

        self.mainbox = QVBox(self)
        self.setCentralWidget(self.mainbox)

        self.workspace = QWorkspace(self.mainbox)
        self.workspace.setScrollBarsEnabled(True)
        self.connect(self.workspace, SIGNAL("windowActivated(QWidget *)"), self.on_window_activated)

        self.recent = grafity.settings.get('windows', 'recent')
        if self.recent in [None, '']:
            self.recent = []
        else:
            self.recent = [s for s in self.recent.split(' ') if os.path.isfile(s)]
        self.recentids = []

#        self.history = QListBox(self.workspace)
#        self.connect(self.history, SIGNAL("doubleClicked(QListBoxItem*)"), self.history_select)
#        self.history.setIcon(QPixmap(project.datadir + 'pixmaps/undo_history.png'))
#        self.history.setCaption('History')
#        self.history.hide()

### status bar #################################################################################

        self.statusBar().show()
        self.statusBar().message ("Welcome to Grafity", 1000)
        self.statuslabel = QLabel (self, 'Pikou')
        self.statusBar().addWidget (self.statuslabel, 0, True)
        self.statuslabel.setText ("")
        self.progressbar = QProgressBar(100, self)
        self.statusBar().addWidget (self.progressbar, 0, True)
        self.progressbar.hide()

### bottom panel ###############################################################################

        locals = {}
        self.bpanel = Panel(self, QMainWindow.DockBottom)
        self.script = Console(self.bpanel, locals=locals)
        self.script.cmd(['from grafity import *'])
        self.script.cmd(['from grafity.arrays import *'])
        locals['mainwin'] = self
        locals['undo'] = undo
        locals['redo'] = redo
        self.script.clear()

        self.bpanel.add('Script', getpixmap('console'), self.script)

### left panel #################################################################################
        self.lpanel = Panel(self, QMainWindow.DockLeft)
        self.explorer = ProjectExplorer(self.lpanel)
        self.explorer.connect('activated', self.on_activated)
        self.lpanel.add('Explorer', getpixmap('folder'), self.explorer)
        self.lpanel._Explorer_callback(True)

### right panel ################################################################################
        
        self.rpanel = Panel(self, QMainWindow.DockRight)
        self.graph_data = GraphData(self.bpanel, self)
        self.graph_style = GraphStyleUI(self.bpanel)
        self.rpanel.add('Data', getpixmap('console'), self.graph_data)
        self.rpanel.add('Axes', getpixmap('console'), self.graph_style)

        self.open_project(grafity.Project('test/pdms.gt'))

    def on_activated(self, obj):
        if isinstance(obj, grafity.Graph):
            obj._view = GraphView(self.workspace, obj)
            obj._view.show()

    def open_project(self, project):
        """Connect a project to the gui"""
        self.project = project

        self.explorer.set_project(self.project)
        self.graph_data.set_project(self.project)

#        self.project.connect('change-current-folder', self.on_change_folder)
        self.script.locals['project'] = self.project

    def close_project(self):
        """Disconnect the current project form the gui"""
#        self.project.disconnect('change-current-folder', self.on_change_folder)
        self.explorer.set_project(None)
        # and close all pages
        self.project = None

    def ask_save(self):
        """Prepare to close the project. Ask the user whether to
        save changes and save is necessary. Raises Cancel if
        the user cancels.
        """
        if not self.project.modified:
            return
        message = "<b>Do you want to save the changes you made to the document?</b>" \
                  "<p>Your changes will be lost if you don't save them"
        resp = QMessageBox.information(None, "Grafit", message, 
                                       "&Save",  "&Cancel", "&Don't Save", 0, 1)
        if resp == 0:
            self.on_project_save()
        if resp == 1:
            raise Cancel
        elif resp == 2:
            pass

    # Menu and toolbar actions

    def on_graph_mode(self):
        modes = ['arrow', 'hand', 'zoom', 'range', 'dreader', 'sreader']
        mode = modes[[getattr(self, 'act_graph_%s'%a).isOn() for a in modes].index(True)]
 

    def on_project_open(self):
        """File/Open"""
        try:
            self.ask_save()
        except Cancel:
            return

        filesel = QFileDialog(self)
        if filesel.exec_loop() != 1:
            return
        self.close_project()
        self.open_project(grafity.Project(str(filesel.selectedFile())))

    def on_project_save(self):
        if self.project.filename is not None:
            self.project.commit()
        else:
            self.on_file_saveas(item)

    def on_project_saveas(self):
        filesel = QFileDialog(self)
        filesel.setMode(QFileDialog.AnyFile)
        if filesel.exec_loop() != 1:
            return
        self.project.saveto(str(filesel.selectedFile()))
        self.close_project()
        self.open_project(grafity.Project(str(filesel.selectedFile())))

    def on_project_new(self):
        try:
            self.ask_save()
        except Cancel:
            return
        self.close_project()
        self.open_project(grafity.Project())

    def on_new_folder(self):
        self.project.new(grafity.Folder)
        
    def on_new_worksheet(self):
        self.project.new(grafity.Worksheet)

    def on_new_graph(self):
        self.project.new(grafity.Graph)

    def fileMenuAboutToShow(self):
        return
        menu = self.menus['&File']
        for id in self.recentids:
            menu.removeItem(id)

        self.recentids = []
        for i, name in enumerate(self.recent):
            id = menu.insertItem('%d. %s' % (i, name), self.on_recent, 0, -1, 5+i)
            menu.setItemParameter(id, i)
            self.recentids.append(id)

    def on_recent(self, id):
        project.load(self.recent[id])

    def windowMenuAboutToShow(self):
        menu = self.menus['&Window']
        menu.clear()

        menu.insertSeparator()

        for i, win in enumerate(self.workspace.windowList()):
            id = menu.insertItem('&%d %s' % (i, win.caption()))
            menu.setItemParameter(id, i)
            menu.setItemChecked(id, self.workspace.activeWindow() == win)

    def on_window_activated(self, window):
        if window is None:
            return

        self.active = window
        self.worksheet_toolbar.hide()
        self.graph_toolbar.hide()
        self.rpanel.hide()

        if isinstance(window, GraphView):
            self.rpanel.show()
            self.graph_toolbar.show()
            self.graph_data.set_graph(window.graph)
        elif isinstance(window, WorksheetView):
            self.worksheet_toolbar.show()

    def clear (self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            aw.clear_selected()

    def delete (self):
        pass

    def closeEvent (self, event):
        self.exit()

    def exit(self):
        grafity.settings.set('windows', 'recent', ' '.join(self.recent))
        
#        s = QString()
#        st = QTextStream(s, IO_WriteOnly)
#        st << self
#        s = str(s)
#        settings.set('windows', 'toolbars', s)
#        project.settings['/grafit/console/history'] = '\n'.join(self.script.history[-20:])
        grafity.settings.set('script', 'history', '\n'.join(self.script.history[-20:]))
        
        try:
            self.ask_save()
        except Cancel:
            return
        else:
            QApplication.exit(0)
        
    def status_message(self, msg, time = 1000):
        self.statusBar().message(msg, time)

    def about(self):
        a = AboutWindow(self)  
        a.exec_loop()

    def help(self):
        from grafit.help import HelpWidget
        h = HelpWidget(self)
        h.show()
def splash_message(text):
    if __name__ == '__main__':
        splash.message (text, Qt.AlignLeft, Qt.gray)
    pass


