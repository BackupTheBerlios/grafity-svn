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


    def get_min_size(self): return self.GetMinSize()
    def set_min_size(self, size): self.SetMinSize(size)
    min_size = property(get_min_size, set_min_size)


    def close(self):
        return self.Close()

class Label(Widget, wx.StaticText):
    def __init__(self, place, text="", **kwds):
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



class Checkbox(Widget, wx.CheckBox):
    """ A a labelled box which by default is either on (checkmark is visible) 
        or off (no checkmark). 
    """
    def __init__(self, place, label='', **args):
        wx.CheckBox.__init__(self, place[0], -1, label)
        Widget.__init__(self, place, **args)

        self.Bind(wx.EVT_CHECKBOX, self.on_event)

    def get_state(self):
        return self.GetValue()
    def set_state(self, state):
        self.SetValue(state)
    state = property(get_state, set_state)

    def on_event(self, event):
        self.emit('modified', self.state)


from wx.lib.colourselect import ColourSelect, EVT_COLOURSELECT
from wx.lib.fancytext import StaticFancyText

class Spin(Widget, wx.SpinCtrl):
    """
    usage:
    ------
    >>> spin = gui.Spin(parent, **place)
    >>> spin.value = 16
    >>> spin.value
    16

    signals:
    --------
    modified(value)
    """
    def __init__(self, place, **args):
        wx.SpinCtrl.__init__(self, place[0], -1)
        Widget.__init__(self, place, **args) 

        self.Bind(wx.EVT_SPINCTRL, self.on_spin)

    def get_value(self): return self.GetValue()
    def set_value(self, val): self.SetValue(val)
    value = property(get_value, set_value)

    def on_spin(self, event):
        self.emit('modified', self.value)

class Choice(Widget, wx.Choice):
    def __init__(self, place, **args):
        wx.Choice.__init__(self, place[0], -1)
        Widget.__init__(self, place, **args)
        self.Bind(wx.EVT_CHOICE, self.on_choice)

    def append(self, s):
        self.Append(s)

    def get_value(self): return self.GetSelection()
    def set_value(self, sel): self.SetSelection(sel)
    value = property(get_value, set_value)

    def on_choice(self, event):
        self.emit('select', self.value)



class ImageChoice(Widget, wx.BitmapButton):
    def __init__(self, place, **args):
#        bimp = wx.Image('../data/images/'+'arrow.png').ConvertToBitmap()
        bimp = self.create_colored_bitmap((30, 10), (100, 80, 120))
        wx.BitmapButton.__init__(self, place[0], -1, bimp, style=wx.BU_EXACTFIT)
        Widget.__init__(self, place, **args) 
        self.imagelist = wx.ImageList(20, 10)

        self.Bind(wx.EVT_BUTTON, self.on_button)

        self.images = {}
        self.items = []

        self.down = False

    def create_colored_bitmap(self, size, rgb):
        dc = wx.MemoryDC()
        bmp = wx.EmptyBitmap(*size)
        dc.SelectObject(bmp)
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush(wx.Colour(*rgb)))
        dc.Clear()
        dc.EndDrawing()

        return bmp

    def on_button(self, event):
        if self.down:
            self.on_kill_focus(None)
            return
        self.win = win = wx.PopupWindow(self, wx.SUNKEN_BORDER)
        lst = wx.ListCtrl(win, -1, size=(120, 220), style=wx.LC_SMALL_ICON)
        win.lst = lst
#        lst.InsertColumn(0, 'col')
#        lst.SetImageList(self.imagelist, wx.IMAGE_LIST_NORMAL)
        lst.SetImageList(self.imagelist, wx.IMAGE_LIST_SMALL)
        lst.SetItemSpacing(0, 1)
        for i, img in enumerate(self.items):
            lst.InsertImageItem(i, img)
        pos = self.ClientToScreen( (0,0) )
        sz = self.GetSize()
        win.Position(pos, (0,sz[1]))
        win.SetSize(lst.GetSize())
        win.Show(True)
#        win.Popup()
        lst.SetFocus()
        lst.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_sel)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)
        self.down = True
        self._selection = -1

    def on_sel(self, event):
        i = event.GetIndex()
        bitmap = self.images[self.items[i]]
        self.SetBitmapLabel(bitmap)
        wx.CallAfter(self.win.Destroy)
        self.down = False
        self._selection = i
        self.emit('select', i)

    def set_selection(self, idx):
        bitmap = self.images[self.items[idx]]
        self._selection = idx
        self.SetBitmapLabel(bitmap)
    def get_selection(self):
        return self._selection
    value = property(get_selection, set_selection)

    def on_kill_focus(self, event):
        try:
            self.win.Destroy()
            self.down = False
        except wx.PyDeadObjectError:
            pass

    def append(self, bitmap):
        if isinstance(bitmap, basestring):
            bitmap = wx.Image(DATADIR+'data/images/'+bitmap).ConvertToBitmap()
        id = self.imagelist.Add(bitmap)
        self.items.append(id)

class ColorSelect(Widget, ColourSelect):
    def __init__(self, place, **args):
        self = ColourSelect(place[0], -1, size=(100, 10))
        Widget.__init__(self, place, **args)

class Frame(Widget, Container, wx.Panel):
    def __init__(self, place, orientation='vertical', title='', **kwds):
        wx.Panel.__init__(self, place[0], -1)
        Widget.__init__(self, place, **kwds)
        Container.__init__(self)

        self._box = wx.StaticBox(self, -1, title)
        if orientation == 'horizontal':
            self.layout = wx.StaticBoxSizer(self._box, wx.HORIZONTAL)
        elif orientation == 'vertical':
            self.layout = wx.StaticBoxSizer(self._box, wx.VERTICAL)
        else:
            raise NameError
        self.SetSizer(self.layout)
        self.SetAutoLayout(True)

    def _add(self, widget, expand=True, stretch=1.0):
#        widget.Reparent(self.parent)
        if expand:
            expand = wx.EXPAND
        else:
            expand = 0
        self.layout.Add(widget, stretch, wx.EXPAND)
#        self.layout.SetSizeHints(self)
        self.Layout()

class ProgressBar(Widget, wx.Gauge):
    def __init__(self, place, **args):
        wx.Gauge.__init__(self, place[0], -1, 100)
        Widget.__init__(self, place, **args)

    def set_value(self, value): self.SetValue(value); wx.Yield()
    def get_value(self): return self.GetValue()
    value = property(get_value, set_value)

    def set_range(self, range): self.SetRange(range)
    def get_range(self): return self.GetRange()
    range = property(get_range, set_range)


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
