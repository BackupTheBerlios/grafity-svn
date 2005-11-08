import wx
import  keyword
from wx.html import HtmlWindow
import wx.stc as stc
from base import Widget

class Text(Widget, wx.TextCtrl):
    def __init__(self, place, multiline=False, connect={}, **kwds):
        style = 0
        if multiline:
            style |= wx.TE_MULTILINE
        else:
            style |= wx.TE_PROCESS_ENTER
        wx.TextCtrl.__init__(self, place[0], -1, style=style)
        Widget.__init__(self, place, connect, **kwds)

    def get_value(self):
        return self.GetValue()
    def set_value(self, val):
        self.SetValue(val)
    text = property(get_value, set_value)


class Html(Widget, HtmlWindow):
    def __init__(self, place, connect={}, **kwds):
        HtmlWindow.__init__(self, place[0], -1)
        Widget.__init__(self, place, connect, **kwds)
        self.SetStandardFonts()
