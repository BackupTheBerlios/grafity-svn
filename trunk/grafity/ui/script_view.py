import sys
sys.modules['grafity.ui.start'].splash.message('loading ui_script_view')

from qt import *
from qtext import QextScintilla, QextScintillaLexerPython

from grafity import Script
from grafity.ui.utils import getimage

class ScriptView(QVBox):
    def __init__(self, parent, mainwin, script):
        self.script = script
        QVBox.__init__(self, parent)
        self.resize(500, 300)
        self.setIcon(getimage('script'))

        split = QSplitter(QSplitter.Vertical, self)
        self.editor = QextScintilla(split)
        self.output = QTextBrowser(split)
        self.editor.setText(self.script.text)
        self.connect(self.editor, SIGNAL('textChanged()'), self.on_text_changed)

        lex = QextScintillaLexerPython()
        lex.setDefaultFont(QApplication.font())
        lex.setFont(QApplication.font(), -2)
        self.editor.setLexer(lex)

        self.script.project.connect('remove-item', self.on_project_remove_item)

    def on_run(self):
        self.script.run()

    def on_text_changed(self):
        self.script.text = unicode(self.editor.text())

    def on_project_remove_item(self, item):
        if item == self.script:
            self.close()
