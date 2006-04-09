from grafity.core.storage import Storage, Container, Item, Attr
from dispatch import dispatcher
import sys

class Column(Item):
    colname = Attr.Text()
    data = Attr.Bytes()

class Folder(Item):
    name = Attr.Text()
    number = Attr.Integer()
    columns = Container(Column)
    col2 = Container(Column)
    parent = Attr.ObjectRef()
    foo = Attr.Bytes()

class Meta(Item):
    name = Attr.Text()
    value = Attr.Text()

class Store(Storage):
    folders = Container(Folder)
    meta = Container(Meta)


class Project(object):
    def __init__(self):
        filename = 'foo.db'
        self.store = Store(filename)
        dispatcher.connect(self.on_action)

        self.store.begin('foobar')
        try:
            m = self.store.meta.create()
            m.name, m.value = 'foo', 'bar'
            f = self.store.folders.create()
            f.parent = m
        finally:
            self.store.commit()

        f = self.store.folders.create()
        f.foo.data = 'foobar'
        f.foo.set('OOF', 5)
        print f.foo.data
        print f.foo.get(3, 3)

    def on_action(self, arg, signal=None, sender=None):
        print 'ACTION', signal, sender, arg

p = Project()
