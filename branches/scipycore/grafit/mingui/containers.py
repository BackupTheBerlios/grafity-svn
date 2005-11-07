from base import Widget, Container
#from grafit.thirdparty.splitter import MultiSplitterWindow
from wx.lib.splitter import MultiSplitterWindow

import wx

class Box(Widget, Container, wx.Panel):
    def __init__(self, place, orientation='vertical', **kwds):
        wx.Panel.__init__(self, place[0], -1)
        Widget.__init__(self, place, **kwds)
        if orientation == 'horizontal':
            self.layout = wx.BoxSizer(wx.HORIZONTAL)
        elif orientation == 'vertical':
            self.layout = wx.BoxSizer(wx.VERTICAL)
        else:
            raise NameError
        self.SetAutoLayout(True)
        self.SetSizer(self.layout)

    def __getitem__(self, key):
        return self.GetChildren()[key]

    def __iter__(self):
        for item in self.GetChildren():
            yield item

    def _add(self, widget, expand=True, stretch=1.0, prepend=False):
        if expand:
            expand = wx.EXPAND
        else:
            expand = 0
        if prepend:
            self.layout.Prepend(widget, stretch, expand | wx.ADJUST_MINSIZE)
        else:
            self.layout.Add(widget, stretch, expand | wx.ADJUST_MINSIZE)
        self.layout.Layout()
        self.layout.Fit(self)


class Splitter(Widget, Container, MultiSplitterWindow):
    def __init__(self, place, orientation, **kwds):
        self.orientation = orientation
        MultiSplitterWindow.__init__(self, place[0], style=wx.SP_LIVE_UPDATE)
        Widget.__init__(self, place, **kwds)
        self.SetOrientation({'horizontal':wx.HORIZONTAL, 'vertical':wx.VERTICAL}[orientation])

    def _add(self, widget, width=-1, stretch=0):
        widget._stretch = stretch
        if width == -1:
            width = widget.GetBestSize()[self.orientation=='vertical']
        self.AppendWindow(widget, width)

    def _OnMouse(self, evt):
        evt.ShiftDown = lambda: True
        return MultiSplitterWindow._OnMouse(self, evt)

    def resize_child(self, widget, size):
        idx = self._windows.index(widget)
        if self.orientation == 'horizontal':
            sash = size-widget.size[0]
            widget.size = (size, widget.size[1])
        else:
            sash = size-widget.size[1]
            widget.size = (widget.size[0], size)
        self._sashes[idx] += sash
        self.SizeWindows()

    def child_size(self, widget):
        return self._sashes[self._windows.index(widget)]

    def _SizeSizeWindows(self):
        total_window_w = self.GetClientSize()[self.orientation == 'vertical'] \
                         - 2*self._GetBorderSize() - self._GetSashSize()*(len(self._windows)-1)

        for win, sash in zip(self._windows, self._sashes):
            if win._stretch == 0:
                total_window_w -= sash

        total_stretch = sum(w._stretch for w in self._windows)

        for i, win in enumerate(self._windows):
            if win._stretch != 0:
                self._sashes[i] = total_window_w*win._stretch/total_stretch

        MultiSplitterWindow._SizeWindows(self)

    _SizeWindows = _SizeSizeWindows


class Notebook(Widget, Container, wx.Notebook):
    def __init__(self, place, connect={}, **kwds):
        wx.Notebook.__init__(self, place[0], -1)
        Widget.__init__(self, place, connect, **kwds)

        # item images
        self.imagelist = wx.ImageList(16, 16)
        self.SetImageList(self.imagelist)
        self.pixmaps = {}

        self.pages = []


    def getpixmap(self, image):
        if image not in self.pixmaps:
            self.pixmaps[image] = self.imagelist.Add(_pil_to_wxbitmap(images[image][16,16]))
        return self.pixmaps[image]

    def _add(self, widget, label="", image=None):
        self.AddPage(widget, label)
        if image is not None:
            self.SetPageImage(self.GetPageCount()-1, self.getpixmap(image))
        self.pages.append(widget)

    def active_page():
        def fget(self): return self.pages[self.GetSelection()]
        def fset(self, page): self.SetSelection(self.pages.index(page))
        return locals()
    active_page = property(**active_page())

    def delete(self, widget):
        self.DeletePage(self.pages.index(widget))
        self.pages.remove(widget)

    def select(self, widget):
        if widget in range(len(self.pages)):
            self.SetSelection(widget)
        elif widget in self.pages:
            self.SetSelection(self.pages.index(widget))
        else:
            raise NameError


