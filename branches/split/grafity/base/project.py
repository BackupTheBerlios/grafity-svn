from grafity.core.storage import Storage, Item, Attr, Container
from dispatch import dispatcher
import sys
import os

class ProjectItem(Item):
    """
    The base class for all items in a project.
    
    Signals:
    --------
    fullname-changed: the item's name or the name of one of its ancestors has changed 
    """

    name = Attr.Text()
    folder = Attr.ObjectRef()

    def __init__(self):
        Item.__init__(self)
        dispatcher.connect(self._on_set_attr, signal='set-attr', sender=self)

    def __repr__(self):
        if self.initialized:
            return '<%s %s>' % (type(self).__name__, self.name,)
        else:
            return Item.__repr__(self)

    def _on_set_attr(self, attr, value, old):
        if attr == 'name':
            dispatcher.send('fullname-changed', self)
        elif attr == 'folder' and self is not self.project.top:
            if old is not None:
                dispatcher.send('contents-changed', old)
            dispatcher.send('contents-changed', self.folder)

    def _get_fullname(self):
        return '.'.join(reversed([self.name] + [a.name for a in self.ancestors()]))
    fullname = property(_get_fullname)

    def ancestors(self):
        if self == self.project.top:
            return
        yield self.folder
        for f in self.folder.ancestors():
            yield f


class Folder(ProjectItem):
    """
    A folder which contains other items.
    
    Signals:
    --------
    contents-changed: an item has been added or removed from the folder
    """

    name = Attr.Text()

    def contents(self):
        for c in self.storage.containers():
            for item in c:
                if item.folder is self and item is not self.project.top:
                    yield item
    
    def _on_set_attr(self, attr, value, old):
        ProjectItem._on_set_attr(self, attr, value, old)
        if attr == 'name' and self is not self.project.top:
            for child in self.contents():
                child._on_set_attr('name')


class Store(Storage):
    folders = Container(Folder)

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
        self.top.project = self
        self.top.folder = self.top
        self.top.name = 'top'

    def new_folder(self, name, parent=None):
        if parent is None:
            parent = self.top

        new = self.store.folders.create()
        new.project = self
        new.folder = parent
        new.name = name
        return new

    def on_action(self, arg1=None, arg2=None, signal=None, sender=None):
        print 'ACTION', sender, signal, arg1, arg2

if __name__ == '__main__':
    p = Project()
    f = p.new_folder('foo')
    f2 = p.new_folder('bar', f)
    f3 = p.new_folder('baz', f)
    f2.folder = f3
    print list(f2.ancestors())
    print f2.fullname
    print list(f.contents())
