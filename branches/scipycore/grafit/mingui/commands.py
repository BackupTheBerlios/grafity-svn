from base import Widget, Container, _pil_to_wxbitmap
from signals import HasSignals
from images import images

import Image
import wx

class Toolbar(Widget, Container, wx.ToolBar):
    def __init__(self, place, orientation='horizontal', **kwds):
        orient = { 'horizontal': wx.TB_HORIZONTAL, 'vertical': wx.TB_VERTICAL } [orientation]
        wx.ToolBar.__init__(self, place[0],
                            style=wx.SUNKEN_BORDER|wx.TB_FLAT|wx.TB_TEXT|orient)
        Widget.__init__(self, place, **kwds)
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
        self.AddControl(child)
 

class Menubar(Widget, wx.MenuBar):
    def __init__(self, place, **kwds):
        wx.MenuBar.__init__(self)
        self.frame = place[0]
        Widget.__init__(self, place, **kwds)
        self.frame.Bind(wx.EVT_MENU, self.on_menu)
        self.menus = {}
        self.items = {}

    def on_menu(self, event):
        self.items[event.GetId()]()

    def __getitem__(self, item):
        return self.menus[item]

class Menu(object):
    def __init__(self, menubar=None, name=None):
        self._menu = wx.Menu()
        self.menubar = menubar
        self.name = name
        self.items = {}
        self._menu.Bind(wx.EVT_MENU, self.on_menu)
        if menubar is not None:
            menubar.Append(self._menu, name)
            menubar.menus[name] = self

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

class Command(HasSignals):
    def __init__(self, name, desc, call, pixmap=None, accel=None, type='simple'):
        self.name, self.desc, self.call, self.pixmap, self.accel = name, desc, call, pixmap, accel
        self.type = type

        self._state = False
        self._enabled = True
        self.upd = []

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
        return self.call(*args, **kwds)

    @staticmethod
    def from_function(name, desc, pixmap=None, accel=None, type='simple'):
        def f(fcn):
            return Command(name, desc, fcn, pixmap, accel, type)
        return f

