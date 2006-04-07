import sys
import re
import time, random, socket, md5
import string

import metakit

from grafity.actions import action_from_methods, action_list, action_from_methods2, StopAction
from grafity.signals import HasSignals

# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/213761
def create_id(*args):
    """Generates a universally unique ID.
    Any arguments only create more randomness.
    """
    t = long(time.time() * 1000)
    r = long(random.random()*100000000000000000L)
    try:
        a = socket.gethostbyname(socket.gethostname())
    except:
        # if we can't get a network address, just imagine one
        a = random.random()*100000000000000000L
    data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
    data = md5.md5(data).hexdigest()
    return data

# The layout of the metakit project database.
# For each type of object (worksheet, graph etc) we call
# register_class(class, metakit_desc)
storage_desc = {}

def wrap(value, type):
    if type == 'V':
        return view_to_list(value)
    else:
        return value

def row_to_dict(view, row):
    return dict((prop.name, wrap(getattr(row, prop.name), prop.type)) for prop in view.structure())

def view_to_list(view):
    return list(row_to_dict(view, row) for row in view)

def fill(view, data):
    for row in data:
        addrow(view, row)

def addrow(view, row):
    attrs = dict((k, v) for k, v in row.iteritems() if not isinstance(v, list))
    subviews = dict((k, v) for k, v in row.iteritems() if isinstance(v, list))
    ind = view.append(**attrs)
    for name, value in subviews.iteritems():
        fill(getattr(view[ind], name), value)
    return ind

def metakit_to_dict(db):
    views = []
    sofar = []
    depth = 0
    for c in db.description():
        if c == '[': depth += 1
        elif c == ']': depth -= 1
        if depth == 0 and c == ',':
            views.append("".join(sofar))
            sofar[:] = []
        else:
            sofar.append(c)
    views.append("".join(sofar))

    di = dict(zip(views, [view_to_list(db.getas(v)) for v in views]))
    return di

def dict_to_metakit(di):
    db = metakit.storage()

    for viewdesc, data in di.iteritems():
        view = db.getas(viewdesc)
        fill(view, data)

    return db


def register_class(cls, desc):
    for w in string.whitespace:
        desc = desc.replace(w, '')
    storage_desc[cls] = desc

def wrap_attribute(name, signal=None):
    """Wrap a metakit column in a class attribute.
    
    If the wrapped attribute is an id of an object in project.items,
    it is wrapped with an attribute referencing the object.
    """
    def get_data(self):
        value = getattr(self.data, name)
        if hasattr(self, 'project') and value in self.project.items:
            value = self.project.items[value]
        return value

    def set_data(self, value):
        if hasattr(self, 'project') and hasattr(value, 'id') and value in self.project.items.values():
            value = value.id
        try:
            setattr(self.data, name, value)
        except TypeError:
            setattr(self.data, name, value.encode('utf-8'))
        if signal:
            self.emit(signal)
    return property(get_data, set_data)


class Item(HasSignals):
    """Base class for all items in a Project"""
    def __init__(self, project, name=None, parent=None, location=None):
        self.project = project

        action_list.disable()

        if location is None or isinstance(location, dict):
            # this is a new item, not present in the database 
            # create an entry for it
            self.view, self.data, self.id = project._create(type(self), location)

            # we have to handle creation of the top folder as a special case
            # we cannot specify its parent when we create it!
            if hasattr(self, '_isroot') and self._isroot:
                parent = self

            # parent defaults to top-level folder
            # (XXX: should this be the current folder?)
            if parent is None:
                parent = self.project.top

            if name is None:
                name = self.create_name(parent)
            if not self.check_name(name, parent):
                raise NameError

            # enter ourselves in the project dictionary
            self.project.items[self.id] = self

            # initialize
            self.name = name
            self.parent = parent.id
        else:
            # this is an item already present in the database
            self.view, self.data, self.id = location

            # enter ourselves in the project dictionary
            self.project.items[self.id] = self

        action_list.enable()


        # We have to emit the signal at the end
        # so the signal handlers can access wrapped attributes.
        # We can't emit in project.add()
        self.project.emit('add-item', self)


    def check_name(self, name, parent):
        if not re.match('^[a-zA-Z]\w*$', name):
            return False
        if isinstance(parent, Folder) and name in [i.name for i in parent.contents()]:
            return False
        return True

    def create_name(self, parent):
        for i in xrange(sys.maxint):
            name = self.default_name_prefix+str(i)
            if self.check_name(name, parent):
                return name

    def get_fullname(self):
        return '.'.join(reversed([self.name] + [a.name for a in self.ancestors()]))
    fullname = property(get_fullname)

    def ancestors(self):
        if self == self.project.top:
            return
        yield self.parent
        for f in self.parent.ancestors():
            yield f

    def set_parent(self, state, parent):
        state['new'], state['old'] = parent, self._parent
        oldparent = self._parent
        self._parent = parent
        self.emit('set-parent', self._parent)
        self.emit('fullname-changed', self.fullname, item=self)
        if not isinstance(oldparent, Folder):
            raise StopAction
    def undo_set_parent(self, state):
        self._parent = state['old']
        self.emit('set-parent', self._parent)
        self.emit('fullname-changed', self.fullname, item=self)
    def redo_set_parent(self, state):
        self._parent = state['new']
        self.emit('set-parent', parent)
        self.emit('fullname-changed', self.fullname, item=self)
    set_parent = action_from_methods2('object/set-parent', set_parent, undo_set_parent, redo=redo_set_parent)
    def get_parent(self):
        return self._parent
    parent = property(get_parent, set_parent)

    _parent = wrap_attribute('parent')

    def update_fullname(self):
        if isinstance(self, Folder):
            for item in list(self):
                item.emit('fullname-changed', item.fullname, item=item)
                item.update_fullname()

    def set_name(self, state, n):
        if not self.check_name(n, self.parent):
            raise StopAction
        state['new'], state['old'] = n, self._name
        self._name = n
        self.emit('rename', self._name, item=self)
        self.update_fullname()
    def undo_set_name(self, state):
        self._name = state['old']
        self.emit('rename', self._name, item=self)
        self.update_fullname()
    def redo_set_name(self, state):
        self._name = state['new']
        self.emit('rename', self._name, item=self)
        self.update_fullname()
    set_name = action_from_methods2('object/rename', set_name, undo_set_name, redo=redo_set_name)

    def get_name(self):
        return self._name
    name = property(get_name, set_name)

    _name = wrap_attribute('name')

    def todict(self):
        import mk
        return mk.row_to_dict(self.view, self.data)


    default_name_prefix = 'item'


class Folder(Item, HasSignals):
    def __init__(self, project, name=None, parent=None, location=None, _isroot=False):
        # we have to handle creation of the top folder as a special case
        # since we cannot specify its parent when we create it. 
        # see Item.__init__
        self._isroot = _isroot
        self.project = project
        Item.__init__(self, project, name, parent, location)

    def __items__(self):
        return dict((f.name, f) for f in self.contents())

    def contents(self):
        for desc in storage_desc.values():
            for row in self.project.db.getas(desc):
                if row.parent == self.id and row.id in self.project.items and row.id != self.id:
                    yield self.project.items[row.id]

    def all_subfolders(self):
        for item in self.subfolders():
            yield item
            for i in item.all_subfolders():
                yield i

    def subfolders(self):
        for item in self.contents():
            if isinstance(item, Folder):
                yield item

#    name = wrap_attribute('name')
    _parent = wrap_attribute('parent')

    def set_parent(self, parent):
        oldparent = self._parent
        self._parent = parent
        if oldparent != '' and isinstance(self.parent, Folder) and self in self.parent.ancestors():
            print >>sys.stderr, "are you kidding?"
            self._parent = oldparent
            return
        self.emit('set-parent', self._parent)
    def get_parent(self):
        return self._parent
    parent = property(get_parent, set_parent)


    default_name_prefix = 'folder'

    up = property(lambda self: self.parent)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError

    def __getitem__(self, key):
        cn = [i.name for i in self.contents()]
        ci = [i.id for i in self.contents()]

        if isinstance(key, int):
            return self.project.items[ci[key]]

        if key in cn:
            return self.project.items[ci[cn.index(key)]]
        else:
            raise KeyError, "item '%s' does not exist" % key

    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            return False

    def __repr__(self):
        return '<Folder %s>' % self.name

register_class(Folder, 'folders[name:S,id:S,parent:S]')

class Project(HasSignals):
    def __init__(self, filename=None):
        if isinstance(filename, unicode):
            filename = filename.encode(sys.getfilesystemencoding())
        self.filename = filename

        if self.filename is None:
            # We initially create an in-memory database.
            # When we save to a file, we will reopen the database from the file.
            self.db = metakit.storage()
        else:
            self.db = metakit.storage(self.filename, 1)
            self.cleanup()

        self._modified = False
        action_list.connect('added', self.on_action_added)

        self.items = {}
        self.deleted = {}

        # Create top folder.
        # - it must be created before all other items
        # - it must be created with _isroot=True, to set itself as its parent folder
        try:
            fv = self.db.getas(storage_desc[Folder])
            row = fv.select(name='top')[0]
            self.top = self.items[row.id] = Folder(self, location=(fv, row, row.id), _isroot=True)
        except IndexError:
            # can't find it in the database, create a new one.
            self.top = Folder(self, 'top', _isroot=True)

        self.here = self.top
        self.this = None

        # create objects
        for cls, desc in [(i, storage_desc[i]) for i in (Folder, grafity.worksheet.Worksheet, 
                                                                    grafity.script.Script, grafity.graph.Graph)]:
            view = self.db.getas(desc)
            for i, row in enumerate(view):
                if row.id != self.top.id:
                    if not row.id.startswith('-'):
                        self.items[row.id] = cls(self, location=(view, row, row.id))
                    else:
                        self.deleted[row.id] = cls(self, location=(view, row, row.id))

        action_list.disable()
        for item in (p for p in self.items.values() if isinstance(p, grafity.worksheet.Worksheet)):
            for c in item.columns:
                c.expr = c.expr
        action_list.enable()

    def on_action_added(self, action=None):
        self.modified = True

    def __repr__(self):
        if self.filename is not None:
            return "<grafity.Project '%s'>"% self.filename
        else:
            return "<grafity.Project (untitled)>"

    def cleanup(self):
        """Purge all deleted items from the database"""
        for cls, desc in storage_desc.iteritems():
            view = self.db.getas(desc)
            for i, row in enumerate(view):
                if row.id.startswith('-'):
                    view.delete(i)

    def _create(self, cls, location):
        """Create a new entry a new item of class `cls` in the database

        This method is called from the constructor of all `Item`-derived
        classes, if the item is not already in the database.
        Returns the view, row and id of the new item.
        """
        try:
            view = self.db.getas(storage_desc[cls])
        except KeyError:
            raise TypeError, "project cannot create an item of type '%s'" % cls

        id = create_id()
        if location is None:
            row = view.append(id=id)
        else:
            row = addrow(view, location)
            view[row].id = id
        data = view[row]

        return view, data, id

    # new ##################################

    def new(self, cls, *args, **kwds):
        obj = cls(self, *args, **kwds)
        self.items[obj.id] = obj
        # don't emit 'add-item' because it is emitted by Item.__init__
        return obj, obj

    def new_undo(self, obj):
        del self.items[obj.id]
        obj.id = '-'+obj.id
        self.deleted[obj.id] = obj
        self.emit('remove-item', obj)
        obj.parent.emit('modified')

    def new_redo(self, obj):
        del self.deleted[obj.id]
        obj.id = obj.id[1:]
        self.items[obj.id] = obj
        self.emit('add-item', obj)
        obj.parent.emit('modified')

    def new_cleanup(self, obj):
        if obj.id in self.deleted:
            del self.deleted[obj.id]
        obj.view.remove(obj.view.select(id=obj.id))

    new = action_from_methods('project_new', new, new_undo, new_redo, new_cleanup)

    # remove ###############################

    def remove(self, id):
        obj = self.items[id]
        ind = obj.view.find(id=id)

        if ind == -1:
            raise NameError
        else:
            del self.items[id]
            obj.id = '-'+obj.id 
            self.deleted[obj.id] = obj

        self.emit('remove-item', obj)
        return id

    def remove_undo(self, id):
        obj = self.deleted['-'+id]
        ind = obj.view.find(id=obj.id)

        del self.deleted[obj.id]
        obj.id = obj.id[1:]
        self.items[obj.id] = obj

        self.emit('add-item', obj)

    remove = action_from_methods('project_remove', remove, remove_undo)

    def commit(self):
        self.db.commit()
        self.modified = False

    def saveto(self, filename):
        if isinstance(filename, unicode):
            filename = filename.encode(sys.getfilesystemencoding())
        try:
            f = open(filename, 'wb')
            self.db.save(f)
        finally:
            f.close()
            self.modified = False

    def get_modified(self):
        return self._modified
    def set_modified(self, value):
        if value and not self._modified:
            self.emit('modified')
        elif self._modified and not value:
            self.emit('not-modified')
        self._modified = value
    modified = property(get_modified, set_modified)

# import only in order to register object types
import grafity.worksheet
import grafity.graph
import grafity.script
