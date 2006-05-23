#!/usr/bin/env python
import sys
from PyQt4 import QtCore, QtGui, uic
import code, rlcompleter

class ConsoleTextEdit(QtGui.QTextEdit):
    def __init__(self, *args):
        QtGui.QTextEdit.__init__(self, *args)

        self.locals = {}
        sys.stdout = self
        sys.stdin = self
        sys.stderr = self

        self.interpreter = code.InteractiveInterpreter(self.locals)
        self.completer = rlcompleter.Completer()

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
class MainWindow(formclass, baseclass):
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
