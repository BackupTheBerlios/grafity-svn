from grafity.base.squirrel import Item, Attr

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
#        old = self.folder
#        if self.folder is not None:
#            dispatcher.send('about-to-remove', self.folder, self)
#        dispatcher.send('about-to-add', folder, self)
        self._folder = folder
    folder = property(_get_folder, _set_folder)

    def _validate___folder(self, folder):
        return folder

    def _notify_set___folder(self, folder, old):
        if old is not None:
            old._update_contents()
            dispatcher.send('removed', old, self)
        if folder is not None:
            folder._update_contents()
            dispatcher.send('added', folder, self)
        

#    def _auth_del(self):
#        self.___folder = self.folder
#        print >>sys.stderr, 'roorororoo', self.folder, self._row._folder
#        print >>sys.stderr, 'roorororoo', self.name, self._row._name
#        return True

#    def _notify_del(self):
#        print >>sys.stderr, 'reeeeee', self.___folder
#        self.___folder._update_contents()
#        dispatcher.send('removed', self.___folder, self)
#        del self.___folder

    def __init__(self):
        Item.__init__(self)
#        dispatcher.connect(self._on_set_attr, signal='set-attr', sender=self)

    def __repr__(self):
        if self._initialized:
            return '<%s %s>' % (type(self).__name__, self.name,)
        else:
            return Item.__repr__(self)

#    def _on_set_attr(self, attr, value, old):
#        print >>sys.stderr, attr, value, old
#        if attr == 'name':
#            dispatcher.send('fullname-changed', self)
#        elif attr == 'folder' and self is not self._project.top:
#            if old is not None:
#                old._update_contents()
#                dispatcher.send('contents-changed', old)
#            self.folder._update_contents()
#            dispatcher.send('contents-changed', self.folder)

    def _get_fullname(self):
#        if not hasattr(self, '_project'):
#            return None
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

#    name = Attr.Text()

    def __init__(self, *args):
        self._contents = []
        ProjectItem.__init__(self, *args)
#        self._update_contents()

    def _update_contents(self):
        self._contents = []
        for c in self._storage.containers():
            for item in c:
                if not item.deleted and item.folder is self and item is not self._project.top:
                    self._contents.append(item)

    def contents(self):
        return self._contents
    
    def _on_set_attr(self, attr, value, old):
        ProjectItem._on_set_attr(self, attr, value, old)
        if attr == 'name' and self is not self._project.top:
            for child in self.contents():
                child._on_set_attr('name')

    def __getattr__(self, key):
#        try:
#           return object.__getattribute__(self, key)
#       except AttributeError:
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

