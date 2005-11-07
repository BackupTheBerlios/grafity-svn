import inspect
import os
import sys

try: sys.modules['__main__'].splash_message('loading Main')
except: pass

from qt import *
from qttable import *

from grafit.project import project
from grafit.script import Console
from grafit.worksheet import Worksheet, WorksheetView
from grafit.graph import Graph, GraphView

class Panel(QDockWindow):
    """A panel in the main window similar to IDEAl mode"""
    def __init__(self, mainwin, position):
        QDockWindow.__init__(self, QDockWindow.InDock, mainwin)
        mainwin.moveDockWindow(self, position)
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

        self.stack = QWidgetStack(box)
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
            p.resize (70, 20)
        elif orientation == '|':
            p.resize (20, 70)
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



class Notes(QTabWidget):
    def __init__(self, parent):
        QTabWidget.__init__(self, parent)
        self.setCaption('Notes')
        self.addTab(QTextEdit(), 'Note 1')

class ListViewItem (QListViewItem):
    def __init__ (self, parent, text, obj):
        QListViewItem.__init__ (self, parent, text)
        self.obj=obj



class AboutWindow(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        self.image0 = QPixmap(project.datadir + 'pixmaps/logo.png')

        if not name:
            self.setName("About")

        Form1Layout = QVBoxLayout(self,11,6,"Form1Layout")

        self.tabWidget3 = QTabWidget(self,"tabWidget3")

        self.tab = QWidget(self.tabWidget3,"tab")
        tabLayout = QVBoxLayout(self.tab,11,6,"tabLayout")

        self.textLabel1 = QLabel(self.tab,"textLabel1")
        self.textLabel1.setSizePolicy(QSizePolicy(5,0,0,0,self.textLabel1.sizePolicy().hasHeightForWidth()))
        self.textLabel1.setMargin(20)
        self.textLabel1.setAlignment(QLabel.WordBreak | QLabel.AlignTop | QLabel.AlignHCenter)
        tabLayout.addWidget(self.textLabel1)

        self.pixmapLabel1 = QLabel(self.tab,"pixmapLabel1")
        self.pixmapLabel1.setSizePolicy(QSizePolicy(5,7,0,0,self.pixmapLabel1.sizePolicy().hasHeightForWidth()))
        self.pixmapLabel1.setPixmap(self.image0)
        self.pixmapLabel1.setScaledContents(1)
        tabLayout.addWidget(self.pixmapLabel1)
        self.tabWidget3.insertTab(self.tab,QString(""))

        self.tab_2 = QWidget(self.tabWidget3,"tab_2")
        tabLayout_2 = QHBoxLayout(self.tab_2,11,6,"tabLayout_2")

        self.textLabel1_2 = QLabel(self.tab_2,"textLabel1_2")
        self.textLabel1_2.setMargin(20)
        self.textLabel1_2.setAlignment(QLabel.WordBreak | QLabel.AlignTop | QLabel.AlignHCenter)
        tabLayout_2.addWidget(self.textLabel1_2)
        self.tabWidget3.insertTab(self.tab_2,QString(""))

        self.TabPage = QWidget(self.tabWidget3,"TabPage")
        TabPageLayout = QHBoxLayout(self.TabPage,11,6,"TabPageLayout")

        self.textBrowser1 = QTextBrowser(self.TabPage,"textBrowser1")
        TabPageLayout.addWidget(self.textBrowser1)
        self.tabWidget3.insertTab(self.TabPage,QString(""))
        Form1Layout.addWidget(self.tabWidget3)

        layout2 = QHBoxLayout(None,0,6,"layout2")
        spacer2 = QSpacerItem(311,31,QSizePolicy.Expanding,QSizePolicy.Minimum)
        layout2.addItem(spacer2)

        self.closebtn = QPushButton(self,"closebtn")
        layout2.addWidget(self.closebtn)
        Form1Layout.addLayout(layout2)

        self.languageChange()

        self.resize(QSize(357,324).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

    def languageChange(self):
        self.setCaption(self.__tr("About grafit"))
        self.textLabel1.setText(self.__tr("<b>grafit</b> version 0.0.r%s<br>\n"
"Data directory: /home/daniel/grafit/<br>Latest revision: %s" % (project.revision, project.latestrevision)))
        self.tabWidget3.changeTab(self.tab,self.__tr("Version"))
        self.textLabel1_2.setText(self.__tr("<b>Daniel Fragiadakis</b> <a href='mailto:danielf@mail.ntua.gr'>danielf@mail.ntua.gr</a><br><br>"))
        self.tabWidget3.changeTab(self.tab_2,self.__tr("Authors"))
        self.textBrowser1.setText(self.__tr("grafit is Copyright (C) 2003-2004 by Daniel Fragiadakis\n"
"\n"
"This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.\n"
"\n"
"Grafit is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.\n"
"See the GNU General Public License for more details.\n"
"You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA."))
        self.tabWidget3.changeTab(self.TabPage,"Copyright")
        self.closebtn.setText("Close")
        self.connect(self.closebtn, SIGNAL('clicked()'), self.close)

    def __tr(self,s,c = None):
        return qApp.translate("Form1",s,c)

class ProjectExplorer(QListView):
    def __init__(self, parent):
        QListView.__init__(self, parent)
        self.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Expanding)
        self.setMinimumSize(QSize(150,0))
        self.setMaximumSize(QSize(150,32767))
        self.header().hide()
        self.addColumn ('Object', 145)
        self.connect (self, SIGNAL("doubleClicked(QListViewItem *, const QPoint &, int)"), \
                      self.on_doubleclick)
        self.connect (self, SIGNAL("itemRenamed (QListViewItem *, int, const QString &)"), \
                      self.on_rename)
        self.connect (self, SIGNAL("contextMenuRequested (QListViewItem *, const QPoint &, int)"), \
                      self.on_context_menu_requested)

        self.setSelectionMode(QListView.Extended)
      
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

        self.folders = {}
        names = [o._folder for o in project.worksheets + project.graphs]
        for n in names:
            self.folders[n] = QListViewItem(self, n)
            self.folders[n].setPixmap (0, QPixmap(project.datadir + "pixmaps/open-folder.png"))
            self.folders[n].setOpen (True)

        self.wsitem = QListViewItem (self, "Worksheets")
        self.wsitem.setPixmap (0, QPixmap(project.datadir + "pixmaps/open-folder.png"))
        self.wsitem.setOpen (True)
        self.gritem = QListViewItem (self, "Graphs")
        self.gritem.setPixmap (0, QPixmap(project.datadir + "pixmaps/open-folder.png"))
        self.gritem.setOpen (True)
#        self.historyitem = QListViewItem (self, "History")
#        self.historyitem.setPixmap (0, QPixmap("pixmaps/history-small.png"))

    def on_doubleclick (self, item, point, column):
        if item==None:
            return
        if item.parent() == self.wsitem:
            project.w[item.text(0)]._view.hide()
            project.w[item.text(0)]._view.show()
        elif item.parent() == self.gritem:
            project.g[item.text(0)].hide()
            project.g[item.text(0)].show()

    def dragObject(self):
        selected_worksheets = [w.name for w in project.worksheets if self.isSelected(w._explorer_item)]
        selected_graphs = [g.name for g in project.graphs if self.isSelected(g._explorer_item)]
        drag = QTextDrag('(' + ', '.join(selected_worksheets) + ' ,' + ', '.join(selected_graphs) + ')', self)
        return drag

    def on_context_menu_requested(self, item, point, column):
        if item is None:
            return
        if item.parent() == self.wsitem:
            self.wsheet_context_menu.popup (point)
            self.wscontextitem = project.w[item.text(0)]
        elif item.parent() == self.gritem:
            self.graph_context_menu.popup (point)
            self.grcontextitem = project.g[item.text(0)]

    def on_rename (self, item, column, text):
        if item.parent() == self.wsitem:
            item.obj.name = str(text)
        elif item.parent() == self.gritem:
            item.obj.name = str(text)

    def remove (self, obj):
        if isinstance (obj, Worksheet):
            self.wsitem.takeItem(obj._explorer_item)
            del obj._explorer_item
        if isinstance (obj, Graph):
            self.gritem.takeItem(obj._explorer_item)
            del obj._explorer_item

    def add (self, obj):
        if isinstance (obj, Worksheet):
            i = ListViewItem (self.wsitem, obj.name, obj)
            i.setRenameEnabled (0, True)
            i.setDragEnabled (True)
            i.setPixmap (0, QPixmap(project.datadir + 'pixmaps/wsheet.png'))
            obj._explorer_item = i
#            for name in obj.column_names:
#                i = ListViewItem (obj._explorer_item, name, name)
        elif isinstance (obj, Graph):
            i = ListViewItem (self.gritem, obj.name, obj)
            i.setRenameEnabled (0, True)
            i.setDragEnabled (True)
            i.setPixmap (0, QPixmap(project.datadir + 'pixmaps/graph.png'))
            obj._explorer_item = i

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



class MainWindow(QMainWindow):
    def __init__(self,parent = None,name = None,fl = 0):
        QMainWindow.__init__(self,parent,name,fl)

        self.setCaption ('Grafit')

        self.view_back = QVBox (self)
        self.workspace = QWorkspace (self.view_back)
        self.workspace.setScrollBarsEnabled (True)
        self.setCentralWidget(self.view_back)
        self.resize(QSize(565,362).expandedTo(self.minimumSizeHint()))
        self.connect (self.workspace, SIGNAL("windowActivated(QWidget *)"), self.on_window_activated)
        
        self.recent = project.settings['/grafit/recent_projects']
        if self.recent in [None, '']:
            self.recent = []
        else:
            self.recent = [s for s in self.recent.split(' ') if os.path.isfile(s)]
        self.recentids = []

#------------------------------------------------------------------------------------------
# Console

        self.history = QListBox(self.workspace)
        self.connect(self.history, SIGNAL("doubleClicked(QListBoxItem*)"), self.history_select)
        self.history.setIcon(QPixmap(project.datadir + 'pixmaps/undo_history.png'))
        self.history.setCaption('History')
        self.history.hide()

#        from grafit.gl import GLGraphWidget
#        self.gl = GLGraphWidget(self.workspace)
#        self.gl.show()

#        self.notes = Notes(self.workspace)
#        self.notes.setIcon(QPixmap(project.datadir + 'pixmaps/notes.png'))
#        self.notes.hide()

#------------------------------------------------------------------------------------------
# Project explorer

        self.explorerwindow = QDockWindow(QDockWindow.InDock, self)
        self.explorerwindow.show()
        self.explorerwindow.setVerticallyStretchable (True)
        self.explorerwindow.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Expanding)
        self.moveDockWindow (self.explorerwindow, self.DockLeft)

#        self.tips = QDockWindow(QDockWindow.InDock, self)
#        self.tips.show()
#        self.tips.setVerticallyStretchable (True)
#        self.tips.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)
#        self.moveDockWindow (self.tips, self.DockRight)

#        self.tiplabel = QLabel(self.tips)
#        self.tiplabel.setText('Welcome to Grafit')
#        self.tips.setWidget(self.tiplabel)

        self.explorer = ProjectExplorer(self.explorerwindow)
        self.explorerwindow.setWidget (self.explorer)

        self.statusBar().message ("Welcome to <b>Grafit</b>", 1000)
        self.statuslabel = QLabel (self, 'Pikou')
        self.statusBar().addWidget (self.statuslabel, 0, True)
        self.statuslabel.setText ("")
        self.progressbar = QProgressBar(100, self)
        self.statusBar().addWidget (self.progressbar, 0, True)
        self.progressbar.hide()

        project.addobserver (self.observe_project)

################################################################################################

        self.bpanel = Panel(self, QMainWindow.DockBottom)
        self.script = Console(self.bpanel)
        self.bpanel.add('Script', QPixmap(project.datadir + 'pixmaps/console-small.png'), self.script)

################################################################################################
        self.rpanel = Panel(self, QMainWindow.DockRight)

        from grafit.graph_properties import GraphDataPanel, GraphStylePanel, GraphAxesPanel
        self.rpanel.Data = GraphDataPanel(self.rpanel)
        self.rpanel.add('Data', QPixmap(project.datadir +'pixmaps/wsheet.png'), self.rpanel.Data)
        self.rpanel.Style = GraphStylePanel(self.rpanel)
        self.rpanel.add('Style', QPixmap(project.datadir+'pixmaps/style.png'), self.rpanel.Style)
        self.rpanel.Axes = GraphAxesPanel(self.rpanel)
        self.rpanel.add('Axes', QPixmap(project.datadir+'pixmaps/axes.png'), self.rpanel.Axes)

################################################################################################        

#------------------------------------------------------------------------------------------
# Menus and toolbars

        self.actions = {
         'new_ws': [ "New Worksheet", "New &Worksheet", "newwsheet.png", 
                      project.new_worksheet, False, None],
         'new_gr': [ "New Graph", "New &Graph", "newgraph.png", project.new_graph, False, None],
         'new_folder': [ "New Folder", "New &Folder", "new-folder.png", project.new_graph, False, None],
         'imp_ascii': [ "Import ASCII", "&Import ASCII...", "import_ascii.png", self.importAscii, False, None],
         'new_prj': [ "New Project", "New &Project", "filenew.png", self.new_project_do, False, None],
         'open_prj': [ "Open Project", "&Open Project...", "fileopen.png", 
                        self.open_project_do, False, None],
         'save_prj': [ "Save Project", "&Save Project", "filesave.png", 
                        self.save_project_do,  False, None],
         'save_prj_as': [ "Save Project As", "Save Project &As...", "filesaveas.png", 
                           self.save_project_as_do, False, None],
         'exit': [ "Exit", "E&xit", "exit.png", self.exit, False, None],
         'history': [ "History", "&History", "undo_history.png", self.view_history, True, None],
#         'notes': [ "Notes", "&Notes", "notes.png", self.view_notes, True, None],
	 
         'g_arrow': [ "", "", "arrow.png", self.graph_mode, True, None],
         'g_hand': [ "<b>left:</b> move fit function", "", "hand.png", self.graph_mode, True, None],
         'g_zoom': [ "<b>left:</b> zoom in<br><b>right:</b> zoom out<br><b>middle</b>: auto "
                     " zoom<hr><b> shift+middle:</b> auto zoom on dataset", 
                     "", "zoom.png", self.graph_mode, True, None],
         'g_range':[ "<b>left:</b> set range start<br><b>right:</b> set range end<br>"
                     "<b>middle:</b>set range auto", 
                     "", "range.png", self.graph_mode, True, None],
         'g_dreader': [ "<b>left:</b> read data coordinates / select dataset<hr><b>shift+left:</b> move point<br>"
                        "<b>ctrl+shift+left:</b> move entire curve", "", 
                        "dreader.png", self.graph_mode, True, None],
         'g_sreader': [ "<b>left:</b> read graph coordinates<hr><b>shift+left:</b> delete data", 
                        "", "sreader.png", self.graph_mode, True, None],
         'cut': [ "Cut", "Cut", "cut.png", self.cut, False, 'Ctrl+X'],
         'copy': [ "Copy", "Copy", "copy.png", self.copy, False, 'Ctrl+C'],
         'paste': [ "Paste", "Paste", "paste.png", self.paste, False, 'Ctrl+V'],
         'clear': [ "Clear", "Clear", "delete.png", self.clear, False, 'Delete'],
         'delete' : [ "Delete", "Delete", "delete.png", self.delete, False, None],
         'undo' : [ "Undo", "Undo", "undo.png", self.undo, False, 'Ctrl+Z'],
         'redo' : [ "Redo", "Redo", "redo.png", self.redo, False, 'Ctrl+R'],
         'duplicate' : [ "Duplicate", "Duplicate", "duplicate.png", self.duplicate_do, False, None],

         'w_addcolumn' : [ "Add Column", "Add Column", "addcolumn.png", self.on_add_column, False, None],
         'w_delcolumn' : [ "Delete Column", "Add Column", "delcolumn.png", self.on_remove_column, False, None],
         'w_colright' : [ "Move Column Right", "Move Column Right", "colright.png", self.MoveColumnRight, False, None],
         'w_colleft' : [ "Move Column Left", "Move Column Left", "colleft.png", self.MoveColumnLeft, False, None],
#         'w_sortcol' : [ "Sort Column", "Sort Column", "sort.png", commands.MoveColumnLeft, False, None],
#         'w_sortws' : [ "Sort Worksheet", "Sort Worksheet", "sort.png", commands.MoveColumnLeft, False,None],

         'run_script' : [ "Run Script", "Run Script...", "run.png", self.RunScript, False, None],

         'prefs' : [ "Preferences", "&Preferences...", "properties.png", self.Preferences, False, None],
         'about' : [ "About", "&About...", None, self.about, False, None],
         'manual' : [ "Manual", "&Manual...", None, self.help, False, None],
        }

        for k, a in self.actions.items():
            self.actions[k] = self.action_from_tuple(a)

        # create menus
        self.menudesc = [
         [ '&File', [ 'new_prj', 'open_prj', 'save_prj', 'save_prj_as', 0, 0, 
                      'exit' ]],
         [ '&Edit', [ 'undo', 'redo', 0,
                      'cut', 'copy', 'paste', 'clear', 0,
                      'duplicate', 0,
                      'delete' ]],
         [ '&Worksheet', [ 'new_ws', 'imp_ascii', 0,
                           'w_addcolumn', 'w_colleft', 'w_colright', 0, ]],
         [ '&Graph', [ 'new_gr' ]],
         [ '&Analysis', [ ]],
         [ '&Tools', [ 'run_script', 0,
                       'prefs', ]],
         [ '&Window', [ 'history', 0 ]],
         [ '&Help', [ 'about', 'manual']],
        ]

        self.MenuBar = QMenuBar(self,"MenuBar")
        self.menus = {}
        for m in self.menudesc:
            self.menus[m[0]] = QPopupMenu (self)
            self.MenuBar.insertItem (m[0], self.menus[m[0]])
            for item in m[1]:
                if item: self.actions[item].addTo (self.menus[m[0]])
                else: self.menus[m[0]].insertSeparator ()

        self.connect(self.menus['&File'], SIGNAL('aboutToShow()'), self.fileMenuAboutToShow)
        self.connect(self.menus['&Window'], SIGNAL('aboutToShow()'), self.windowMenuAboutToShow)

        # create toolbars
        self.toolbardesc = [
         [ 'File', [ 'new_prj', 'open_prj', 'save_prj', 'save_prj_as', 0, 
                      'new_ws', 'new_gr', 'new_folder', 0, 
                      'imp_ascii', 0,
                      'exit' ]],
         [ 'Edit', [ 'copy', 'cut', 'paste', 'clear', 0,
                     'duplicate', 0, 
                     'undo', 'redo' ]],
         [ 'View', [ 'history', ]],
         [ 'Worksheet', [ 'w_addcolumn', 'w_delcolumn', 'w_colleft', 'w_colright', ]],
        ]

        self.toolbars = {}
        for m in self.toolbardesc:
            self.toolbars[m[0]] = QToolBar (m[0], self, Qt.DockTop)
            for item in m[1]:
                if item: self.actions[item].addTo (self.toolbars[m[0]])
                else: self.toolbars[m[0]].addSeparator ()

        self.graph_toolbar = QToolBar ('Graph', self, Qt.DockLeft)
        self.actions_graph = QActionGroup (self)
        for a in [ 'g_arrow', 'g_hand', 'g_zoom', 'g_range', 'g_dreader', 'g_sreader', ]:
            self.actions[a].setStatusTip("")
            self.actions_graph.add (self.actions[a])
        self.actions_graph.addTo (self.graph_toolbar)
        self.actions['g_arrow'].setOn (True)
        self.toolbars['Graph'] = self.graph_toolbar

        self.moveDockWindow(self.toolbars['Worksheet'], Qt.DockLeft)

        # load dock window dimensions
        s = project.settings['/grafit/windows/toolbars']
        if s is not None:
            st = QString(s)
            ts = QTextStream(st, IO_ReadOnly)
            ts >> self

        # panels always start closed
        self.bpanel.setFixedExtentHeight(0)
        self.rpanel.setFixedExtentWidth(0)

    def on_btn3(self, on, height=[None]):
        if on:
            self.rpanel.stack.show()
            if height[0] is not None:
                self.rpanel.setFixedExtentWidth(height[0])
            self.rpanel.stack.raiseWidget(self.Style)
        else:
            self.rpanel.stack.hide()
            height[0] = self.rpanel.width()
            self.rpanel.setFixedExtentWidth(0)


    def on_btn2(self, on, height=[None]):
        if on:
            self.rpanel.stack.show()
            if height[0] is not None:
                self.rpanel.setFixedExtentWidth(height[0])
            self.rpanel.stack.raiseWidget(self.Data)
        else:
            self.rpanel.stack.hide()
            height[0] = self.rpanel.width()
            self.rpanel.setFixedExtentWidth(0)


    def on_btn1(self, on, height=[None]):
        if on:
            self.stack.show()
            if height[0] is not None:
                self.bpanel.setFixedExtentHeight(height[0])
        else:
            self.stack.hide()
            height[0] = self.bpanel.height()
            self.bpanel.setFixedExtentHeight(0)

    def RunScript(self):
        qfd = QFileDialog (project.mainwin)
        qfd.setMode (QFileDialog.AnyFile)
        if qfd.exec_loop() != 1:
            return False
        file = str(qfd.selectedFile())
        project.mainwin.script.fakeUser(['execfile("%s")' % file])

    def Preferences(self):
        dlg = preferences_dialog()
        dlg.exec_loop()

    def MoveColumnLeft(self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            sel = aw.worksheet.selected_columns()
            aw.worksheet._view._table.clearSelection()
            for col in sel:
                aw.worksheet.move_column(col, col-1)
                aw.worksheet._view._table.selectColumn(col-1)

    def MoveColumnRight(self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            sel = aw.worksheet.selected_columns()
            aw.worksheet._view._table.clearSelection()
            for col in sel:
                aw.worksheet.move_column(col, col+1)
                aw.worksheet._view._table.selectColumn(col+1)


    def insert_menu_item(self, location, callback):
        path = location.split('/')
        menu = self.menus[path[0]]

        if len(path) == 2:
            menu.insertItem(path[1], callback)
        elif len(path) == 3:
#            ids = [menu.idAt(pos) for pos in range(menu.count())]
#            names = [menu.text(id) for id in ids]
            if not hasattr(menu, 'popups'):
                menu.popups = {}
            if path[1] not in menu.popups:
                menu.popups[path[1]] = QPopupMenu()
                menu.insertItem(path[1], menu.popups[path[1]])
            menu.popups[path[1]].insertItem(path[2], callback)

    def remove_menu_item(self, location):
        path = location.split('/')
        menu = self.menus[path[0]]

        if len(path) == 2:
            ids = [menu.idAt(pos) for pos in range(menu.count())]
            names = [menu.text(id) for id in ids]
            menu.removeItem(ids[names.index(path[1])])
        elif len(path) == 3:
            submenu = menu.popups[path[1]]
            ids = [submenu.idAt(pos) for pos in range(submenu.count())]
            names = [submenu.text(id) for id in ids]
            submenu.removeItem(ids[names.index(path[2])])
            if submenu.count() == 0:
                self.remove_menu_item('/'.join(path[:2]))
        
    def fileMenuAboutToShow(self):
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

    def action_from_tuple (self, a):
        act = QAction (self, None, a[4])
        act.setText (a[0])
        act.setMenuText (a[1])
        if isinstance(a[2], QPixmap):
            act.setIconSet (QIconSet(a[2]))
        elif a[2] is not None:
            act.setIconSet (QIconSet(QPixmap(project.datadir + "pixmaps/" + a[2])))
        if a[5]: act.setAccel (QKeySequence (a[5]))
        if inspect.isclass(a[3]):
            callback = self.make_callback(a[3])
        else:
            callback = a[3]
        if callback is not None:    
            if a[4]: 
                self.connect (act, SIGNAL("toggled(bool)"), callback)
            else: 
                self.connect (act, SIGNAL("activated()"), callback)
        return act

 
    def on_window_activated(self, window):
        self.active = window
        toolbars = { WorksheetView : 'Worksheet',
                          GraphView : 'Graph', }
        [self.toolbars[i].hide() for i in toolbars.itervalues()]
        self.rpanel.hide()
        if window is None or not window.isVisible() or window.__class__ not in toolbars:
            return

        self.toolbars[toolbars[window.__class__]].show()

        if isinstance(window, GraphView):
            self.rpanel.show()
            self.rpanel.Style.open()
            self.rpanel.Data.open()
            self.rpanel.Axes.open()
        elif isinstance(window, WorksheetView):
            pass

    def on_add_column(self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            aw.worksheet.add_column()
 
    def on_remove_column(self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            ws = aw.worksheet
            for nam in [ws.column_names[ind] for ind in ws.selected_columns()]:
                del ws[nam]
    
   
    def make_callback(self, command_class):
        def callback():
            command = command_class()
            if hasattr(command_class, 'undo'):
                project.undolist.append(command)
            command.do()
        setattr(self, command_class.__name__ + '_callback', callback)
        return callback

    def cut (self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            self.clipboard = aw.cut_selected()

    def copy (self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            self.clipboard = aw.copy_selected()

    def paste (self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            aw.paste_selected(self.clipboard)

    def clear (self):
        aw = self.workspace.activeWindow()
        if isinstance(aw, WorksheetView):
            aw.clear_selected()

    def delete (self):
        pass

    def history_select(self, item):
        pos = self.history.index(item)
        id = len(project.undolist) - pos - 1
        curr = project.undolist[id]

        if hasattr(curr, 'undone') and curr.undone:
            for com in project.undolist:
                if hasattr(com, 'undone') and com.undone:
                    break
            last = project.undolist.index(com)

            for com in project.undolist[last:id+1]:
                self.do_redo(com)
        else:
            for com in project.undolist[::-1]:
                if not hasattr(com, 'undone') or not com.undone:
                    break
            last = project.undolist.index(com)

            for com in project.undolist[last:id:-1]:
                self.do_undo(com)
        self.history.setCurrentItem(pos)
        
    def do_undo(self, com):
        id = len(project.undolist) - project.undolist.index(com) - 1
        self.history.changeItem(QPixmap(project.datadir + 'pixmaps/undo.png'), self.history.text(id), id)
        project.lock_undo()
        try:
            com.undo()
        finally:
            project.unlock_undo()
        com.undone = True

    def do_redo(self, com):
        id = len(project.undolist) - project.undolist.index(com) - 1
        if hasattr(com, 'pixmap') and com.pixmap is not None:
            self.history.changeItem(com.pixmap, self.history.text(id), id)
        else:
            self.history.changeItem(self.history.text(id), id)
        project.lock_undo()
        try:
            com.do()
        finally:
            project.unlock_undo()
        com.undone = False
        
    def undo (self): 
        for com in project.undolist[::-1]:
            if not hasattr(com, 'undone') or not com.undone:
                break
        if com and (not hasattr(com, 'undone') or not com.undone):
            self.do_undo(com)
        else:
            self.statusBar().message ("No more commands to undo", 1000)
        
    def redo (self):
        for com in project.undolist:
            if hasattr(com, 'undone') and com.undone:
                break
        if com and (hasattr(com, 'undone') and com.undone):
            self.do_redo(com)
        else:
            self.statusBar().message ("No more commands to redo", 1000)


    def view_history (self, show):
        if show: self.history.show ()
        else: self.history.hide ()

#    def view_notes (self, show):
#        if show: self.notes.show ()
#        else: self.notes.hide ()

    def graph_mode (self, on): 
        modes = [ 'g_arrow', 'g_zoom', 'g_range', 'g_dreader', 'g_sreader', 'g_hand' ]
        ons = [self.actions[m].isOn() for m in modes]
        if ons.count (True) != 1: return
        Graph.graph_mode = ons.index (True)
        for g in project.graphs: g.set_mode ()

    def observe_project (self, obj, **arg):
        signal =  arg['msg']
        if signal == 'add_worksheet':
            if arg['wsheet']._view is None:
                arg['wsheet']._view = WorksheetView (arg['wsheet'])
            self.explorer.add (arg['wsheet'])
        elif signal == 'add_graph':
            self.explorer.add (arg['graph'])
        elif signal == 'remove_worksheet':
            self.explorer.remove (arg['wsheet'])
            arg['wsheet']._view.close()
            arg['wsheet'].vogel()
        elif signal == 'remove_graph':
            self.explorer.remove (arg['graph'])
            arg['graph'].vogel()

    def importAscii(self):
        self.qfd = QFileDialog (self)
        self.qfd.setMode (QFileDialog.ExistingFiles)
        if self.qfd.exec_loop() == 1:
            for f in self.qfd.selectedFiles():
                w = project.new_worksheet(os.path.splitext(os.path.split(str(f))[1])[0], [])
                w.import_ascii (str(f))

    def save_if_changed (self):
        if not project.modified:
             return True
        flag = QMessageBox.information (self, "Grafit", "<b>Do you want to save the changes you made to the document?</b><p>Your changes will be lost if you don't save them", "&Save",  "&Cancel", "&Don't Save", 0, 1)
        if flag == 0:
            return self.save_project_do()
        elif flag == 1:
            return False
        elif flag == 2: 
            return True

    def closeEvent (self, event):
        self.exit()

    def exit (self):
        project.settings['/grafit/recent_projects'] = ' '.join(self.recent)
        
        s = QString()
        st = QTextStream(s, IO_WriteOnly)
        st << self
        s = str(s)
        project.settings['/grafit/windows/toolbars'] = s
        project.settings['/grafit/console/history'] = '\n'.join(self.script.history[-20:])
        
        if not self.save_if_changed ():
            return
        project.settings.settings.sync()
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


    def open_project_do(self):
        if not project.mainwin.save_if_changed ():
            return
        qfd = QFileDialog (project.mainwin)
        if qfd.exec_loop() != 1:
            return
        project.load (str(qfd.selectedFile()))

    def save_project_do(self): 
        if project.filename is None:
            qfd = QFileDialog (project.mainwin)
            qfd.setMode (QFileDialog.AnyFile)
            if qfd.exec_loop() != 1:
                return False
            project.filename = str(qfd.selectedFile())
        return project.save (project.filename)

    def save_project_as_do(self): 
        qfd = QFileDialog (project.mainwin)
        qfd.setMode (QFileDialog.AnyFile)
        if qfd.exec_loop() != 1:
            return False
        return project.save (str(qfd.selectedFile()))

    def new_project_do(self): 
        if not project.mainwin.save_if_changed ():
            return
        project.clear ()

    def duplicate_do(self):
        aw = project.mainwin.workspace.activeWindow()
        if aw.__class__.__name__ == 'WorksheetView':
           obj = aw.worksheet
        elif aw.__class__.__name__ == 'Graph':
           obj = aw
        else:
           return
        
        elem = obj.to_element()
        new = obj.__class__()
        new.from_element(elem)
        new.name = 'another_' + obj.name
        project.add(new)
        self.obj = new
