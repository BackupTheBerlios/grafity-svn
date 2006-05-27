__author__ = "Daniel Fragiadakis <dfragi@gmail.com>"
__revision__ = "$Id: resources.py 163 2006-04-07 15:29:08Z danielf $"

import sys
import os
import time, random, md5
import marshal

from dispatch import dispatcher
import metakit

class Storage(object):
    def __init__(self, filename=None):
        if filename is None:
            self.db = metakit.storage()
            self.undodb = metakit.storage()
        else:
            self.db = metakit.storage(filename, 1)
            if os.path.exists(filename+'.swp'):
                os.remove(filename+'.swp')
            self.undodb = metakit.storage(filename+'.swp', 1)

        self.filename = filename
        self.itemtypes = {}
        self.items = {}
        self.oplist = []
        self.action_name = None
        self._storage = self
        for name in dir(type(self)):
            attr = getattr(self, name)
            if isinstance(attr, Container):
                attr.name = name
                attr._storage = self
                self.itemtypes[name] = attr.cls

    def _create_id(self, *args):
        """Generates a unique ID.
        Any arguments only create more randomness.
        """
        t = long(time.time() * 1000)
        r = long(random.random()*100000000000000000L)
        data = str(t)+' '+str(r)+' '+str(args)
        data = md5.md5(data).hexdigest()
        return data

    def save(self, filename):
        self.db.save(open(filename, 'w'))

    def close(self):
        if self.filename is not None:
            os.remove(self.filename+'.swp')

    def __getitem__(self, oid):
        if oid == '':
            return None
        elif oid not in self.items:
            parent = None
            if ':' in oid:
                objid, theid = oid.split(':')
                itemtype = theid.split('/')[0]
                parent = self[objid]
                view = getattr(parent._row, itemtype)
            else:
                itemtype = oid.split('/')[0]
                view = self.db.view(itemtype)

            row = view[view.find(oid=oid)]
            if parent is None:
               obj = self.itemtypes[itemtype]()
            else:
                obj = getattr(parent, itemtype).cls()
            obj.initialize(row, view, parent)
            obj._storage = self

            self.items[oid] = obj
        return self.items[oid]

    def delete(self, obj):
        self._operation('del', obj.oid)

    def containers(self):
        for i in self.itemtypes:
            yield getattr(self, i)

    def _operation(self, opcode, *args):
        if opcode == 'add':
            itemtype, root = args
            oid = itemtype+'/'+self._create_id()
            if root is None:
                view = self.db.getas('%s[%s]'%(itemtype, self.itemtypes[itemtype]._attributes()))
            else:
                view = getattr(self[root]._row, itemtype)
                oid = root+':'+oid
            view.append(oid=oid)
            inv = ('del', oid)
#            dispatcher.send('add-object', self, oid)
        elif opcode == 'del':
            # find object
            oid, = args
            obj = self[oid]
            print >>sys.stderr, "authdel", obj, oid

            # get authorization
            if hasattr(obj, '_auth_del'):
                if not getattr(obj, '_auth_del')():
                    return

            # delete
            obj._row.deleted = True
            del self.items[oid]
            inv = ('und', obj._row.oid)

            # notify
            if hasattr(obj, '_notify_del'):
                getattr(obj, '_notify_del')()
        elif opcode == 'und':
            oid, = args
            obj = self[oid]
            obj._row.deleted = False
            inv = ('del', obj._row.oid)
#            dispatcher.send('add-object', self, oid)
        elif opcode == 'set':
            oid, name, value = args 
            obj = self[oid]

            # validation
            try:
                value = getattr(obj, '_validate__%s' % name)(value)
            except AttributeError, foo:
                pass
            except ValueError:
                return

            inv = ('set', oid, name, getattr(obj._row, name))
            old = getattr(obj, name)
            setattr(obj._row, name, value)
            new = getattr(obj, name)

            # notification
            if hasattr(obj, '_notify_set__%s' % name):
                getattr(obj, '_notify_set__%s' % name)(new, old)
        elif opcode == 'mod':
            oid, name, data, offset = args
            obj = self[oid]

            ind = obj._view.find(oid=obj.oid)
            old = obj._view.access(getattr(obj._view, name), ind, offset, len(data))
            obj._view.modify(getattr(obj._view, name), ind, data, offset)
            inv = ('mod', oid, name, old, offset)
#            dispatcher.send('mod-attr', self[oid], name, offset=offset, data=data, old=old)

        self.oplist.append(inv)

    def begin(self, name):
        self.action_name = name
        self.oplist = []

    def commit(self):
        uview = self.undodb.getas("undolist[name:S,ops:B]")
        uview.append(name=self.action_name, ops=marshal.dumps(self.oplist))
        if self.filename is not None:
            self.undodb.commit()
            self.db.commit()
        self.action_name = None

    def undo(self, _redo=False):
        uview = self.undodb.getas("undolist[name:S,ops:B]")
        rview = self.undodb.getas("redolist[name:S,ops:B]")

        if _redo:
            uview, rview = rview, uview

        name, oplist = uview[-1].name, marshal.loads(uview[-1].ops)

        self.oplist = []
        for oper in reversed(oplist):
            self._operation(*oper)

        uview.delete(len(uview)-1)

        rview.append(name=name, ops=marshal.dumps(self.oplist))
        if self.filename is not None:
            self.undodb.commit()
            self.db.commit()

    def redo(self):
        return self.undo(_redo=True)


class Attribute(object):
    def __init__(self, code):
        self.key = code

    def __get__(self, obj, cls):
        if obj is None:
            return self
#        if self.name not in Item.__dict__ and obj.deleted:
#            raise ValueError, 'object is deleted'
        self.obj = obj
        return self.decode(getattr(obj._row, self.name))

    def __set__(self, obj, value):
        if obj.deleted:
            raise ValueError, 'object is deleted'
        obj._storage._operation('set', obj.oid, self.name, self.encode(value))

    def _getcode(self):
        return self.name +':'+self.key
    code = property(_getcode)

    def encode(self, value):
        return value

    def decode(self, value):
        return value

    

class Attr(object):
    """Default attribute types"""

    class Text(Attribute):
        def __init__(self):
            Attribute.__init__(self, 'S')

    class Bytes(Attribute):
        def __init__(self):
            Attribute.__init__(self, 'B')

        def __get__(self, obj, cls):
            new = type(self)()
            new.__dict__.update(self.__dict__)
            new.obj = obj
            return new

#        def get_data(self):
#            return getattr(self.obj._row, self.name)
#        def set_data(self, value):
#            self.obj._storage._operation('set', self.obj.oid, self.name, value)
#        data = property(get_data, set_data)

        def get(self, offset, length):
            ind = self.obj._view.find(oid=self.obj.oid)
            return self.obj._view.access(getattr(self.obj._view, self.name), 
                                         ind, offset, length)

        def set(self, data, offset):
            self.obj._storage._operation('mod', self.obj.oid, self.name, data, offset)

        def __len__(self):
            return self.obj._view.itemsize(getattr(self.obj._view, self.name), 
                                           self.obj._view.find(oid=self.obj.oid))
                
    class Integer(Attribute):
        def __init__(self):
            Attribute.__init__(self, 'I')

    class ObjectRef(Attribute):
        def __init__(self):
            Attribute.__init__(self, 'S')

        def encode(self, value):
            return value.oid

        def decode(self, value):
            return self.obj._storage[value]

class Container(object):
    def __init__(self, cls):
        self.cls = cls

    def _getcode(self):
        return '%s[%s]' % (self.name, self.cls._attributes())
    code = property(_getcode)

    def __get__(self, obj, cls):
        self.obj = obj
        return self

    def create(self):
        if isinstance(self.obj, Storage):
            parent = None
        else:
            parent = self.obj.oid
        self.obj._storage._operation('add', self.name, parent)
        obj  = self[-1]
        obj._storage = self.obj._storage
        return obj

    def __getitem__(self, item):
        if isinstance(self.obj, Storage):
            try:
                return self.obj[self.obj.db.view(self.name).select(deleted=0)[item].oid]
            except ValueError:
                raise IndexError
        else:
            try:
                return self.obj._storage[getattr(self.obj._row, self.name).select(deleted=0)[item].oid]
            except ValueError:
                raise IndexError

    def __len__(self):
        if isinstance(self.obj, Storage):
            if len(self.obj.db.view(self.name)) == 0:
                return 0
            return len(self.obj.db.view(self.name).select(deleted=0))
        else:
            return len(getattr(self.obj._row, self.name))


class Item(object):
    class __metaclass__(type):
        def __new__(cls, name, bases, contents):
            c = type.__new__(cls, name, bases, contents)
            for key, value in contents.iteritems():
                if isinstance(value, (Attribute, Container)):
                    value.name = key
            return c

    @classmethod
    def _attributes(cls):
        st = ''
        for c in reversed(cls.__mro__):
            for key, attr in c.__dict__.iteritems():
                if isinstance(attr, (Attribute, Container)):
                    st += attr.code+','
        st = st[:-1]
        return st

    def initialize(self, row, view, obj):
        self._row = row
        self._view = view
        self._initialized = True
        self._parent = obj

    def __init__(self):
        self._initialized = False

#    def __init__(self, row):
#        self._row = row

    oid = Attribute('S')
    deleted = Attribute('I')

if __name__=='__main__':
#    import doctest
#    doctest.testmod()
    from grafity.base.utils import test
    test('squirrel.txt')
