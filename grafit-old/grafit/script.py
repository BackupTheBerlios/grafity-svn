import os, sys, traceback, operator, code
import re
import rlcompleter
import operator
import sets

#sys.modules['__main__'].splash_message('loading Console')

from qt import *
from qtext import QextScintilla,QextScintillaLexerPython, QextScintillaAPIs

from grafit.project import project

import compiler

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
        print "'Python error"
#        lines = traceback.format_exception_only (*sys.exc_info()[0:2])
        lines = traceback.format_exception (*sys.exc_info())
        for l in reduce (operator.add, lines).splitlines():
            print '# ' + l

    def showsyntaxerror (self, err):
        self.showtraceback ()

class Console (QextScintilla):
    def __init__(self, parent, locals=project.main_dict, log=''):
        QextScintilla.__init__(self, parent, 'Console')
        self.interpreter = Interpreter(locals)
        self.locals = locals

        self.resize (500, 300)

        lex = QextScintillaLexerPython()
        lex.setDefaultFont (QApplication.font())
        lex.setFont (QApplication.font(), -1)
        self.setLexer (lex)

#        self.SendScintilla(self.SCI_SETHSCROLLBAR, False)
        self.SendScintilla(self.SCI_SETSCROLLWIDTH, 100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        sys.stdout   = self
        sys.stdin    = self

        self.last_lines   = []

        self.more = False
        self.reading = False

        # history
        self.history = project.settings['/grafit/console/history']
        if self.history is None:
            self.history = []
        else:
            self.history = self.history.split('\n')
        self.pointer = 0

        sys.ps1 = '>>> '
        sys.ps2 = '... '

        self.clear ()
        self.write ('# Welcome to Grafit\n>>> ')

        self.completer = rlcompleter.Completer()

    # Simulate stdin, stdout, and stderr.
    def flush(self): pass

    def isatty(self): return 1

    def readline(self):
        self.reading = True
        self.__clearLine()
        self.moveCursorToEnd ()
        while self.reading:
            qApp.processOneEvent()
        if self.line.length() == 0:
            return '\n'
        else:
            return str(self.line) 

    def write(self, text):
        self.append (text)
        self.moveCursorToEnd ()

    def writelines(self, text):
        self.write (text)

    def moveCursorToEnd (self):
        last_line = self.lines() - 1
        last_line_len = self.lineLength (last_line)
        self.setCursorPosition (last_line, last_line_len+1)

    def fakeUser(self, lines):
        """
        Simulate a user: lines is a sequence of strings, (Python statements).
        """
        for line in lines:
#            self.line = QString(line.rstrip())
            self.write(line[:].rstrip())
            self.write('\n')
            self.run()

    def get_input(self, line=-2):
        return unicode(self.text(self.lines()+line)).split('\n')[0][4:self.lineLength(self.lines()+line)]
            
    def run(self):
        """
        Append the last line to the history list, let the interpreter execute
        the last line(s), and clean up accounting for the interpreter results:
        (1) the interpreter succeeds
        (2) the interpreter fails, finds no errors and wants more line(s)
        (3) the interpreter fails, finds errors and writes them to sys.stderr
        """
        line = self.get_input()
        self.pointer = 0
        self.history.append(line)
        self.last_lines.append(line)
        source = '\n'.join(self.last_lines).replace('{', 'array([').replace('}', '])')
        source = re.sub('\$(?P<name>[0-9a-zA-Z_]*)', 'project[\'\g<name>\']', source)

#        patt = r'\b%s\.%s\b' % (self.worksheet.name, name)
#        repl = '%s.%s' % (self.worksheet.name, newname)
#        source = re.sub ($<S-F1>patt, repl, source)

        protected = ['project', 'mainwin']

        class ForbiddenAssignmentError (Exception): pass

        class Walker:
            def visitAssign(self, node):
                var = node.asList()[0]
                if len(var)==2 and isinstance (var[0], str) and var[0] in protected:
                     print "# Assignment to %s not allowed" % var[0]
                     raise ForbiddenAssignmentError
                    
        walker = Walker()

        forbidden_assign = False
        try:
            tree = compiler.parse (source) 
            compiler.walk (tree, walker)
        except ForbiddenAssignmentError:
            forbidden_assign = True
        except:
            pass

        if not forbidden_assign:
            self.more = self.interpreter.runsource(source)

        if self.more:
            self.write(sys.ps2)
        else:
            self.write(sys.ps1)
            self.last_lines = []
        self.moveCursorToEnd()
        
    def __insertText(self, text):
        """
        Insert text at the current cursor position.
        """
        y, x = self.getCursorPosition()
        self.insertAt(text, y, x)
        self.setCursorPosition(y, x + len(text))

    def complete(self):
        line = self.get_input(-1)
        line = re.search(r'([\w\.]*)$', line).group(0)
        try:
            self.completer.complete(line, 0)
        except:
            pass
        else:
            self.completer.matches = list(sets.Set(self.completer.matches))
            self.completer.matches = [w for w in self.completer.matches if not w.startswith('_')]
            self.completer.matches.sort()
            if len(line) >= 4 and len(self.completer.matches) > 0:
                self.SendScintilla(self.SCI_AUTOCSHOW, len(line), str(' '.join(self.completer.matches)))

    def autoCompletionActive(self):
        return self.SendScintilla(self.SCI_AUTOCACTIVE)

    def keyPressEvent(self, e):
        """
        Handle user input a key at a time.
        """

        text  = e.text()
        key   = e.key()
        ascii = e.ascii()
        y, x = self.getCursorPosition()

        if self.autoCompletionActive():
            return QextScintilla.keyPressEvent(self, e)

        if text.length() and ascii>=32 and ascii<127:
            QextScintilla.keyPressEvent(self, e)
            self.complete()
            return

        if e.state() & Qt.ControlButton or e.state() & Qt.ShiftButton:
            e.ignore()
            return

        if key == Qt.Key_Backspace:
            if x > 4:
                QextScintilla.keyPressEvent (self, e)
        elif key == Qt.Key_Delete:
            QextScintilla.keyPressEvent (self, e)
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            if self.autoCompletionActive():
                QextScintilla.keyPressEvent(self, e)
            else:
                if self.reading:
                    self.reading = False
                else:
                    self.write('\n')
                    self.run()
        elif key == Qt.Key_Tab:
            self.complete()
#            self.__insertText(text)
        elif key == Qt.Key_Left:
            if x > 4:
                QextScintilla.keyPressEvent (self, e)
        elif key == Qt.Key_Right:
            QextScintilla.keyPressEvent (self, e)
        elif key == Qt.Key_Home:
            self.setCursorPosition(y, 4)
        elif key == Qt.Key_End:
            QextScintilla.keyPressEvent (self, e)
        elif key == Qt.Key_Up:
            if len(self.history):
                if self.pointer == 0:
                    self.pointer = len(self.history)
                self.pointer -= 1
                self.__recall()
        elif key == Qt.Key_Down:
            if len(self.history):
                self.pointer += 1
                if self.pointer == len(self.history):
                    self.pointer = 0
                self.__recall()
        else:
            e.ignore()

    def __recall(self):
        """
        Display the current item from the command history.
        """
        y, x = self.getCursorPosition()
        self.setCursorPosition(y, 4)
        self.setSelection(y, 4, y, self.lineLength(y))
        self.removeSelectedText()
        self.__insertText(self.history[self.pointer])

        
    def focusNextPrevChild(self, next):
        """
        Suppress tabbing to the next window in multi-line commands. 
        """
        if next and self.more:
            return 0
        return QextScintilla.focusNextPrevChild(self, next)

    def mousePressEvent(self, e):
        """
        Keep the cursor after the last prompt.
        """
        if e.button() == Qt.LeftButton:
            self.moveCursorToEnd ()
        return

    def eventFilter(self, obj, event):
        ret = QextScintilla.eventFilter(self, obj, event)
        if event.type() == QEvent.MouseButtonPress:
            self.mousePressEvent(event)
            return False
        return ret

