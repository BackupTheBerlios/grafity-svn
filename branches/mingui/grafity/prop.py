import wx
import wx.xrc as xrc

class Editor(object):
    def __init__(self, parent, xrcfile, obj):
        doc = xrc.XmlDocument(xrcfile)

        self.found = []

        node = doc.GetRoot()
        node = node.GetChildren()
        prop = node.GetProperties()
        found = None

        while node is not None and found is None:
            prop = node.GetProperties()
            while prop is not None:
                if prop.GetName() == 'name':
                    name = prop.GetValue()
                    if name ==  'edit(%s)' % (type(obj).__name__,):
                        found = node
                        break
                prop = prop.GetNext()
            node = node.GetNext()

        self.scan(found)

        self.resource = xrc.XmlResource(xrcfile)
        self._widget = self.resource.LoadDialog(parent._widget, 'edit(%s)' % (type(obj).__name__,))

        self.widgets = []
        for name in self.found:
            widget = xrc.XRCCTRL(self._widget, name)
            self.widgets.append((widget, name[5:-1]))

        self.lookup_prop = None
        self.lookup_widget = None

        self.connect_object(obj)

        self.closebtn = xrc.XRCCTRL(self._widget, 'wxID_CLOSE')
        self.closebtn.Bind(wx.EVT_BUTTON, self.on_clicked)

    def on_clicked(self, evt):
        self._widget.Close()

    def connect_object(self, obj):
        for widget, prop in self.widgets:
            self.connect_changed(widget, self.on_gui_changed)
        self.lookup_prop = dict(self.widgets)
        self.lookup_widget = dict((p, w) for (w, p) in self.widgets)
        self.values = [self.get_value(w) for w, _ in self.widgets]

        self.obj = obj
        self.obj.connect('modified', self.on_obj_changed)
        self.lock = False

    def disconnect_object(self):
        for widget, prop in self.widgets:
            self.disconnect_changed(widget)
        self.lookup_prop = None
        self.lookup_widget = None

        self.obj = None

    def on_gui_changed(self, evt):
        newval = [self.get_value(w) for w, _ in self.widgets]

        self.lock = True
        for x, y, prop in zip(self.values, newval, [name for _, name in self.widgets]):
            if x != y:
                setattr(self.obj, prop, y)
        self.lock = False

        self.values = newval

    def on_obj_changed(self):
        newval = [getattr(self.obj, name) for _, name in self.widgets]

        for x, y, wi in zip(self.values, newval, [w for w, _ in self.widgets]):
            if x != y:
                self.set_value(wi, y)
         
        self.values = newval

    def set_value(self, widget, value):
        if isinstance(widget, (wx.TextCtrl, wx.SpinCtrl)):
            widget.SetValue(value)

    def get_value(self, widget):
        if isinstance(widget, (wx.TextCtrl, wx.SpinCtrl)):
            return widget.GetValue()

    def connect_changed(self, widget, fn):
        if isinstance(widget, wx.TextCtrl):
            widget.Bind(wx.EVT_KILL_FOCUS, fn)
            widget.Bind(wx.EVT_TEXT_ENTER, fn)
        elif isinstance(widget, wx.SpinCtrl):
            widget.Bind(wx.EVT_SPINCTRL, fn)

    def disconnect_changed(self, widget):
        if isinstance(widget, wx.TextCtrl):
            widget.Unbind(wx.EVT_KILL_FOCUS, fn)
            widget.Unbind(wx.EVT_TEXT_ENTER, fn)
        elif isinstance(widget, wx.SpinCtrl):
            widget.Unbind(wx.EVT_SPINCTRL, fn)
 
    def scan(self, node):
        prop = node.GetProperties()
        found = False
        while prop is not None:
            if prop.GetName() == 'name':
                name = prop.GetValue()
                if name.startswith('auto(') and name.endswith(')'):
                    found = True
            elif prop.GetName() == 'class':
                cls = prop.GetValue()
            if found:
                self.found.append(name)
            prop = prop.GetNext()

        child = node.GetChildren()
        while child is not None:
            self.scan(child)
            child = child.GetNext()
