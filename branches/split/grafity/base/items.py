from grafity.core.storage import Item, Attr, Container

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
        if self._initialized:
            return '<%s %s>' % (type(self).__name__, self.name,)
        else:
            return Item.__repr__(self)

    def _on_set_attr(self, attr, value, old):
        if attr == 'name':
            dispatcher.send('fullname-changed', self)
        elif attr == 'folder' and self is not self._project.top:
            if old is not None:
                dispatcher.send('contents-changed', old)
            dispatcher.send('contents-changed', self.folder)

    def _get_fullname(self):
        return '.'.join(reversed([self.name] + [a.name for a in self.ancestors()]))
    fullname = property(_get_fullname)

    def ancestors(self):
        if self == self._project.top:
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
        for c in self._storage.containers():
            for item in c:
                if item.folder is self and item is not self._project.top:
                    yield item
    
    def _on_set_attr(self, attr, value, old):
        ProjectItem._on_set_attr(self, attr, value, old)
        if attr == 'name' and self is not self._project.top:
            for child in self.contents():
                child._on_set_attr('name')

