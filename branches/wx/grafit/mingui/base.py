import sys
import os.path
import platform

import wx

import PIL.Image
from signals import HasSignals

class Container(HasSignals):
    def __init__(self):
        self.children = []

    def place(self, **kwds):
        return self, kwds
    __call__ = place

def _pil_to_wxbitmap(image):
    wi = wx.EmptyImage(image.size[0], image.size[1])
    wi.SetData(image.convert('RGB').tostring())
    wi.SetAlphaData(image.convert('RGBA').tostring()[3::4])
    return wi.ConvertToBitmap()


def _text_img_wxbitmap(text, image, rotate=False):
    bimp = _pil_to_wxbitmap(image)

    # create an empty bitmap
    dc = wx.MemoryDC()
    w, h = dc.GetTextExtent(text)
    wb, hb = bimp.GetSize()
    bmp = wx.EmptyBitmap(w + wb, max([h, hb]))

    # draw bitmap and text
    dc.SelectObject(bmp)
    dc.BeginDrawing()
    dc.SetBackground(wx.Brush(app.mainwin.GetBackgroundColour()))
    dc.Clear()
    dc.SetFont(app.mainwin.GetFont())
    dc.DrawBitmap(bimp, 0, 0, True)
    dc.DrawText(text, wb+5, 0)
    dc.EndDrawing()
    if platform.system() == 'Linux':
        bmp.SetMaskColour(app.mainwin.GetBackgroundColour())

    # rotate if nescessary
    if rotate:
        bmp = bmp.ConvertToImage().Rotate90(False).ConvertToBitmap()

    return bmp

class Placeable(object):
    def __init__(self, place, **kwds):
        if place is None:
            self.parent = None
            placeargs = {}
        elif isinstance(place, Container):
            self.parent = place
            placeargs = {}
        else:
            self.parent, placeargs = place

        if hasattr(self.parent, '_add'):
            self.parent._add(self, **placeargs)
            self.parent.children.append(self)
        for k, v in kwds.iteritems():
            setattr(self, k, v)

class Poulos(Exception):
    pass

class Widget(Placeable, HasSignals):
    def __init__(self, place, connect={}, **kwds):
        self.name = None
        Placeable.__init__(self, place, **kwds)
        for signal, slot in connect.iteritems():
            self.connect(signal, slot)

    def ref(self, path):
        cmd, path = path[0], path[1:]
        if '^' not in path and '/' not in path:
            name = path.strip()
            ret = True
        else:
            try:
                m1 = path.index('/')
            except ValueError:
                m1 = len(path)
            try:
                m2 = path.index('^')
            except ValueError:
                m2 = len(path)
            pos = min(m1, m2)
            name, rest = path[:pos].strip(), path[pos:]
            ret = False

        if cmd == '/':
            next = self.find(name)
        elif cmd == '^':
            next = self.rfind(name)

        if ret:
            return next
        else:
            return next.ref(rest)

    def find(self, name):
        if self.name == name:
            return self
        if hasattr(self, 'children'):
            for c in self.children:
                if hasattr(c, 'find'):
                    f = c.find(name)
                    if f is not None:
                        return f

    def rfind(self, name):
        widget = self
        if widget.name == name:
            return widget

        while hasattr(widget, 'parent'):
            widget = widget.parent
            if widget.name == name:
                return widget
        return None

    def destroy(self):
        self.Destroy()

    def show(self): self.visible = True
    def hide(self): self.visible = False

    def visible():
        doc = ""
        def fget(self): return self.IsShown()
        def fset(self, vis):
            if isinstance(vis, basestring):
                vis = eval(vis, {})
            if vis:
                self.Show(True)
            else:
                self.Hide()
        return locals()
    visible = property(**visible())

    def enabled():
        doc = """True if the control can be manipulated by the user. Disabled controls are typically
displayed in a different way, and do not respond to user actions."""
        def fget(self): return self.IsEnabled()
        def fset(self, value): 
            if isinstance(value, basestring):
                value = eval(value, {})
            self.Enable(value)
        return locals()
    enabled = property(**enabled())

    def size():
        doc = ""
        def fget(self): return tuple(self.GetSize())
        def fset(self, sz): 
            if isinstance(sz, basestring):
                sz = eval(sz, {})
            self.SetSize(sz)
        return locals()
    size = property(**size())

    def position():
        doc = ""
        def fget(self): return tuple(self.GetPosition())
        def fset(self, po): 
            if isinstance(sz, basestring):
                sz = eval(sz, {})
            self.SetPosition(po)
        return locals()
    position = property(**position())

    def close(self):
        return self.Close()

class Label(Widget, wx.StaticText):
    def __init__(self, place, text, **kwds):
        wx.StaticText.__init__(self, place[0], -1, text)
        Widget.__init__(self, place, **kwds)

class Image(Widget, wx.StaticBitmap):
    def __init__(self, place, image, **kwds):
        bitmap = _pil_to_wxbitmap(image)

        wx.StaticBitmap.__init__(self, place[0], -1, bitmap)
        Widget.__init__(self, place, **kwds)

class Button(Widget, wx.Button, wx.ToggleButton):
    def __init__(self, place, text='', toggle=False, connect={}, **kwds):

        if toggle:
            wxbase = wx.ToggleButton
        else:
            wxbase = wx.Button

        wxbase.__init__(self, place[0], -1, text)
        Widget.__init__(self, place, connect, **kwds)

#        self.Bind(wx.EVT_LEFT_DCLICK, self.emitter('double-clicked'), True)
        self.Bind(wx.EVT_BUTTON, self.emitter('clicked'))
        self.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggled)

    def on_toggled(self, evt):
        self.emit('toggled', evt.IsChecked())

    def toggled():
        doc = "Whether a toggle button is on or not"
        def fget(self): return self.GetValue()
        def fset(self, state): self.SetValue(state)
        return locals()
    toggled = property(**toggled())

    def text():
        doc = "Text to display inside the button"
        def fget(self): return self.GetLabel()
        def fset(self, text): self.SetLabel(text)
        return locals()
    text = property(**text())

class Singleton(object):
    _state = {}
    def __new__(cls, *p, **k):
        self = object.__new__(cls, *p, **k)
        self.__dict__ = cls._state
        return self

class Application(Singleton):
    def __init__(self):
        if not hasattr(self, '_app'):
            self._app = wx.App(redirect=False)

    def run(self, mainwin):
        self.mainwin = mainwin
        self._app.SetTopWindow(self.mainwin)
        self.mainwin.show()
        return self._app.MainLoop()

app = Application()

def run(mainwinclass):
    Application().run(mainwinclass)
