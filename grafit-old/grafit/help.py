from qt import *

class HelpWidget(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        layout = QVBoxLayout(self)
        self.browser = QTextBrowser(self)
        self.browser.setText("<h1>Hello</h1>This is <a href='grafit'>grafit</a> help")
        layout.addWidget(self.browser)
