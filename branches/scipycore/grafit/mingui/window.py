from base import Widget, Container
from commands import Menubar, Toolbar

import wx

import PIL.Image
from signals import HasSignals

class Window(wx.Frame, Widget, Container):
    def __init__(self, parent=None, connect={}, **kwds):
        wx.Frame.__init__(self, parent, -1)
        Widget.__init__(self, None, connect, **kwds)
        self.parent = parent

    def _add(self, child, **place):
        if isinstance(child, Toolbar):
            self.SetToolBar(child)
        elif isinstance(child, Menubar):
            self.SetMenuBar(child)
#        else:
#            Container._add(self, child, **place)


    title = property(lambda self: self.GetTitle(), lambda self, t: self.SetTitle(t))

class Dialog(wx.Dialog, Widget, Container):
    def __init__(self, parent=None, connect={}, **kwds):
        wx.Dialog.__init__(self, parent, -1, style=wx.THICK_FRAME)
        Widget.__init__(self, None, connect, **kwds)
        self.parent = parent

    def show(self, modal=False):
        if modal:
            return self.ShowModal()
        else:
            return Widget.show(self)

    title = property(lambda self: self.GetTitle(), lambda self, t: self.SetTitle(t))
