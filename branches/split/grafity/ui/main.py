import sys

from PyQt4.Qt import *

def main():
    app = QApplication(sys.argv)
    pm = QPixmap("splash02.png")
    splash = QSplashScreen(pm)
    splash.show()

    from dispatch import dispatcher

    def messg(msg):
        splash.showMessage(msg, Qt.AlignLeft, Qt.white)
        app.processEvents()

    dispatcher.connect(messg, signal='splash-message')

    from grafity.ui.mainwin import MainWindow
    form = MainWindow()
    form.show()
    splash.finish(form)
    splash.close()
    app.exec_()

# splash01.png http://flickr.com/photos/sunrise/17563090/
# splash02.png http://flickr.com/photos/di1980/43594468/

if __name__ == "__main__":
    main()
