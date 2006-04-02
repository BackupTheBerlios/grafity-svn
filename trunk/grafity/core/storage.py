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
            print 'foo!'
            os.remove(filename+'.swp')
        self.filename = filename
        self.undodb = metakit.storage(filename+'.swp', 1)
        self.items = {}
        self.oplist = []
        self.storage = self
        for name in dir(type(self)):
            attr = getattr(self, name)
            if isinstance(attr, Container):
                attr.name = name
                attr.storage = self
                itemtypes[name] = attr.cls

    def close(self):
        os.remove(self.filename+'.swp')

    def create_id(self, *args):
        """Generates a unique ID.
        Any arguments only create more randomness.
        """
        t = long(time.time() * 1000)
        r = long(random.random()*100000000000000000L)
        data = str(t)+' '+str(r)+' '+str(args)
        data = md5.md5(data).hexdigest()
        return data

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
                if obj is None:
                    obj = itemtypes[itemtype](row)
                else:
                    obj = getattr(obj, itemtype).cls(row)
                obj.storage  = self
            self.items[oid] = obj
        return self.items[oid]

    def operation(self, opcode, *args):
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
        self.db.commit()

    def begin_action(self, name):
        self.action_name = name
        self.oplist = []

    def end_action(self):
        uview = self.undodb.getas("undolist[name:S,ops:B]")
        uview.append(name=self.action_name, ops=marshal.dumps(self.oplist))
        self.undodb.commit()
        print self.oplist

    def undo(self, _redo=False):
        uview = self.undodb.getas("undolist[name:S,ops:B]")
        rview = self.undodb.getas("redolist[name:S,ops:B]")

        if _redo:
            uview, rview = rview, uview

        name, oplist = uview[-1].name, marshal.loads(uview[-1].ops)

        print 'undoing operation', name

        self.oplist = []
        for oper in reversed(oplist):
            self.operation(*oper)

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

class Container(object):
    def __init__(self, cls):
        self.cls = cls

    def get_code(self):
        return '%s[%s]' % (self.name, self.cls.attributes())
    code = property(get_code)

    def __get__(self, obj, cls):
        self.obj = obj
        return self

    def create(self):
        if isinstance(self.obj, Storage):
            parent = None
        else:
            parent = self.obj.oid
        self.obj.storage.operation('add', self.name, parent)
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
    def attributes(cls):
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
    from grafity.core.utils import test
    test('storage.txt')
