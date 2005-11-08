import sys
from itertools import chain

import wx

from signals import HasSignals
from base import Widget
 
class TreeNode(HasSignals):
    def __init__(self, parent=None):
        self.children = []
        if parent is not None:
            parent.append(self)

    def __iter__(self):
        return iter(self.children)
    
    def __str__(self):
        return 'TreeNode'

    def get_pixmap(self):
        return None

    def append(self, child):
        self.children.append(child)
        child.connect('modified', self.on_child_modified)
        self.emit('modified')

    def on_child_modified(self):
        self.emit('modified')

class _xTreeCtrl(wx.TreeCtrl):
    def __init__(self, tree, parent):
        wx.TreeCtrl.__init__(self, parent, -1, style=wx.TR_DEFAULT_STYLE|wx.TR_EDIT_LABELS|wx.SUNKEN_BORDER)
        self.tree = tree

    def OnHover(self, x, y):
        """
        Override this to perform an action when a drag action is
        hovering over the widget.
        """
        item, flags = self.HitTest(wx.Point(x, y))
#        if not (flags & wx.TREE_HITTEST_ONITEM):
#            item = -1
        try:
            item = self.tree.items.key(item)
        except ValueError:
            return wx.DragNone

        result = self.tree.emit('drop-hover', item)
        if 'move' in result:
            return wx.DragMove
        elif 'copy' in result:
            return wx.DragCopy
        else:
            return wx.DragNone

    def OnRequestDrop(self, x, y):
        item, flags = self.HitTest(wx.Point(x, y))
#        if not (flags & wx.LIST_HITTEST_ONITEM):
#            item = -1
        try:
            item = self.tree.items.key(item)
        except ValueError:
            return False

        result = self.tree.emit('drop-ask', item)
        if True in result:
            return True
        else:
            return False

    def AddItem(self, x, y, data):
        item, flags = self.HitTest(wx.Point(x, y))

        try:
            item = self.tree.items.key(item)
        except ValueError:
            return

        result = self.tree.emit('dropped', item, data)


class TreeData(HasSignals):
    def root(self):
        """Returns the object represented by the root node"""

    def children(self, obj):
        """Returns the children of object `obj`"""

    def text(self, obj):
        """Returns the string representation of object `obj` in the tree"""

    def image(self, obj):
        """Returns the image of object `obj` in the tree"""

    # signal 'modified' (obj)
    #   signals that the object `obj` has been modified and the 
    #   tree branch should be updated. If obj is None the whole
    #   tree should be updated.

from thirdparty.two_way_dict import TwoWayDict

class Tree(Widget, _xTreeCtrl):
    def __init__(self, place, data=None, **kwds):
        _xTreeCtrl.__init__(self, self, place[0])
        Widget.__init__(self, place,  **kwds)

        self.data = data
        
        self.root = None
        self.items = TwoWayDict()
        self.selection = None

        self.SetIndent(10)

        self.imagelist = wx.ImageList(16, 16)
        self.SetImageList(self.imagelist)
        self.pixmaps = {}

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_sel_changed)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.on_label_edit)

#        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.on_expand)
#        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.on_collapse)

        self._skip_event = False


    def on_sel_changed(self, evt):
        if self._skip_event:
            return
        for id in self.items:
            if self.IsSelected(id):
                self.emit('selected', self.items[id])
                self.selection = self.items[id]
                return
        self.selection = None

    def select(self, item, skip_event=False):
        self._skip_event = skip_event
        self.SelectItem(self.items.key(item))
        self._skip_event = False

    def on_label_edit(self, evt):
        item = self.items[evt.GetItem()]
        label = evt.GetLabel()
        if hasattr(self.data, 'rename') and label != '' and self.data.rename(item, label):
            evt.Veto()

    def getpixmap(self, filename):
        if filename is None:
            return None
        if filename not in self.pixmaps:
            self.pixmaps[filename] = self.imagelist.Add(wx.Image(DATADIR+'data/images/'+filename).ConvertToBitmap())
        return self.pixmaps[filename]

    def on_data_modified(self, obj):
        self.clear()
        self.set_data(self.data)
        if self.selection is not None:
            self.SelectItem(self.items.key(self.selection))

    def set_data(self, data):
        self.data = data
        self.data.connect('modified', self.on_data_modified)

        self.root = self.data.root()
        nodeid = self.AddRoot(self.data.text(self.root))
        self.items[nodeid] = self.root

        for child in self.data.children(self.root):
            self._add_node_and_children(self.root, child)

        self.Expand(nodeid)

    def _add_node_and_children(self, parent, node):
        nodeid = self.AppendItem(self.items.key(parent), self.data.text(node))
        self.items[nodeid] = node

        for child in self.data.children(node):
            self._add_node_and_children(node, child)

        self.Expand(nodeid)

    def clear(self):
        self.root = None
        self.data.disconnect('modified', self.on_data_modified)
        self.items.clear()
        self.DeleteAllItems()

    def enable_drop(self, formats):
        self.can_drop = True
        self.formats = formats
        target = _xDropTarget(self)
        self.composite = create_wx_data_object(self.formats)
        target.SetDataObject(self.composite)
        self.SetDropTarget(target)
        target.formats = formats
