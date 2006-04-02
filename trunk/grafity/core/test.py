from grafity.core.storage import Storage, Container, Item, Attr
from dispatch import dispatcher

class Column(Item):
    colname = Attr.String()

class Folder(Item):
    name = Attr.String()
    number = Attr.Integer()
    columns = Container(Column)
    col2 = Container(Column)

class Meta(Item):
    name = Attr.String()
    value = Attr.String()

class Store(Storage):
    folders = Container(Folder)
    meta = Container(Meta)


class Project(object):
    def __init__(self):
        filename = 'foo.db'
        self.store = Store(filename)
        dispatcher.connect(self.on_action, sender=self.store)

        self.store.begin_action('foobar')

        try:
            m = self.store.meta.create()
            m.name, m.value = 'foo', 'bar'
        finally:
            self.store.end_action()

        print m.name, m.value
        self.store.undo()
        self.store.redo()
        self.store.close()

    def on_action(self, arg, signal=None, sender=None):
        print 'ACTION', signal, sender, arg

p = Project()
