from grafit.project import project
from grafit.graph import GraphView
from grafit.utils import CompositeCommand
from sets import Set
from scipy import *
import os
from qt import *

def median_filter():
    aw = project.mainwin.workspace.activeWindow()
    if not isinstance(aw, GraphView):
        return
    datasets = aw.graph.selected_datasets()
    if len(datasets) == 0:
        return

    value, ok =  QInputDialog.getInteger ("Grafit", 'Points', 3, 1, 10000001, 2, aw)
    if ok:
        for d in datasets:
            x, y, indices = d.data()
            d.worksheet[d.coly][list(indices)] = signal.medfilt(y, value)

def wiener_filter():
    aw = project.mainwin.workspace.activeWindow()
    if not isinstance(aw, GraphView):
        return
    datasets = aw.graph.selected_datasets()
    if len(datasets) == 0:
        return

    value, ok =  QInputDialog.getInteger ("Grafit", 'Points', 3, 1, 10000001, 2, aw)
    if ok:
        for d in datasets:
            x, y, indices = d.data()
            d.worksheet[d.coly][list(indices)] = signal.wiener(y, value)

def derivative():
    aw = project.mainwin.workspace.activeWindow()
    if not isinstance(aw, GraphView):
        return
    datasets = aw.graph.selected_datasets()
    if len(datasets) == 0:
        return

    for d in datasets:
        x, y, indices = d.data()
        data = {}
        for xi, yi, i in zip(x, y, indices):
            data[xi] = (yi, i)

        x = sort(array(data.keys()))
        y = array([data[xi][0] for xi in x])
        indices = [data[xi][1] for xi in x]

        spl = interpolate.splrep(x, y, s=0)
        der = interpolate.splev(x, spl, der=1)
        project.undolist.begin_composite(CompositeCommand('Derivative'))
        try:
            d.worksheet[d.coly] = []
            d.worksheet[d.coly][indices] = der
        finally:
            project.undolist.end_composite()

def integral():
    aw = project.mainwin.workspace.activeWindow()
    if not isinstance(aw, GraphView):
        return
    datasets = aw.selected_datasets()
    if len(datasets) == 0:
        return

    for d in datasets:
        x, y, indices = d.data()
        data = {}
        for xi, yi, i in zip(x, y, indices):
            data[xi] = (yi, i)

        x = sort(array(data.keys()))
        y = array([data[xi][0] for xi in x])
        indices = [data[xi][1] for xi in x]

        spl = interpolate.splrep(x, y, s=0)
        res = array([interpolate.splint(x[0], xi, spl) for xi in x])
        project.undolist.begin_composite(CompositeCommand('Integral'))
        try:
            d.worksheet[d.coly] = []
            d.worksheet[d.coly][indices] = res
        finally:
            project.undolist.end_composite()

def interpolation(x, y, xnew):
    data = {}
    for xi, yi in zip(x, y):
        data[xi] = yi

    x = sort(data.keys())
    y = array([data[xi] for xi in x])

    spl = interpolate.splrep(x, y, s=0)
    return interpolate.splev(xnew, spl)


icon= '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x18\x00\x00\x00\x18\x08\x06\x00\x00\x00\xe0w=\xf8\x00\x00\x00\x06bKGD\x00\xff\x00\xff\x00\xff\xa0\xbd\xa7\x93\x00\x00\x01dIDATx\xda\xed\x94\xbfK\xc3@\x14\xc7\xbf&1`\xa9.\n\xa2\x08]\x1c\x94f\xd0\xc5\xc5MpQ\xff\x16G\xf5/\xf0OpW\xc1\x7f\xc3\xc1A\x10\x07\xa1\x06\xab\x8b\xb5\x15\x946-ik\xd3K\xee.\xcf!6j\xa8I\x7f\r\x0e\xfd\xc2\x1b\xde\xdd\xbb\xef\x87{\xdc;`\xac\xb1\x86\xd5D$\xa7Q{*\xd1]"\x1a(\xaer\xaf]iZt\xe1\xf2\xae\x88\xc5\xd94fR:\xd2S:\xa6S:\x9a\x8e\x07\xfb\x83\xa1l;\xa85\x19Z\x8c\x83\x88`\xb7\x82u\xe6\t<\x14\xab]\x01\xd1\x1b\x18[\xeb\x19T\x1bm\xb8\\\x06\xe1\t\xe8\x9a\x02M\xfd\x1d\x8e+\xd0b\x1cB\xfa\xc8\x97j8?\xda\x03\x00#\t`\x0206\x8d%T\xeamp!\xe1\t\x1f\x93\x9a\nU\xf9n\xad\xf4\t\x8e+\xc0<\x81\xfb\x82\x85\xb3\xc3\xdd\x8e\xb9\x99\x04\x08!\x1b+\x0b(\xdb\x0e\\.\xd1v9\xa4O\xf0\x84\x0f\x00\x10\xd2\x07\x172\xd1\xfc/@\x08Y[\x9e\x87U\x0f \x9a\x1a\x94vZg\xbeTqz\xb0\x13k\x1e\x07\x08!\xab\x999X\r\x16\xbc\x08U\x81\xf4\t\xb9\xe7\nN\xf6\xb7\x13\xcd{U\x16\x00=\x96jd\x16,:\xbe\xb8\xa6\xafy\xc9\x8er \xb3\x00\xe8&\xff\xd6\xb7\xb9\xd2c\x9d\xd9\xe9\xff\xcf|\x94\x80p\xca\xfb\xd5\xff\x02\xdc>\xbd\x0f\xfd\x9b\xc6^`\xc0sc\xc5\xeb\x13\xc5^\xd8\x98\x0em\x06\x99\x00\x00\x00\x00IEND\xaeB`\x82'

def qpixmap_from_data(data):
    tempfile = '/tmp/graphite-mimetex'
    f = open(tempfile, 'wb')
    f.write (data)
    f.close()
    pix = QPixmap(tempfile)
    os.remove(tempfile)
    return pix


def install():
    project.mainwin.insert_menu_item('&Analysis/Filters/Median filter...', median_filter) 
    project.mainwin.insert_menu_item('&Analysis/Filters/Wiener filter...', wiener_filter) 
    project.mainwin.insert_menu_item('&Analysis/Derivative', derivative)
    project.mainwin.insert_menu_item('&Analysis/Integral', integral)
    project.mainwin.menus['&Analysis'].changeItem(project.mainwin.menus['&Analysis'].idAt(0), QIconSet(qpixmap_from_data(icon)), 'Filters')

install() 
