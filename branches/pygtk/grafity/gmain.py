import gtk
import gtk.glade
from gtk.gtkgl.apputils import GLScene, GLArea, GLSceneButton, GLSceneButtonMotion
import gobject
import numarray

import sys
sys.path.append('..')
import grafity

from sheet import Sheet
from pyconsole import Console

import logging
logging.basicConfig(format="%(asctime)s [%(name)s] %(message)s")

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-l', '--log', dest='log', help='Log program events')
options, args = parser.parse_args()

if options.log is not None:
    for l in options.log.split(','):
        logging.getLogger(l).setLevel(logging.DEBUG)

class Widgets(object):
    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return self.widgets.get_widget(attr)
 
def make_panel(notebook, paned_widget, side):
    def on_switch_page(widget, _, pagenum, paned):
        if pagenum == 0:
            if side in ['left', 'right']:
                coord = 2
            elif side in ['top', 'bottom']:
                coord = 3
            pos = widget.get_allocation()[coord]-widget.get_nth_page(0).get_allocation()[coord]
            if pos == 0:
                pos = 34
            if side in ['right', 'bottom']:
                paned.set_position(paned.get_property("max-position")-pos)
            elif side in ['top', 'left']:
                paned.set_position(pos)
        else:
            if side in ['right', 'bottom']:
                paned.set_position(paned.get_property("max-position")-200)
            elif side in ['top', 'left']:
                paned.set_position(200)

    notebook.connect("switch_page", on_switch_page, paned_widget)
    on_switch_page(notebook, None, 0, paned_widget)


class Scene(GLScene, GLSceneButton, GLSceneButtonMotion):
    def __init__(self, graph):
        self.graph = graph
        self.graph.mode = 'zoom'
        GLScene.__init__(self, gtk.gdkgl.MODE_RGB|gtk.gdkgl.MODE_DEPTH|gtk.gdkgl.MODE_DOUBLE)
#        self.btns = {gtk.gdk.LEFTBUTTON:1, gtk.gdk.RIGHTBUTTON:3, gtk.gdk.MIDDLEBUTTON:2 }
    def init(self): return self.graph.init()
    def reshape(self, w, h): return self.graph.reshape(w, h)
    def display(self, w, h): return self.graph.display(w, h)

    def button_press(self, w, h, event): 
        self.graph.button_press(event.x, event.y, event.button)
    def button_release(self, w, h, event): 
        self.graph.button_release(event.x, event.y, event.button)
    def button_motion(self, w, h, event): 
        self.graph.button_motion(event.x, event.y, True)


class GraphView(Widgets):
    def __init__(self, graph):
        self.graph = graph
        self.widgets = gtk.glade.XML("pixmaps/grafity.glade", 'graph_view')
        self.label = gtk.glade.XML("pixmaps/grafity.glade", 'graph_view_label').get_widget('graph_view_label')
        self.page = self.graph_view

        scene = Scene(self.graph)
        self.area = area = GLArea(scene)
        area.set_size_request(300, 300)
        area.show()
        self.box.pack_start(area)
        make_panel(self.right_panel, self.graph_view, 'right')

        self.graph.connect('redraw', self.on_redraw, True)

    def on_redraw(self):
        self.area.queue_draw()


class WorksheetView(Widgets):
    def __init__(self, worksheet):
        self.worksheet = worksheet
        self.widgets = gtk.glade.XML("pixmaps/grafity.glade", 'worksheet_view')
        self.label = gtk.glade.XML("pixmaps/grafity.glade", 'worksheet_view_label').get_widget('worksheet_view_label')
        self.page = self.worksheet_view

        sheet = Sheet(self.worksheet)
        self.sheet_box.pack_start(sheet)


def folder_list_store(folder):
    store = gtk.ListStore(object)
 
    def on_add_item(item):
        if item.parent == folder:
            item._store_item = store.append([item])

    def on_remove_item(item):
        if item.parent == folder:
            store.remove(item._store_item)
            
    store._on_list_add_item = on_add_item
    store._on_list_remove_item = on_remove_item
        
    for item in folder:
        item._store_item = store.append([item])

    folder.project.connect('add-item', on_add_item)
    folder.project.connect('remove-item', on_remove_item)
    return store

def project_tree_store(project):
    store = gtk.TreeStore(object)

    def t_on_add_item(item):
        if isinstance(item, grafity.Folder):
            item._tree_store_item = store.append(item.parent._tree_store_item, [item])

    def t_on_remove_item(item):
        if isinstance(item, grafity.Folder):
            store.remove(item._tree_store_item)

    store._on_tree_add_item = t_on_add_item
    store._on_tree_remove_item = t_on_remove_item

    project.top._tree_store_item = store.append(None, [project.top])
    for folder in project.top.all_subfolders():
        folder._tree_store_item = store.append(folder.parent._tree_store_item, [folder])

    project.connect('add-item', t_on_add_item, True)
    project.connect('remove-item', t_on_remove_item, True)

    return store


class Main(Widgets):
    def __init__(self):
        self.widgets = gtk.glade.XML("pixmaps/grafity.glade", 'mainwin')
        signals = { "on_quit" : self.on_quit,
                    "on_file_open" : self.on_file_open,
                    "on_object_activated" : self.on_object_activated }
        class getter(object):
            def __getattr__(s, attr):
                return getattr(self, attr)
        signals = getter()
        self.widgets.signal_autoconnect(signals)
        print hasattr(self, 'on_file_open')

        graphicon = gtk.gdk.pixbuf_new_from_file('/home/daniel/grafity/data/images/16/graph.png')
        foldericon = gtk.gdk.pixbuf_new_from_file('/home/daniel/grafity/data/images/16/folder.png')
        worksheeticon = gtk.gdk.pixbuf_new_from_file('/home/daniel/grafity/data/images/16/worksheet.png')

        def obj_id_str(treeviewcolumn, cell_renderer, model, iter):
            obj = model.get_value(iter, 0)
            cell_renderer.set_property('text', obj.name)

        def obj_id_icon(treeviewcolumn, cell_renderer, model, iter):
            obj = model.get_value(iter, 0)
            icon = {grafity.Graph: graphicon,
                    grafity.Worksheet: worksheeticon,
                    grafity.Folder: foldericon } [type(obj)]
            cell_renderer.set_property('pixbuf', icon)

        # tree columns
        cell = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn("icon", cell)
        column.set_cell_data_func(cell, obj_id_icon)
        self.folder_tree.append_column(column)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("name", cell)
        column.set_cell_data_func(cell, obj_id_str)
        self.folder_tree.append_column(column)

        # list columns
        cell = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn("icon", cell)
        column.set_cell_data_func(cell, obj_id_icon)
        self.object_list.append_column(column)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("name", cell)
        column.set_cell_data_func(cell, obj_id_str)
        self.object_list.append_column(column)

#        self.object_list.connect('row-activated', self.on_object_activated)
        self.folder_tree.get_selection().connect('changed', self.on_tree_select)

        self.console = Console( #                          locals={"project":self.project},
                          use_rlcompleter=True,
                          start_script="from grafity import Folder, Worksheet, Graph\n")
        self.console_box.add(self.console)
        self.console.show()

        make_panel(self.left_panel, self.left_paned, 'left')
        make_panel(self.bottom_panel, self.bottom_paned, 'bottom')

        self.open_project(grafity.Project('test/pdms.gt'))

        self.left_panel.set_current_page(1)

    def on_tree_select(self, selection):
        model, paths = selection.get_selected_rows()
        self.project.cd(self.folder_tree.get_model()[paths[0]][0])

    def open_project(self, project):
        self.project = project

        # tree
        self.project._tree_model = project_tree_store(self.project)
        self.folder_tree.set_model(self.project._tree_model)

        # folders
        for folder in self.project.top.all_subfolders():
            folder._list_model = folder_list_store(folder)
        self.project.top._list_model = folder_list_store(self.project.top)

        self.project.connect('change-current-folder', self.on_change_folder)
        self.console.locals['project'] = self.project

    def close_project(self):
        def respond(widget, resp):
            print resp
        msg = gtk.MessageDialog(parent=self.mainwin, flags=gtk.DIALOG_MODAL, 
                                type=gtk.MESSAGE_QUESTION, 
                                buttons=gtk.BUTTONS_YES_NO, 
                                message_format='foo')
        msg.connect('response', respond)
        msg.show()
        
        return
        self.project.disconnect('change-current-folder', self.on_change_folder)
        self.folder_tree.set_model(None)
        self.object_list.set_model(None)
        # and close all pages
        self.project = None

    def on_file_open(self, pikou):
        filesel = gtk.FileSelection(title="Open Project")

        def on_ok(widget):
            print filesel.get_filename()
            self.close_project()
            self.open_project(grafity.Project(filesel.get_filename()))
            filesel.destroy()

        filesel.ok_button.connect("clicked", on_ok)
        filesel.cancel_button.connect("clicked", lambda w: filesel.destroy())
        filesel.show()

    def on_change_folder(self, folder):
        self.object_list.set_model(folder._list_model)

    def on_object_activated(self, treeview, path, view_column):
        self.view(treeview.get_model()[path][0])

    def view(self, obj):
        if isinstance(obj, grafity.Graph):
            view = GraphView(obj)
            self.notebook.append_page(view.page, view.label)
        elif isinstance(obj, grafity.Worksheet):
            view = WorksheetView(obj)
            self.notebook.append_page(view.page, view.label)

       
    def on_quit(self, widget):
        gtk.main_quit()
        
if __name__ == "__main__":
    widgets = Main()
    gtk.main()
