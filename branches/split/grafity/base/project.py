import sys
import os

from dispatch import dispatcher

from grafity.base.storage import Storage, Container
from grafity.base.items import Folder
from grafity.base.worksheet import Worksheet

class Store(Storage):
    folders = Container(Folder)
    worksheets = Container(Worksheet)

class Project(object):
    """
    A grafity project.
    """
    def __init__(self, filename=None):
#        try:
#            os.remove('foo.db')
#        except:
#            pass
        self.store = Store(filename)
        dispatcher.connect(self.on_action)

        # top folder
        if len(self.store.folders) == 0:
            self.top = self.store.folders.create()
            self.top._project = self
            self.top.folder = self.top
            self.top.name = 'top'
        else:
            self.top = self.store.folders[0]
            self.top._project = self

        for c in self.store.containers():
            for item in c:
                item._project = self

        for f in self.store.folders:
            f._update_contents()


    def _new_object(self, container, name, parent=None, **kwds):
        if parent is None:
            parent = self.top

        new = container.create()
        new._project = self
        new.folder = parent
        new.name = name
        return new

    def new_folder(self, name, parent=None):
        return self._new_object(self.store.folders, name, parent)

    def new_worksheet(self, name, parent=None):
        return self._new_object(self.store.worksheets, name, parent)

    def on_action(self, arg1=None, arg2=None, signal=None, sender=None):
        pass

if __name__ == '__main__':
    p = Project()
    f = p.new_folder('foo')
    w = p.new_worksheet('bar', f)
    w = p.new_worksheet('bar', f)
    w = p.new_worksheet('bar', f)
    c = w.columns.create()
    c.name = 'baroof'
    print hasattr(w, 'babasdasd')
    print list(w.columns)
    print w.baroof
    c[:] = [1,2,3]
    w.columns[0][10] = 3
    w.baroof = [1,2,3,4,5,6,7,]
    w.printa = [2,3,4]
    print w.baroof
    print c, c.data
    print f
    print w.printa[33]
    w.printa[1240] = 4
    print w.printa[1230:1250]
