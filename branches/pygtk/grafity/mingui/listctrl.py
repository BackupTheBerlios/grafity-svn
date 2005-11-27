import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, ListCtrlSelectionManagerMix
from images import images
import Image

from signals import HasSignals

from base import Widget, _pil_to_wxbitmap

class ListData(HasSignals):
    def __init__(self):
        self.items = []
        
    # list data interface
    def get(self, row, column):
        r = self.items[row]
        try:
            return str(r[column])
        except (IndexError, TypeError):
            return str(r)

    def get_image(self, row):
        return None

    def __len__(self):
        return len(self.items)

    # behave as a sequence
    def append(self, item):
        self.items.append(item)
        self.emit('modified')

    def __setitem__(self, key, value):
        self.items[key] = value
        self.emit('modified')

    def __getitem__(self, key):
        return self.items[key]

    def __delitem__(self, key):
        del self.items[key]
        self.emit('modified')

    def index(self, value):
        return self.items.index(value)


class _xListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin, ListCtrlSelectionManagerMix):
    def __init__(self, lst, *args, **kwds):
        wx.ListCtrl.__init__(self, *args, **kwds)
        ListCtrlAutoWidthMixin.__init__(self)
        ListCtrlSelectionManagerMix.__init__(self)
        self.lst = lst

        # item images
        self.imagelist = wx.ImageList(16, 16)
        self.SetImageList(self.imagelist, wx.IMAGE_LIST_NORMAL)
        self.SetImageList(self.imagelist, wx.IMAGE_LIST_SMALL)
        self.pixmaps = {}

    def getpixmap(self, image):
        if image is None:
            return None

        if image not in self.pixmaps:
            if isinstance(image, Image.Image):
                img = _pil_to_wxbitmap(image)
            elif isinstance(image, wx.Bitmap):
                img = image
            else:
                img = _pil_to_wxbitmap(images[image][16,16])
            self.pixmaps[image] = self.imagelist.Add(img)

        return self.pixmaps[image]

    def OnGetItemText(self, item, col):
        if hasattr(self.lst.data, 'get'):
            return str(self.lst.data.get(item, self.lst.columns[col]))
        else:
            if col == 0:
                return str(self.lst.data[item])
            else:
                raise AttributeError

    def OnGetItemImage(self, item):
        if hasattr(self.lst.data, 'get_image'):
            return self.getpixmap(self.lst.data.get_image(item))


class List(Widget, _xListCtrl):
    def __init__(self, place, data=None, columns=None, headers=False, editable=False, 
                 connect={}, **kwds):
        flags = wx.LC_REPORT|wx.LC_VIRTUAL|wx.BORDER_SUNKEN
        if not headers:
            flags |= wx.LC_NO_HEADER
        if editable:
            flags |= wx.LC_EDIT_LABELS

        _xListCtrl.__init__(self, self, place[0], -1, style=flags)
        Widget.__init__(self, place, connect, **kwds)

        if data is None:
            data = ListData()

        if columns is None:
            columns = [None]

        self.selection = []

        self._columns = columns
        self._data = data
        if hasattr(self._data, 'connect'):
            self._data.connect('modified', self.update)

        self.update()

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        for event in (wx.EVT_LIST_ITEM_SELECTED, wx.EVT_LIST_ITEM_DESELECTED, wx.EVT_LIST_ITEM_FOCUSED):
            self.Bind(event, self.on_update_selection)

        self.can_drop = False
        self.drop_formats = []

        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click)

    def on_right_click(self, evt):
        item, flags = self.HitTest(evt.GetPosition())
        if not (flags & wx.LIST_HITTEST_ONITEM):
            item = -1
        self.emit('right-click', item)
        evt.Skip()

    def on_item_activated(self, event):
        self.emit('item-activated', self.data[event.m_itemIndex])

    def on_update_selection(self, event):
        # we can't update the selection here since if the event is ITEM_FOCUSED
        # the selection hasn't been updated yet
        wx.CallAfter(self.update_selection)
        event.Skip()

    def update_selection(self):
        # we have to work around the fact that a virtual ListCtrl does _not_
        # send ITEM_SELECTED or ITEM_DESELECTED events when multiple items
        # are selected / deselected

        try:
            selection = self.getSelection()
        except wx.PyDeadObjectError:
            return
        if selection != self.selection:
            self.selection = selection
            self.emit('selection-changed')

    def set_columns(self, columns):
        self._columns = columns
        self.update()
    def get_columns(self):
        return self._columns
    columns = property(get_columns, set_columns)

    def set_data(self, data):
        if data is None:
            data = ListData()
        self._data = data
        if hasattr(self._data, 'connect'):
            self._data.connect('modified', self.update)
        self.update()
    def get_data(self):
        return self._data
    data = property(get_data, set_data)

    def setsel(self, sel):
        for item in sel:
            self.SetItemState(item, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

    def update(self):
        self.Freeze()
        sel = self.selection
        self.ClearAll()
        self.SetItemCount(len(self.data))
        for num, name in enumerate(self.columns):
            self.InsertColumn(num, str(name))
        self.selection = sel
        for item in sel:
            self.SetItemState(item, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        self.resizeLastColumn(-1)
        self.Thaw()

