import sys

from base import Widget, Container, _pil_to_wxbitmap, Placeable
from signals import HasSignals
from images import images

import Image
import wx

commands = {}

def CommandRef(parent=None, object=None, id=None):
    if object is None:
        try:
            try:
                parent._add(commands[id])
            except AttributeError:
                parent[0]._add(commands[id])
        except KeyError:
            pass
    else:
        parent._add(parent.ref(object).commands[id])


class Separator(Placeable):
    def __init__(self, parent, **kwds):
        self.command = 'sep'
        Placeable.__init__(self, parent)

class Toolbar(Widget, Container, wx.ToolBar):
    def __init__(self, place, orientation='horizontal', **kwds):
        orient = { 'horizontal': wx.TB_HORIZONTAL, 'vertical': wx.TB_VERTICAL } [orientation]
        wx.ToolBar.__init__(self, place[0],
                            style=wx.SUNKEN_BORDER|wx.TB_FLAT|wx.TB_TEXT|orient)
        Widget.__init__(self, place, **kwds)
        Container.__init__(self)
        self.Bind(wx.EVT_TOOL, self.on_tool)
        self.tools = {}

    def on_tool(self, event):
        action = self.tools[event.GetId()]
        if action.type == 'check':
            action(event.IsChecked())
        else:
            action()

    def append(self, action):
        if action is None:
            self.AddSeparator()
        else:
            if action.pixmap is None:
                bitmap = None
            elif isinstance(action.pixmap, Image.Image):
                bitmap = _pil_to_wxbitmap(action.pixmap)
            elif isinstance(action.pixmap, wx.Bitmap):
                bitmap = action.pixmap
            elif isinstance(action.pixmap, basestring):
                bitmap = _pil_to_wxbitmap(images[action.pixmap][16,16])
            else:
                bitmap = None
            id = wx.NewId()
            if action.type == 'check':
                self.AddCheckTool(id, bitmap, bitmap, action.name, action.desc)
            elif action.type == 'radio':
                self.AddRadioTool(id, bitmap, bitmap, action.name, action.desc)
            else:
                self.AddSimpleTool(id, bitmap, action.name, action.desc)
            self.tools[id] = action
            
            x, y = self.GetToolBitmapSize()
            xb, yb = bitmap.GetSize()
            self.SetToolBitmapSize((max(x, xb), max(y, yb)))
            action.upd.append([self, id])

    def _add(self, child, **place):
        if isinstance(child, Command):
            self.append(child)
        elif isinstance(child, Separator):
            self.append(None)
        else:
            try:
                self.append(commands[child.command])
            except KeyError:
                pass

#   def _add(self, child, **place):
#        self.AddControl(child)

    def __call__(self):
        return self

 

class Menubar(Widget, Container, wx.MenuBar):
    def __init__(self, place, **kwds):
        wx.MenuBar.__init__(self)
        Container.__init__(self)
        self.frame = place[0]
        Widget.__init__(self, place, **kwds)
        self.frame.Bind(wx.EVT_MENU, self.on_menu)
        self.menus = {}
        self.items = {}

    def on_menu(self, event):
        self.items[event.GetId()]()

    def __getitem__(self, item):
        return self.menus[item]

    def __call__(self):
        return self

class _menu(wx.Menu):
    def UpdateUI(self, evt):
        print evt
        wx.Menu.UpdateUI(evt)

class Menu(Container):
    def __init__(self, menubar=None, label=None):
        Container.__init__(self)
        self._menu = _menu()
        self.menubar = menubar
        self.name = label
        self.items = {}
        self._menu.Bind(wx.EVT_MENU, self.on_menu)
        if menubar is not None:
            menubar.Append(self._menu, label)
            menubar.menus[label] = self

#    def __call__(self):
#        return self
    def _add(self, child, **place):
        if isinstance(child, Command):
            self.append(child)
        elif isinstance(child, Separator):
            self.append(None)
        else:
            try:
                self.append(commands[child.command])
            except KeyError:
                pass

    def append(self, action):
        if action is None:
            self._menu.AppendSeparator()
        else:
            id = wx.NewId()
            self.items[id] = action
            if action.accel is not None:
                name = action.name + '\t' + action.accel
            else:
                name = action.name
            if action.desc is not None:
                help = action.desc
            else:
                help = ''
#            self._menu.Append(id, name, help)
            item = wx.MenuItem(self._menu, id, name, help)
            if action.pixmap is not None:
                item.SetBitmap(_pil_to_wxbitmap(images[action.pixmap][16,16]))
            self._menu.AppendItem(item)
    
            if self.menubar is not None:
                self.menubar.items[id] = action

    def __getitem__(self, item):
        return self.items[self._menu.FindItemByPosition(item).GetId()]
    def __setitem__(self, item, value):
        pass
    def __delitem__(self, item, value):
        pass

    def on_menu(self, event):
        self.items[event.GetId()]()

class Item(Placeable):
    def __init__(self, parent, value, label, *args, **kwds):
#        self.command = command
        Placeable.__init__(self, parent)

class Command(HasSignals):
    def __init__(self, id='', label='', desc='', image=None, accel=None, type='simple'):
        self.id, self.name, self.desc, self.pixmap, self.accel = id, label, desc, image, accel
        self.type = type

        self._state = False
        self._enabled = True
        self.upd = []
        self.items = []

    def get_state(self):
        return self._state
    def set_state(self, state):
        self._state = state
        for w, id in self.upd:
            w.ToggleTool(id, state)
            self(state)
    state = property(get_state, set_state)

    def enabled():
        def fget(self):
            return self._enabled
        def fset(self, state):
            self._enabled = state
            for w, id in self.upd:
                w.EnableTool(id, state)
        return locals()
    enabled = property(**enabled())

    def __call__(self, *args, **kwds):
        if hasattr(self, 'call'):
            self.call(*args, **kwds)
        else:
            self.emit('activated')

    @staticmethod
    def from_function(name, desc, pixmap=None, accel=None, type='simple'):
        def f(fcn):
            c = Command(name, name, desc, pixmap, accel, type)
            c.call = fcn
            return c
        return f

