# Various useful functions

import string
import sets
import sys
from qt import *

def itoa(x, base=10):
   isNegative = x < 0
   if isNegative:
      x = -x
   digits = []
   while x > 0:
      x, lastDigit = divmod(x, base)
      digits.append('0123456789abcdefghijklmnopqrstuvwxyz'[lastDigit])
   if isNegative:
      digits.append('-')
   digits.reverse()
   return ''.join(digits)


def alfmt (num):
    stri = ''
    if num == 0:
        return 'A'
    while num>0:
        (num,y) = divmod (num, 26)       
        stri = string.ascii_uppercase[y]+stri
    return stri

def gen_flatten(s):
    try:
        iter(s)
    except TypeError:
        yield s
    else:
        for elem in s:
            for subelem in flatten(elem):
                yield subelem

def flatten(l):
    return list(gen_flatten(l))

def splitlist(seq, sizes):
    "Split list into list of lists with specified sizes"
    sumsizes = [sum(sizes[:i]) for i in range(len(sizes)+1)]
    slices = [sumsizes[i:i+2] for i in range(len(sizes))]
    return [list(seq)[s[0]:s[1]] for s in slices]

class OtherSingleton(object):
    _state = {}

    def __new__(type):
        if not '_instance' in type.__dict__:
            type._instance = object.__new__(type)
        type._instance.__dict__ = type._state
        return type._instance

#http://www.python.org/2.2.2/descrintro.html
class Singleton(object):
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it
    def init(self, *args, **kwds):
        pass

def intersection (ml):
    """Intersection of lists"""
    tmp = {}
    for l in ml:
        for x in l:
            z = tmp.get(x, [])
            z.append(1)
            tmp[x] = z
    rslt = []
    for k,v in tmp.items():
        if len(v) == len(ml):
            rslt.append(k)
    return rslt

def all_the_same (sequence):
    return len (sets.Set(sequence)) == 1


class Observed (object):

    __observers = None

    def addobserver(self, observer):
        if not self.__observers:
            self.__observers = []
        self.__observers.append(observer)

    def removeobserver(self, observer):
        self.__observers.remove(observer)

    def emit(self, **event):
        for o in self.__observers or ():
            o(self, **event)

def pyset (elem, name, value):
    elem.set (name, repr (value))

def pyget (elem, name):
    return eval (elem.get (name), {"__builtins__": { 'True': True, 'False':False, 'None':None, 'nan':0.0 }})

class EventHandler (QObject):
    def __init__ (self, object, callback):
        QObject.__init__ (self, object)
        self.object, self.callback = object, callback

    def eventFilter (self, object, event):
        return self.callback (event)

def connectevents(object, callback):
    object.installEventFilter (EventHandler (object, callback))


class Page(object):
    def __init__(self, parent, *items):
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
        layout.addWidget(ok)
 
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

    def run(self):
        return self.win.exec_loop()
        
def test_page():
        p = Page(None,
            ('Termination Conditions', ['Tolerance (xsqr)', 'Tolerance (param)', '#Max Iterations']),
            ('Weighting', ['|Weighting method|No Weighting|Statistical|Logarithmic Fit']),
            ('Results', ['Worksheet', 'Extra properties', '?Save']),
        )

        p['Worksheet'] = 'fitresults'
        p.run()
        print >>sys.stderr, p['Worksheet'], p['Save']


class Settings(Singleton):
    def init(self):
        self.settings = QSettings()

    def __getitem__(self, key):
        value, success =  self.settings.readEntry(key)
        if success:
            return str(value)
        else:
            return None

    def __setitem__(self, key, value):
        return self.settings.writeEntry(key, value)

class AutoCommands(type):
    """For every method named _foo__init, a command class named is created
       which is referenced by class.foo___. Module.___class__foo___ also holds a 
       reference to the command in order for pickle to work. Class._commands
       holds a list of all the commands defined in the class.
       
       The command methods are taken from the class as follows:
            _foo__init   ->    __init__
            _foo__repr   ->    __repr__
            _foo__do     ->    do
            _foo__undo   ->    undo
    """
    def __init__(cls, name, bases, dct):
        type.__init__(cls, name, bases, dct)
        commands = []
        for n in [k[1:-6] for k in dct.keys() if k.startswith('_') and k.endswith('__init')]:
            c = cls.make_command(cls, n)
            setattr(cls, n+'___', c)    
            # this must be the same as the class name, or pickle will complain
            setattr(sys.modules[cls.__module__], n+'___', c)
            commands.append(c)
        setattr(cls, '_commands', commands)

    def make_command(self, cls, name):
        dct = {}
        for n in ['do', 'undo']:
            if '_'+name+'__'+n in cls.__dict__:
                dct[n] = cls.__dict__['_'+name+'__'+n]
        for n in ['init', 'repr']:
            if '_'+name+'__'+n in cls.__dict__:
                dct['__'+n+'__'] = cls.__dict__['_'+name+'__'+n]
        com = type(name+'___', (Command,), dct)
        # in the same module as the class
        com.__module__ = cls.__module__
        return com


class Command(object):
    def combine(self, command):
        raise TypeError, 'cannot combine'
    def tostring(self):
        return tostring(self.element)
    def fromstring(str):
        element = fromstring(str)
        comm = eval(element.tag)()
        comm.element = element
        return comm
    fromstring = staticmethod(fromstring)

    def addto(self, lst):
        lst.append(self)
        return self
    def register(self):
        project.undolist.append(self)
        return self

    def begin(self):
        project.undolist.begin_composite(self)
        return self

    def proceed(self):
        project.undolist.append(self)
        return self

    def end(self):
        project.undolist.end_composite(self)
        return self



class CompositeCommand(Command):
    def __init__(self, name=None, pixmap=None):
        self.commandlist = []
        self.name = name
#        self.pixmap = pixmap
        self.pixmap = None

    def do(self):
        for com in self.commandlist:
            com.do()

    def undo(self):
        for com in self.commandlist[::-1]:
            com.undo()

    def __repr__(self):
        if self.name is not None:
            return self.name
        else:
            return Command.__repr__(self)

    def add(self, command):
        if len(self.commandlist) == 0:
            self.commandlist.append(command)
            return
            
        try:
            combi = command.combine(self.commandlist[-1])
        except (TypeError, IndexError):
            self.add(self.commandlist.pop())
            self.commandlist.append(command)
        else:
            self.commandlist.pop()
            self.commandlist.append(combi)

from grafit.project import project
