import gtk
import gtk.glade
from gtk.gtkgl.apputils import GLScene, GLArea
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


class Scene(GLScene):
    def __init__(self, graph):
        self.graph = graph
        GLScene.__init__(self, gtk.gdkgl.MODE_RGB|gtk.gdkgl.MODE_DEPTH|gtk.gdkgl.MODE_DOUBLE)
    def init(self): return self.graph.init()
    def reshape(self, w, h): return self.graph.reshape(w, h)
    def display(self, w, h): return self.graph.display(w, h)


class GraphView(object):
    def __init__(self, graph):
        self.graph = graph
        self.widgets = gtk.glade.XML("pixmaps/grafity.glade", 'graph_view')
        self.label = gtk.glade.XML("pixmaps/grafity.glade", 'graph_view_label').get_widget('graph_view_label')

        scene = Scene(self.graph)
        area = GLArea(scene)
        area.set_size_request(300, 300)
        area.show()
        self.box.pack_start(area, True, True, 0)

    def init_ui(self):
        make_panel(self.right_panel, self.graph_view, 'right')

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return self.widgets.get_widget(attr)

def folder_list_store(folder):
    store = gtk.ListStore(str)
 
    def on_add_item(item):
        if item.parent == folder:
            item._store_item = store.append([item.name])

    def on_remove_item(item):
        if item.parent == folder:
            store.remove(item._store_item)
            
    store._on_list_add_item = on_add_item
    store._on_list_remove_item = on_remove_item
        
    for item in folder:
        item._store_item = store.append([item.name])

    folder.project.connect('add-item', on_add_item)
    folder.project.connect('remove-item', on_remove_item)
    return store

def project_tree_store(project):
    store = gtk.TreeStore(str)

    def t_on_add_item(item):
        if isinstance(item, grafity.Folder):
            item._tree_store_item = store.append(item.parent._tree_store_item, [item.name])

    def t_on_remove_item(item):
        if isinstance(item, grafity.Folder):
            store.remove(item._tree_store_item)

    store._on_tree_add_item = t_on_add_item
    store._on_tree_remove_item = t_on_remove_item

    project.top._tree_store_item = store.append(None, [project.top.name])
    for folder in project.top.all_subfolders():
        folder._tree_store_item = store.append(folder.parent._tree_store_item, [folder.name])

    project.connect('add-item', t_on_add_item, True)
    project.connect('remove-item', t_on_remove_item, True)

    return store

class Widgets(object):
    def __init__(self):
        self.widgets = gtk.glade.XML("pixmaps/grafity.glade", 'mainwin')
        signals = { "on_quit1_activate" : self.on_quit1_activate}
        self.widgets.signal_autoconnect(signals)

        self.project = grafity.Project('test/pdms.gt')

        self.project._tree_model = project_tree_store(self.project)
        self.folder_tree.set_model(self.project._tree_model)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("tuples", cell, text=0)
        self.folder_tree.append_column(column)

        model = folder_list_store(self.project.top)

        self.object_list.set_model(model)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("name", cell, text=0)
        self.object_list.append_column(column)


        sheet = Sheet(self.project.top.pdms1.pdms1_e2_f)
        console = Console(banner="Hello there!",
                          locals={"project":self.project},
                          use_rlcompleter=True,
                          start_script="import grafity\n")
        console.show()
        self.console_box.add(console)

        make_panel(self.left_panel, self.left_paned, 'left')
        make_panel(self.bottom_panel, self.bottom_paned, 'bottom')

        g = GraphView(self.project.top.graph0)
        self.notebook.append_page(g.graph_view, g.label)
        g.init_ui()

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return self.widgets.get_widget(attr)
        
    def on_quit1_activate(self, widget):
        gtk.main_quit()
        
if __name__ == "__main__":
    widgets = Widgets()
    gtk.main()
