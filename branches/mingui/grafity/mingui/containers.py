from base import Widget, Container, _text_img_wxbitmap, _pil_to_wxbitmap
from commands import Toolbar, Command
from images import images
#from grafit.thirdparty.splitter import MultiSplitterWindow
from wx.lib.splitter import MultiSplitterWindow

import wx

class Box(Widget, Container, wx.Panel):
    def __init__(self, place, orientation='vertical', **kwds):
        wx.Panel.__init__(self, place[0], -1)
        Widget.__init__(self, place, **kwds)
        Container.__init__(self)
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
        
class Grid(Widget, Container, wx.Panel):
    """
    usage:
    ------
    >>> g = gui.Grid(parent, rows, columns, **place)
    >>> child = gui.Label('Text', pos=(row, col), span=(x, y), expand=True)
    """
    def __init__(self, place, rows=2, columns=2, **args):
        wx.Panel.__init__(self, place[0], -1)
        Widget.__init__(self, place, **args)
        Container.__init__(self)

        self.layout = wx.GridBagSizer(rows, columns)
        self.layout.SetEmptyCellSize((0,0))
        self.SetSizer(self.layout)
#        self.layout.SetSizeHints(self)
        self.SetAutoLayout(True)
#        self.Bind(wx.EVT_SIZE, self.OnSize)

    def _add(self, widget, position=(0,0), span=(1,1), expand=False):
        self.layout.Add(widget, position, span, flag=wx.EXPAND|wx.ALL)
#        self.layout.CalcMin()
#        self.layout.RecalcSizes()
#        self.layout.SetSizeHints(self)
        self.Fit()
##    def OnSize(self, evt):
#        print evt.GetSize()
#        if self.GetAutoLayout():
#            self.Layout()
#        evt.Skip()



class Splitter(Widget, Container, MultiSplitterWindow):
    def __init__(self, place, orientation, **kwds):
        self.orientation = orientation
        MultiSplitterWindow.__init__(self, place[0], style=wx.SP_LIVE_UPDATE)
        Widget.__init__(self, place, **kwds)
        Container.__init__(self)
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
        Container.__init__(self)

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


class Panel(Box):
    def __init__(self, place, position, **kwds):
        self.pos = position
        if position in ['left', 'right']:
            orientation = 'vertical'
            tbo = 'horizontal'
        elif position in ['top', 'bottom']:
            orientation = 'horizontal'
            tbo = 'vertical'
        self.orientation = orientation

        Box.__init__(self, place, tbo, **kwds)
        self.contents = []
        self.toolbar = Toolbar(self.place(stretch=0), orientation)
        self.splitter = place[0]

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self._shown = False
        self._width = place[1].get('width', 100)
        self._updatewidth = True

    def on_paint(self, evt):
        # The first time we are shown,
        # set the correct size
        if not self._shown:
            self._shown = True
            sz = self.toolbar.size[self.orientation=='horizontal']
            self.splitter.resize_child(self, sz)

            for w in self.contents:
                if w._command.state:
                    w._command(True)
        evt.Skip()

    def _add(self, widget, label=None, image=None, **opts):
        if image is not None:
            self.contents.append(widget)
            widget._command = self.callback(widget, label, image)
            self.toolbar.append(widget._command)
        opts['prepend'] = self.pos in ['bottom', 'right']
        Box._add(self, widget, **opts)
        if image is not None:
            self.layout.Hide(widget)

    def open(self, widget):
        widget._command.state = True

    def close(self, widget):
        widget._command.state = False

    def callback(self, widget, label, image):
        if label is None:
            label = ""
        image = _text_img_wxbitmap(label, images[image][16,16],
                                   rotate=self.orientation == 'vertical')

        @Command.from_function('callable', 'callit', image, type='check')
        def callable(on):
            sz = self.toolbar.size[self.orientation=='horizontal']
            if on:
                self._updatewidth = False
                for win in self.contents:
                    if win!=widget:
                        win._command.state = False
                self._updatewidth = True
                self.layout.Show(widget)
                self.splitter.resize_child(self, self._width+sz)
            else:
                if self._updatewidth:
                    self._width = self.size[self.orientation=='horizontal']-sz
                self.layout.Hide(widget)
                self.splitter.resize_child(self, sz)
        return callable

from wx.lib.scrolledpanel import ScrolledPanel
class Scrolled(Widget, Container, ScrolledPanel):
    def __init__(self, place, **args):
        ScrolledPanel.__init__(self, place[0], -1)#, style=wx.SUNKEN_BORDER)
        Widget.__init__(self, place, **args)
        Container.__init__(self)

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.layout)
        self.SetAutoLayout(True)
        self.SetupScrolling()

    def _add(self, widget):
        self.layout.Add(widget, 1., wx.EXPAND)
#        self.layout.SetSizeHints(self)
