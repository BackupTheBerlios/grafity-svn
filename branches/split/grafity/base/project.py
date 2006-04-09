import sys
import os

from dispatch import dispatcher

from grafity.core.storage import Storage, Container
from grafity.base.items import Folder
from grafity.base.worksheet import Worksheet

class Store(Storage):
    folders = Container(Folder)
    worksheets = Container(Worksheet)

class Project(object):
    """
    A grafity project.
    """
    def __init__(self):
        try:
            os.remove('foo.db')
        except:
            pass
        filename = 'foo.db'
        self.store = Store(filename)
        dispatcher.connect(self.on_action)

        self.top = self.store.folders.create()
        self.top._project = self
        self.top.folder = self.top
        self.top.name = 'top'

    def new_folder(self, name, parent=None):
        if parent is None:
            parent = self.top

        new = self.store.folders.create()
        new._project = self
        new.folder = parent
        new.name = name
        return new

    def new_worksheet(self, name, parent=None):
        if parent is None:
            parent = self.top

        new = self.store.worksheets.create()
        new._project = self
        new.folder = parent
        new.name = name
        return new


    def on_action(self, arg1=None, arg2=None, signal=None, sender=None):
        print 'ACTION', sender, signal, arg1, arg2

if __name__ == '__main__':
    p = Project()
    f = p.new_folder('foo')
    w = p.new_worksheet('bar', f)
    c = w.columns.create()
    c[:] = [1,2,3]
    w.columns[0][10] = 3
    print c, c.data
    print f
