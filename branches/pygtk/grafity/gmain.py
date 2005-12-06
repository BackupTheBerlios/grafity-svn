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

class FolderModel(gtk.GenericTreeModel):
    def __init__(self, folder):
        self.folder = folder
        gtk.GenericTreeModel.__init__(self)

    def on_get_flags(self): return gtk.TREE_MODEL_LIST_ONLY | gtk.TREE_MODEL_ITERS_PERSIST
    def on_get_n_columns(self): return 1
    def on_get_column_type(self, index): return gobject.TYPE_STRING

    def on_get_path(self, node):
        return (list(self.folder).index(node),)

    def on_get_iter(self, path):
        '''returns the node corresponding to the given path.'''
        return self.folder[path[0]]

    def on_get_value(self, node, column):
        '''returns the value stored in a particular column for the node'''
        assert column == 0
        return node.name

    def on_iter_next(self, node):
        '''returns the next node at this level of the tree'''
        l = list(self.folder)
        try:
            return l[l.index(node)+1]
        except IndexError:
            return None

    def on_iter_children(self, node): return None
    def on_iter_has_child(self, node): return False
    def on_iter_n_children(self, node): return 0
    def on_iter_nth_child(self, node, n):
        if node is None:
            return list(self.folder)[n]
    def on_iter_parent(self, node): return None



# to create a new GtkTreeModel from python, you must derive from
# TreeModel.
class MyTreeModel(gtk.GenericTreeModel):
    '''This class represents the model of a tree.  The iterators used
    to represent positions are converted to python objects when passed
    to the on_* methods.  This means you can use any python object to
    represent a node in the tree.  The None object represents a NULL
    iterator.

    In this tree, we use simple tuples to represent nodes, which also
    happen to be the tree paths for those nodes.  This model is a tree
    of depth 3 with 5 nodes at each level of the tree.  The values in
    the tree are just the string representations of the nodes.'''

    TREE_DEPTH = 4
    TREE_SIBLINGS = 5
    def __init__(self):
        '''constructor for the model.  Make sure you call
        PyTreeModel.__init__'''
        gtk.GenericTreeModel.__init__(self)

    # the implementations for TreeModel methods are prefixed with on_
    def on_get_flags(self):
        '''returns the GtkTreeModelFlags for this particular type of model'''
        return 0
    def on_get_n_columns(self):
        '''returns the number of columns in the model'''
        return 1
    def on_get_column_type(self, index):
        '''returns the type of a column in the model'''
        return gobject.TYPE_STRING
    def on_get_path(self, node):
        '''returns the tree path(a tuple of indices at the various
        levels) for a particular node.'''
        return node
    def on_get_iter(self, path):
        '''returns the node corresponding to the given path.  In our
        case, the node is the path'''
        return path
    def on_get_value(self, node, column):
        '''returns the value stored in a particular column for the node'''
        assert column == 0
        return `node`
    def on_iter_next(self, node):
        '''returns the next node at this level of the tree'''
        if node[-1] == self.TREE_SIBLINGS - 1: # last node at level
            return None
        return node[:-1] +(node[-1]+1,)
    def on_iter_children(self, node):
        '''returns the first child of this node'''
        if node == None: # top of tree
            return(0,)
        if len(node) >= self.TREE_DEPTH: # no more levels
            return None
        return node +(0,)
    def on_iter_has_child(self, node):
        '''returns true if this node has children'''
        return len(node) < self.TREE_DEPTH
    def on_iter_n_children(self, node):
        '''returns the number of children of this node'''
        if len(node) < self.TREE_DEPTH:
            return self.TREE_SIBLINGS
        else:
            return 0
    def on_iter_nth_child(self, node, n):
        '''returns the nth child of this node'''
        if node == None:
            return(n,)
        if len(node) < self.TREE_DEPTH and n < self.TREE_SIBLINGS:
            return node +(n,)
        else:
            return None
    def on_iter_parent(self, node):
        '''returns the parent of this node'''
        if len(node) == 0:
            return None
        else:
            return node[:-1]


class Scene(GLScene):
    def __init__(self, graph):
        self.graph = graph
        GLScene.__init__(self,
                         gtk.gdkgl.MODE_RGB   |
                         gtk.gdkgl.MODE_DEPTH |
                         gtk.gdkgl.MODE_DOUBLE)
    def init(self):
        return self.graph.init()
    def reshape(self, w, h):
        return self.graph.reshape(w, h)
    def display(self, w, h):
        return self.graph.display(w, h)

class Widgets(object):
    def __init__(self):
        self.widgets = gtk.glade.XML("grafity.glade")
        signals = { "on_quit1_activate" : self.on_quit1_activate}
        self.widgets.signal_autoconnect(signals)

        self.folder_tree = self.widgets.get_widget('folder_tree')
        model = MyTreeModel()
        self.folder_tree.set_model(model)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("tuples", cell, text=0)
        self.folder_tree.append_column(column)

        self.object_list = self.widgets.get_widget('object_list')

        self.project = grafity.Project('test/pdms.gt')
        model = FolderModel(self.project.top)

        self.object_list.set_model(model)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("name", cell, text=0)
        self.object_list.append_column(column)

        p = grafity.Project()
        w = p.new(grafity.Worksheet, 'test')
        w.a = numarray.arange(1000)
        w.b = [2,4,5, 5.5]
        w.c = [3,2,1,3.3]
        w.d = 2*w.a
        w.e = w.b * w.c

        g = p.new(grafity.Graph, 'arse')

        sheet = Sheet(w)
#        self.box.pack_start(sheet, True, True, 0)
        graph = Scene(g)
        area = GLArea(graph)
        area.set_size_request(300, 300)
        area.show()
        self.box.pack_start(area, True, True, 0)

        console = Console(banner="Hello there!",
                          use_rlcompleter=True,
                          start_script="import grafity\n")
        console.show()
        self.console_box.add(console)

        self.left_panel.connect("switch_page", self.on_switch_page, self.left_paned)
        self.right_panel.connect("switch_page", self.on_switch_page, self.right_paned)
        self.bottom_panel.connect("switch_page", self.on_switch_page, self.bottom_paned)
        self.right_paned.set_position(300)


    def on_switch_page(self, widget, _, pagenum, paned):
        if pagenum == 0:
            if widget in [self.left_panel, self.right_panel]:
                coord = 2
            elif widget == self.bottom_panel:
                coord = 3
            pos = widget.get_allocation()[coord]-widget.get_nth_page(0).get_allocation()[coord]
            if widget in [self.right_panel, self.bottom_panel]:
                paned.set_position(paned.get_property("max-position")-pos)
            elif widget == self.left_panel:
                paned.set_position(pos)
        else:
            if widget in [self.right_panel, self.bottom_panel]:
                paned.set_position(paned.get_property("max-position")-200)
            elif widget == self.left_panel:
                paned.set_position(200)
        print widget, pagenum, paned

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
