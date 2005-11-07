from signals import HasSignals
import wx
from base import Widget
 
class TreeNode(HasSignals):
    def __init__(self):
        self.children = []

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
            items = self.tree.items + self.tree.roots
            item = items[[i._nodeid for i in items].index(item)]
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
            items = self.tree.items + self.tree.roots
            item = items[[i._nodeid for i in items].index(item)]
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
            items = self.tree.items + self.tree.roots
            item = items[[i._nodeid for i in items].index(item)]
        except ValueError:
            return

        result = self.tree.emit('dropped', item, data)


class Tree(Widget, _xTreeCtrl):

    def __init__(self, place, **kwds):
        _xTreeCtrl.__init__(self, self, place[0])
        Widget.__init__(self, place, **kwds)
        self.roots = []
        self.items = []

        self.SetIndent(10)

        self.imagelist = wx.ImageList(16, 16)
        self.SetImageList(self.imagelist)
        self.pixmaps = {}

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_sel_changed)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.on_label_edit)

        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.on_expand)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.on_collapse)

        self.tree = self
        self.selection = None

    def on_sel_changed(self, evt):
        from itertools import chain
        for item in chain(self.items, self.roots):
            if self.IsSelected(item._nodeid):
                self.emit('selected', item)
                self.selection = item
                return
        self.selection = None

    def on_label_edit(self, evt):
        item = self.id_to_item(evt.GetItem())
        label = evt.GetLabel()
        if hasattr(item, 'rename') and label != '' and item.rename(label):
            evt.Veto()

    def on_expand(self, evt):
        item = self.id_to_item(evt.GetItem())
        if hasattr(item, 'open'):
            item.open()

    def on_collapse(self, evt):
        item = self.id_to_item(evt.GetItem())
        if hasattr(item, 'close'):
            item.close()

    def id_to_item(self, id):
        items = self.items + self.roots
        return items[[i._nodeid for i in items].index(id)]

    def getpixmap(self, filename):
        if filename is None:
            return None
        if filename not in self.pixmaps:
            self.pixmaps[filename] = self.imagelist.Add(wx.Image(DATADIR+'data/images/'+filename).ConvertToBitmap())
        return self.pixmaps[filename]

    def append(self, node):
        self.roots.append(node)
        node.connect('modified', self.on_node_modified)
        self.on_node_modified()

    def remove(self, node):
        self.roots.remove(node)
        node.disconnect('modified', self.on_node_modified)
        self.on_node_modified()

    def _add_node_and_children(self, parent, node):
        node._nodeid = self.AppendItem(parent._nodeid, str(node))#, self.getpixmap(node.get_pixmap()))
        self.items.append(node)
        for child in node:
            self._add_node_and_children(node, child)
        self.Expand(node._nodeid)

    def on_node_modified(self):
        self.DeleteAllItems()
        self.items = []
        for root in self.roots:
            root._nodeid = self.AddRoot(str(root))#, self.getpixmap(root.get_pixmap()))
            for node in root:
                self._add_node_and_children(root, node)
            self.Expand(root._nodeid)
        if self.selection is not None:
            self.SelectItem(self.selection._nodeid)


    def clear(self):
        self.DeleteAllItems()
        self.roots = []
        self.items = []

    def enable_drop(self, formats):
        self.can_drop = True
        self.formats = formats
        target = _xDropTarget(self)
        self.composite = create_wx_data_object(self.formats)
        target.SetDataObject(self.composite)
        self.SetDropTarget(target)
        target.formats = formats
