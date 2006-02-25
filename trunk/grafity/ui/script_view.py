import sys, os

sys.modules['grafity.ui.start'].splash.message('loading ui_script_view')
from qt import *
from qtext import QextScintilla

from grafity import Script


class ScriptView(QVBox):
    def __init__(self, parent, mainwin, script):
        QVBox.__init__(self, parent)
        self.editor = QextScintilla(self)
