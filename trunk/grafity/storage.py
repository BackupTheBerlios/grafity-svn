import sys
import time, random, md5
import marshal

import metakit

itemtypes = {}

class Storage(object):
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
        oid = self.operation('add', itemtype.__storename__)
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
            itemtype = oid.split('/')[0]
            self.items[oid] = itemtypes[itemtype](self.db.view(itemtype)[self.db.view(itemtype).find(oid=oid)])
        return self.items[oid]

    def undo(self):
        self.operation(undo=True, *self.undolist.pop())

    def redo(self):
        self.operation(undo=False, *self.redolist.pop())

    def operation(self, *args, **kwds):
        print 'executing operation', args
        oper = args
        opcode, args = args[0], args[1:]
        ret = None
        if opcode == 'add':
            itemtype, = args
            oid = itemtype+'/'+self.create_id()
            view = self.db.getas(itemtypes[itemtype].attributes())
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
        else:
            self.undolist.append(inv)
        return ret


class attribute(object):
    def __init__(self, code):
        self.code = code

    def __get__(self, obj, cls):
        return getattr(obj._row, self.name)

    def __set__(self, obj, value):
        if obj.deleted:
            raise ValueError, 'object is deleted'
        obj.storage.operation('set', obj.oid, self.name, value)
#        setattr(obj._row, self.name, value)
#        print >>sys.stderr, "set", obj.oid, obj.storage, self.name, value


class Item(object):
    class __metaclass__(type):
        def __new__(cls, name, bases, contents):
            c = type.__new__(cls, name, bases, contents)
            if '__storename__' in contents:
                itemtypes[contents['__storename__']] = c

            for key, value in contents.iteritems():
                if isinstance(value, attribute):
                    value.name = key
            return c

    @classmethod
    def attributes(cls):
        if not hasattr(cls, '__storename__'):
            return None
        st = cls.__storename__+'['
        for c in cls.__mro__:
            for key, attr in c.__dict__.iteritems():
                if isinstance(attr, attribute):
                    st += key+':'+attr.code+','
        st = st[:-1] + ']'
        return st

    def __init__(self, row):
        self._row = row

    oid = attribute('S')
    deleted = attribute('I')

#    __storename__='items'


class Folder(Item):
    __storename__ = 'folders'
    def __init__(self, row, *args):
        Item.__init__(self, row)

#        print self._rowref
    name = attribute('S')
    number = attribute('I')

if __name__=='__main__':
    store = Storage()
    f = store.create(Folder)
    f.name = '314'
    print f.number
    f.number = 200
    print f.number

    store.delete(f)

    store.save('/home/daniel/project.mk')
