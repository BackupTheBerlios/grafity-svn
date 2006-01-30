#!/usr/bin/env python
import os, sys
import logging
import traceback, time
from optparse import OptionParser

from pkg_resources import require, resource_filename
from qt import *

require('mimetex')

class GrafitSplash(QSplashScreen):
    def __init__(self, pixmap):
        QSplashScreen.__init__(self, pixmap)

    def drawContents(self, painter):
        font = painter.font()
        font.setPointSize(10)
        QSplashScreen.drawContents(self, painter)


class exception_form(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("exception_form")

        self.setSizeGripEnabled(1)

        exception_formLayout = QVBoxLayout(self,1,6,"exception_formLayout")
        exception_formLayout.setResizeMode(QLayout.Minimum)

        layout2 = QHBoxLayout(None,0,6,"layout2")

        self.pixmap = QLabel(self,"pixmap")
        self.pixmap.setScaledContents(1)
        layout2.addWidget(self.pixmap)

        self.label = QLabel(self,"label")
        self.label.setMinimumSize(QSize(380,0))
        layout2.addWidget(self.label)
        exception_formLayout.addLayout(layout2)

        layout2_2 = QHBoxLayout(None,0,6,"layout2_2")
        spacer2 = QSpacerItem(181,31,QSizePolicy.Expanding,QSizePolicy.Minimum)
        layout2_2.addItem(spacer2)

        self.closebtn = QPushButton(self,"closebtn")
        layout2_2.addWidget(self.closebtn)
        exception_formLayout.addLayout(layout2_2)

        self.languageChange()

        self.resize(QSize(391,58).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.closebtn,SIGNAL("clicked()"),self,SLOT("close()"))

    def languageChange(self):
        self.setCaption(self.__tr("Den Vogel"))
        self.label.setText(QString.null)
        self.closebtn.setText(self.__tr("OK!"))

    def __tr(self,s,c = None):
        return qApp.translate("exception_form",s,c)


class ErrorWindow(exception_form):
    def __init__(self, type, value, tback):
        exception_form.__init__(self, mainwin, 'error', True)
        self.label.setText("An error <b>(%s)</b> has occurred.<br><i>%s</i><br>This should not happen, please tell Daniel!" % (type, value))
        self.pixmap.setPixmap(getimage('vogel'))
        lines = ''.join(traceback.format_exception (type, value, tback))
        f = file('.grafity-birds', 'a')
        f.write('# bird at %s\n' % time.strftime("%d %b %Y %H:%M:%S"))
        f.write(lines)
        f.write('\n\n')

       
def excepthook(type, value, traceback):
    ErrorWindow(type, value, traceback).exec_loop()
    sys.__excepthook__(type, value, traceback)
    
sys.excepthook = excepthook

splash = None
mainwin = None

def getimage(name):
    return QPixmap(resource_filename('grafity', 'data/images/'+name+'.png'))

def main():
    global splash, mainwin

    parser = OptionParser()
    parser.add_option('-l', '--log', dest='log', help='Log program events')
    parser.add_option('-d', '--set-data-dir', dest='datadir', help='Set grafity data directory')
    options, args = parser.parse_args()

    if options.datadir is not None:
        configdir = os.path.normpath(os.path.abspath(os.path.dirname(sys.argv[0]))+'/../') + '/'
        open(configdir+'config.py', 'w').write('datadir="%s"'%options.datadir)
        sys.exit(0)

    if options.log is not None:
        for l in options.log.split(','):
            logging.getLogger(l).setLevel(logging.DEBUG)

    logging.basicConfig(format="%(asctime)s [%(name)s] %(message)s")

    app = QApplication(sys.argv)
    splash = GrafitSplash(getimage('logos/grafity'))
    splash.show()
    splash.message('')

    from grafity.ui.main import MainWindow

    splash.message('building user interface')

    mainwin = MainWindow()
    mainwin.app = app
    splash.finish(mainwin)
    app.setMainWidget(mainwin)
    mainwin.show()
    app.exec_loop()

if __name__=='__main__':
    main()
