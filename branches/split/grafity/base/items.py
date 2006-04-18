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

    _name = Attr.Text()
    _folder = Attr.ObjectRef()

    def _get_name(self):
        return self._name
    def _set_name(self, name):
        if name in list(p.name for p in self.folder.contents()):
            raise NameError
        self._name = name
    name = property(_get_name, _set_name)

    def _get_folder(self):
        return self._folder
    def _set_folder(self, folder):
        old = self.folder
        if self.folder is not None:
            dispatcher.send('about-to-remove', self.folder, self)
        dispatcher.send('about-to-add', folder, self)
        self._folder = folder
        if self.folder is not None:
            dispatcher.send('removed', old, self)
        dispatcher.send('added', folder, self)
    folder = property(_get_folder, _set_folder)

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
        print >>sys.stderr, "CONTENTS"
        for c in self._storage.containers():
            for item in c:
                if item.folder is self and item is not self._project.top:
                    yield item
    
    def _on_set_attr(self, attr, value, old):
        ProjectItem._on_set_attr(self, attr, value, old)
        if attr == 'name' and self is not self._project.top:
            for child in self.contents():
                child._on_set_attr('name')

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError

    def __getitem__(self, key):
        d = dict((i.name, i) for i in self.contents())

#        if isinstance(key, int):
#            return self.project.items[ci[key]]

        if key in d:
            return d[key]
        else:
            raise KeyError, "item '%s' does not exist" % key

    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            return False

