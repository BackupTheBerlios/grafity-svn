"""
grafity.core.storage
====================

Using ``factorial``
-------------------

This is an example text file in reStructuredText format.  First import
``factorial`` from the ``example`` module:

    >>> from grafity.core.storage import Storage, Container, Item, Attr

You define new classes derived from Item, like this

    >>> class Column(Item):
    ...     colname = Attr.Text()
    ... 
    >>> class Folder(Item):
    ...     name = Attr.Text()
    ...     number = Attr.Integer()
    ...     columns = Container(Column)
    ...     col2 = Container(Column)
    ...
    >>> class Meta(Item):
    ...     name = Attr.Text()
    ...     value = Attr.Text()
    ...

You define the database like this

    >>> class Store(Storage):
    ...     folders = Container(Folder)
    ...     meta = Container(Meta)
    ...


Create a store

    >>> st = Store('foo.db')

Create new objects

    >>> st.begin('foobar')
    >>> try:
    ...     f = st.folders.create()
    ...     f.name = 'foo'
    ...     m = st.meta.create()
    ...     m.name, m.value = 'foo', 'bar'
    ... finally:
    ...     st.commit()
    ... 
    >>> st.undo()
    >>> len(st.meta)
    0
    >>> st.redo()
    >>> len(st.meta)
    1
"""
import sys
import os
import time, random, md5
import marshal

from dispatch import dispatcher
import metakit

itemtypes = {}
class Storage(object):
    def __init__(self, filename):
        self.db = metakit.storage(filename, 1)
        if os.path.exists(filename+'.swp'):
            os.remove(filename+'.swp')
        self.filename = filename
        self.undodb = metakit.storage(filename+'.swp', 1)
        self.items = {}
        self.oplist = []
        self.action_name = None
        self.storage = self
        for name in dir(type(self)):
            attr = getattr(self, name)
            if isinstance(attr, Container):
                attr.name = name
                attr.storage = self
                itemtypes[name] = attr.cls

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
        os.remove(self.filename+'.swp')

    def __getitem__(self, oid):
        if oid not in self.items:
            obj = None
            for level in oid.split(':'):
                itemtype = level.split('/')[0]
                if obj is None:
                    view = self.db.view(itemtype)
                else:
                    view = getattr(obj._row, itemtype)
                row = view[view.find(oid=oid)]
                if obj is None:
                    obj = itemtypes[itemtype](row)
                else:
                    obj = getattr(obj, itemtype).cls(row)
                obj.storage  = self
            self.items[oid] = obj
        return self.items[oid]

    def delete(self, obj):
        self._operation('del', obj.oid)

    def _operation(self, opcode, *args):
        if opcode == 'add':
            itemtype, root = args
            oid = itemtype+'/'+self._create_id()
            if root is None:
                view = self.db.getas('%s[%s]'%(itemtype, itemtypes[itemtype]._attributes()))
            else:
                view = getattr(self[root]._row, itemtype)
                oid = root+':'+oid
            view.append(oid=oid)
            inv = ('del', oid)
            dispatcher.send('add-object', self, oid)
        elif opcode == 'del':
            oid, = args
            obj = self[oid]
            obj._row.deleted = True
            del self.items[oid]
            inv = ('und', obj._row.oid)
            dispatcher.send('delete-object', self, oid)
        elif opcode == 'und':
            oid, = args
            obj = self[oid]
            obj._row.deleted = False
            inv = ('del', obj._row.oid)
            dispatcher.send('add-object', self, oid)
        elif opcode == 'set':
            oid, name, value = args 
            inv = ('set', oid, name, getattr(self[oid]._row, name))
            setattr(self[oid]._row, name, value)
            dispatcher.send('set-attr', self[oid], name)
        self.oplist.append(inv)

    def begin(self, name):
        self.action_name = name
        self.oplist = []

    def commit(self):
        uview = self.undodb.getas("undolist[name:S,ops:B]")
        uview.append(name=self.action_name, ops=marshal.dumps(self.oplist))
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
        self.undodb.commit()

    def redo(self):
        return self.undo(_redo=True)


class Attribute(object):
    def __init__(self, code):
        self.key = code

    def __get__(self, obj, cls):
        if self.name not in Item.__dict__ and obj.deleted:
            raise ValueError, 'object is deleted'
        self.obj = obj
        return self.decode(getattr(obj._row, self.name))

    def __set__(self, obj, value):
        if obj.deleted:
            raise ValueError, 'object is deleted'
        obj.storage._operation('set', obj.oid, self.name, self.encode(value))

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

    class Integer(Attribute):
        def __init__(self):
            Attribute.__init__(self, 'I')

    class ObjectRef(Attribute):
        def __init__(self):
            Attribute.__init__(self, 'S')

        def encode(self, value):
            return value.oid

        def decode(self, value):
            return self.obj.storage[value]

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
        self.obj.storage._operation('add', self.name, parent)
        obj  = self[-1]
        obj.storage = self.obj.storage
        return obj

    def __getitem__(self, item):
        if isinstance(self.obj, Storage):
            return self.obj[self.obj.db.view(self.name).select(deleted=0)[item].oid]
        else:
            return self.obj.storage[getattr(self.obj._row, self.name).select(deleted=0)[item].oid]

    def __len__(self):
        if isinstance(self.obj, Storage):
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

    def __init__(self, row):
        self._row = row

    oid = Attribute('S')
    deleted = Attribute('I')

if __name__=='__main__':
    import doctest
    doctest.testmod()
#    from grafity.core.utils import test
#    test('storage.txt')
