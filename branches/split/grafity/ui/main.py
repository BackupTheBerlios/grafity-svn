import sys

from PyQt4.Qt import *
from grafity.ui.forms import qtresources

def main():
    app = QApplication(sys.argv)
    pm = QPixmap(":/images/splash01.jpg")
    splash = QSplashScreen(pm)
    splash.show()

    QCoreApplication.setOrganizationName("Grafity Labs");
#    QCoreApplication.setOrganizationDomain("mysoft.com");
    QCoreApplication.setApplicationName("Grafity");

    from dispatch import dispatcher

    def messg(msg):
        splash.showMessage(msg, Qt.AlignLeft, Qt.white)
        app.processEvents()

    dispatcher.connect(messg, signal='splash-message')

    from grafity.ui.mdi import MainWindow

    dispatcher.send('splash-message', msg='Creating windows...')
    form = MainWindow()
    form.show()
    splash.finish(form)
    splash.close()
    app.exec_()

# splash01.jpg http://flickr.com/photos/sunrise/17563090/
# splash02.jpg http://flickr.com/photos/di1980/43594468/

if __name__ == "__main__":
    main()
