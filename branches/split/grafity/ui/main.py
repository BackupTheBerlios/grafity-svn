import sys

from PyQt4.Qt import *

def main():
    app = QApplication(sys.argv)
    pm = QPixmap("splash.png")
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


if __name__ == "__main__":
    main()
