import sys
import time, random, socket, md5

import metakit


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


class Storage(object):
    def __init__(self):
        self.db = metakit.storage()

    def create(self, itemtype):
        view = self.db.getas(itemtype.attributes())
        rowref = view[view.append(oid=create_id())]
        return itemtype(rowref) 

    def save(self, filename):
        self.db.save(open(filename, 'w'))

class attribute(object):
    def __init__(self, code):
        self.code = code

    def __get__(self, obj, cls):
        return getattr(obj._row, self.name)

    def __set__(self, obj, value):
        setattr(obj._row, self.name, value)


class Item(object):
    class __metaclass__(type):
        def __new__(cls, name, bases, contents):
            if '__storename__' in contents:
                print >>sys.stderr, contents['__storename__']
            c = type.__new__(cls, name, bases, contents)
            print c, c.attributes()

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
#    __storename__='items'


class Folder(Item):
    __storename__ = 'folders'
    def __init__(self, row, *args):
        Item.__init__(self, row)
        print 'init', args

#        print self._rowref
    name = attribute('S')
    number = attribute('I')

store = Storage()
f = store.create(Folder)
f.name = '314'
print f.oid
print f.number
f.number = 200
print f.number
print f

store.save('/home/daniel/project.mk')
