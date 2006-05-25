#!/usr/bin/env python
import sys
from PyQt4 import QtCore, QtGui, uic
import code, rlcompleter
import traceback, operator
import keyword


class Interpreter (code.InteractiveInterpreter):
    def _showtraceback (self, type=None, exc=None, traceback=None):
        if type is None:
            type, value, traceback = sys.exc_info()
        if type == NameError:
            modulename = value.args[0].split()[1][1:-1]
            f_locals = traceback.tb_frame.f_locals
            f_globals = traceback.tb_frame.f_globals

            try:
                exec "import " + modulename in f_locals, f_globals
                exec traceback.tb_frame.f_code in f_locals, f_globals
            except NameError, exc:
                self.showtraceback(type, exc, traceback)
            else:
                print >>sys.stderr, "autoload: imported %s" % (modulename,)
        else:
            self.do_showtraceback()
           # excepthook(type, value, traceback)

    def showtraceback (self):
#        print "'Python error"
#        lines = traceback.format_exception_only (*sys.exc_info()[0:2])
        lines = traceback.format_exception (*sys.exc_info())
        for l in reduce (operator.add, lines).splitlines():
            print '# ' + l

    def showsyntaxerror (self, err):
        self.showtraceback ()


class Highlighter(QtCore.QObject):
    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        
        self.mappings = {}
        
    def addToDocument(self, doc):
        self.connect(doc, QtCore.SIGNAL("contentsChange(int, int, int)"), self.highlight)
    
    def addMapping(self, pattern, format):
        self.mappings[pattern] = format
    
    def highlight(self, position, removed, added):
        doc = self.sender()
    
        block = doc.findBlock(position)
        if not block.isValid():
            return
    
        endBlock = QtGui.QTextBlock()
        if added > removed:
            endBlock = doc.findBlock(position + added)
        else:
            endBlock = block
    
        while block.isValid() and not (endBlock < block):
            self.highlightBlock(block)
            block = block.next()
    
    def highlightBlock(self, block):
        layout = block.layout()
        text = block.text()
    
        overrides = []
    
        for pattern in self.mappings:
            expression = QtCore.QRegExp(pattern)
            i = text.indexOf(expression)
            while i >= 0:
                range = QtGui.QTextLayout.FormatRange()
                range.start = i
                range.length = expression.matchedLength()
                range.format = self.mappings[pattern]
                overrides.append(range)
    
                i = text.indexOf(expression, i + expression.matchedLength())
    
        layout.setAdditionalFormats(overrides)
        block.document().markContentsDirty(block.position(), block.length())
        

class ConsoleTextEdit(QtGui.QTextEdit):
    def __init__(self, *args):
        QtGui.QTextEdit.__init__(self, *args)

        self.locals = {}
        sys.stdout = self
        sys.stdin = self

        self.locals['self'] = self

        self.interpreter = Interpreter(self.locals)
        self.completer = rlcompleter.Completer()
        self.highlighter = Highlighter()

        num = QtGui.QTextCharFormat()
        num.setForeground(QtCore.Qt.darkGreen)
        self.highlighter.addMapping("#.*$", num)
 
        variableFormat = QtGui.QTextCharFormat()
        variableFormat.setFontWeight(QtGui.QFont.Bold)
        variableFormat.setForeground(QtCore.Qt.blue)
        self.highlighter.addMapping("\\b[A-Z_]+\\b", variableFormat)

        num = QtGui.QTextCharFormat()
        num.setForeground(QtCore.Qt.blue)
        self.highlighter.addMapping("\\b[0-9e\.]+\\b", num)

#        for kw in keyword.kwlist:
#            variableFormat = QtGui.QTextCharFormat()
#            variableFormat.setFontWeight(QtGui.QFont.Bold)
#            variableFormat.setForeground(QtCore.Qt.darkRed)
#            self.highlighter.addMapping("\\b%s\\b" % kw, variableFormat)

        self.highlighter.addToDocument(self.document())

        sys.ps1 = '>>> '
        sys.ps2 = '... '

        self.write(sys.ps1)

        self.last_lines = []
        self.history = []
        self.pointer = 0

    def __recall(self):
        y, x = self.position()
        for i in range(x-len(sys.ps1)):
            self.textCursor().deletePreviousChar()
        self.write(self.history[self.pointer])

    def keyPressEvent(self, e):
        text = e.text()
        key = e.key()
        y, x = self.position()

        if key in [QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Left]:
            if x > len(sys.ps1):
                QtGui.QTextEdit.keyPressEvent(self, e) 
        elif key in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            self.run()
        elif key == QtCore.Qt.Key_Up:
            if len(self.history):
                if self.pointer == 0:
                    self.pointer = len(self.history)
                self.pointer -= 1
                self.__recall()
        elif key == QtCore.Qt.Key_Down:
            if len(self.history):
                self.pointer += 1
                if self.pointer == len(self.history):
                    self.pointer = 0
                self.__recall()
        else:
            QtGui.QTextEdit.keyPressEvent(self, e) 

    def position(self):
        cb = self.textCursor().block()
        column = self.textCursor().position() - cb.position()
        b = self.document().begin()
        line = 0
        while b != self.document().end():
            if b == cb:
                break
            line += 1
            b = b.next()
        return line, column

    def write(self, text):
        self.insertPlainText(text)
        self.cursor_to_end()
        self.ensureCursorVisible()

    def cursor_to_end(self):
        self.textCursor().movePosition(QtGui.QTextCursor.End)

    def run(self):
        block = self.textCursor().block()
        line = str(block.text())[len(sys.ps1):]
        self.last_lines.append(line)
        self.history.append(line)
        self.pointer = 0
        source = '\n'.join(self.last_lines)
        print >>self
        if self.interpreter.runsource(source):
            self.write(sys.ps2)
        else:
            self.write(sys.ps1)
            self.last_lines = []

formclass, baseclass = uic.loadUiType("console.ui")
class Console(formclass, baseclass):
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
        self.setWindowFlags(self.windowFlags()&QtCore.Qt.Tool)
        self.setupUi(self)




def main():
    app = QtGui.QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
