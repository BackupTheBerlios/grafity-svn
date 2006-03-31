import sys
import time, random, md5
import marshal

import metakit

from grafity.signals import HasSignals

itemtypes = {}

class Storage(HasSignals):
    def __init__(self):
        self.db = metakit.storage()
        self.items = {}
        self.undolist = []
        self.redolist = []

    def create_id(self, *args):
        """Generates a unique ID.
        Any arguments only create more randomness.
        """
        t = long(time.time() * 1000)
        r = long(random.random()*100000000000000000L)
        data = str(t)+' '+str(r)+' '+str(args)
        data = md5.md5(data).hexdigest()
        return data

    def create(self, itemtype):
        oid = self.operation('add', itemtype.__storename__, None)
        obj = self[oid]
        obj.storage = self
        self.items[oid] = obj
        return obj

    def delete(self, obj):
        self.operation('del', obj.oid)

    def save(self, filename):
        self.db.save(open(filename, 'w'))

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
                obj = itemtypes[itemtype](row)
            self.items[oid] = obj
        return self.items[oid]

    def undo(self):
        self.operation(undo=True, *self.undolist.pop())

    def redo(self):
        self.operation(redo=True, *self.redolist.pop())

    def operation(self, *args, **kwds):
        oper = args
        opcode, args = args[0], args[1:]
        ret = None
        if opcode == 'add':
            itemtype, root = args
            oid = itemtype+'/'+self.create_id()
            if root is None:
                view = self.db.getas('%s[%s]'%(itemtype, itemtypes[itemtype].attributes()))
            else:
                view = getattr(self[root]._row, itemtype)
                oid = root+':'+oid
            view.append(oid=oid)
            inv = ('del', oid)
            ret = oid
        elif opcode == 'del':
            oid, = args
            obj = self[oid]
            obj._row.deleted = True
            del self.items[oid]
            inv = ('und', obj._row.oid)
        elif opcode == 'und':
            oid, = args
            obj = self[oid]
            obj._row.deleted = False
            inv = ('del', obj._row.oid)
        elif opcode == 'set':
            oid, name, value = args 
            inv = ('set', oid, name, getattr(self[oid]._row, name))
            setattr(self[oid]._row, name, value)

        if 'undo' in kwds and kwds['undo']:
            self.redolist.append(inv)
        elif 'redo' in kwds and kwds['redo']:
            self.undolist.append(inv)
        else:
            del self.redolist[:]
            self.undolist.append(inv)
        return ret


class Attribute(object):
    def __init__(self, code):
        self.key = code

    def __get__(self, obj, cls):
        if self.name not in Item.__dict__ and obj.deleted:
            raise ValueError, 'object is deleted'
        return getattr(obj._row, self.name)

    def __set__(self, obj, value):
        if obj.deleted:
            raise ValueError, 'object is deleted'
        obj.storage.operation('set', obj.oid, self.name, value)

    def get_code(self):
        return self.name +':'+self.key
    code = property(get_code)

class Attr(object):
    class String(Attribute):
        def __init__(self):
            Attribute.__init__(self, 'S')

    class Integer(Attribute):
        def __init__(self):
            Attribute.__init__(self, 'I')

    class ItemList(Attribute):
        def __init__(self, cls):
            self.cls = cls

        def get_code(self):
            return '%s[%s]' % (self.name, self.cls.attributes())
        code = property(get_code)

        def __get__(self, obj, cls):
            self.obj = obj
            return self

        def create(self):
            oid = self.obj.storage.operation('add', self.name, self.obj.oid)
            obj = self.obj.storage[oid]
            obj.storage = self.obj.storage
            return obj

        def __getitem__(self, item):
            return self.obj.storage[getattr(self.obj._row, self.name).select(deleted=0)[item].oid]

        def __len__(self):
            return len(getattr(self.obj._row, self.name))

class Item(HasSignals):
    class __metaclass__(type):
        def __new__(cls, name, bases, contents):
            c = type.__new__(cls, name, bases, contents)
            for key, value in contents.iteritems():
                if isinstance(value, Attribute):
                    value.name = key
            if '__storename__' in contents:
                itemtypes[contents['__storename__']] = c
            return c

    @classmethod
    def attributes(cls):
#        if not hasattr(cls, '__storename__'):
#            return None
#        st = cls.__storename__+'['
        st = ''
        for c in reversed(cls.__mro__):
            for key, attr in c.__dict__.iteritems():
                if isinstance(attr, Attribute):
                    st += attr.code+','
        st = st[:-1]
#        st = st[:-1] + ']'
        return st

    def __init__(self, row):
        self._row = row

    oid = Attribute('S')
    deleted = Attribute('I')


if __name__=='__main__':
    from grafity.core.utils import test
    test('storage.txt')