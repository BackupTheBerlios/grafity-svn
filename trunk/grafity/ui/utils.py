import sys

from qt import *
from pkg_resources import resource_filename

from grafity.data import images


def getimage(name, cache={}):
    if name not in cache:
        resource, file = images[name]
        if resource:
            file = resource_filename('grafity', file)
        cache[name] = QPixmap(file)
    return cache[name]


class Page(object):
    def __init__(self, parent, *items, **kwds):
        self.win = QDialog(parent, 'page', True)

        layout = QVBoxLayout(self.win)

        self.widgets = {}

        for it in items:
            self.addgroup(it[0], it[1])

        line = QFrame(self.win)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        ok = QPushButton('OK', self.win)
        self.win.connect(ok, SIGNAL('clicked()'), self.win.close)
        self.win.connect(ok, SIGNAL('clicked()'), self.on_close)
        layout.addWidget(ok)

        for item, value in kwds.iteritems():
            self[item] = value
        
        self.callable = None

    def on_close(self):
        if self.callable:
            self.callable(self)
 
    def addgroup(self, name, items):
        self.win.layout().addWidget(QLabel('<b>'+name+'</b>', self.win))
        layout = QGridLayout(None, len(items)+1, 4, 2)

        layout.addColSpacing(0, 16)
        layout.addColSpacing(2, 12)
        layout.addRowSpacing(len(items), 12)

        for n, name in enumerate(items):
            if name[0] == '?':
                label = name[1:]
                widget = QCheckBox(label, self.win)
                layout.addMultiCellWidget(widget, n, n, 1, 3)
            elif name[0] == '#':
                label = name[1:]
                widget = QSpinBox(self.win)
                layout.addWidget(QLabel(label, self.win), n, 1)
                layout.addWidget(widget, n, 3)
            elif name[0] == '|':
                label = name[1:].split('|')[0]
                widget = QComboBox(self.win)
                widget.insertStrList(name[1:].split('|')[1:])
                layout.addWidget(QLabel(label, self.win), n, 1)
                layout.addWidget(widget, n, 3)
            else:
                label = name
                widget = QLineEdit(self.win)
                layout.addWidget(QLabel(label, self.win), n, 1)
                layout.addWidget(widget, n, 3)
            self.widgets[label] = widget
        self.win.layout().addLayout(layout)

    def __getitem__(self, key):
        if key in self.widgets:
            widget = self.widgets[key]
            if isinstance(widget, QLineEdit):
                return str(widget.text())
            elif isinstance(widget, QComboBox):
                return widget.currentItem()
            elif isinstance(widget, QCheckBox):
                return widget.isChecked()
            elif isinstance(widget, QSpinBox):
                return widget.value()
        else:
            raise IndexError

    def __setitem__(self, key, value):
        if key in self.widgets:
            widget = self.widgets[key]
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QComboBox):
                widget.setCurrentItem(value)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(value)
            elif isinstance(widget, QSpinBox):
                widget.setValue(value)
        else:
            raise IndexError

    def run_bg(self, callable):
        self.callable = callable
        self.win.setModal(False)
        self.win.show()

    def run(self):
        self.win.setModal(True)
        self.win.exec_loop()
        
def test_page():
        app = QApplication(sys.argv)
#        p = Page(None,
#            ('Termination Conditions', ['Tolerance (xsqr)', 'Tolerance (param)', '#Max Iterations']),
#            ('Weighting', ['|Weighting method|No Weighting|Statistical|Logarithmic Fit']),
#            ('Results', ['Worksheet', 'Extra properties', '?Save']),
#        )
#
#        p['Worksheet'] = 'fitresults'
#        p['Weighting method'] = 2
        p = Page(None,
            ('Limits', ['From', 'To']),
            **{'From': 0, 'To': 5}
        )
        p.run()
        print >>sys.stderr, p['Worksheet'], p['Save']

class EventHandler(QObject):
    def __init__(self, object, callback):
        QObject.__init__(self, object)
        self.object, self.callback = object, callback

    def eventFilter(self, object, event):
        return self.callback(event)

def connectevents(object, callback):
    object.installEventFilter(EventHandler (object, callback))


if __name__=='__main__':
    test_page()
