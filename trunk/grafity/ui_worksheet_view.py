from qt import *
from qttable import *
from grafity.arrays import clip, nan, arange, log10

from grafity import Worksheet

class WorksheetView(QTabWidget):
    def __init__(self, parent, mainwin, worksheet):
        QTabWidget.__init__(self, parent)
        self.mainwin, self.worskheet = mainwin, worksheet

        self.setTabShape(self.Triangular)
        self.setTabPosition(self.Bottom)

        self.table = QTable(self)
        self.addTab(self.table, 'worksheet')
