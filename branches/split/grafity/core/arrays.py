import struct
import sys

#import metakit
from numarray import *
from numarray.ieeespecial import nan, inf, isfinite, isnan
#from numpy.core import *
from grafity.core.storage import Attr

Error.setMode(all='ignore')

class VarOperation(object):
    def __init__(self, oper):
        self.oper = oper

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.oper, attr)

    def __call__(self, a, b=None):
        # if the argument is a sequence,
        # wrap the result in a varray, otherwise leave it alone
        if self.oper.arity == 1:
            try:
                len(a)
            except (ValueError, TypeError):
                return self.oper(a)
            else:
                return asvarray(self.oper(a))
        elif self.oper.arity == 2:
            try:
                length = min(len(a), len(b))
            except (ValueError, TypeError):
                return self.oper(a, b)
            else:
                return asvarray(self.oper(a[:length], b[:length]))

    def __repr__(self):
        return repr(self.oper).replace('UFunc', 'vUFunc')

# wrap all ufuncs with VarOperations
mod_ufuncs = dict([(k, VarOperation(v)) for k, v in ufunc._UFuncs.iteritems() if v.arity in (1,2)])
globals().update(mod_ufuncs)

def asvarray(*args, **kwds):
    arr = asarray(*args, **kwds)
    arr.__class__ = VArray
    return arr

def varray(*args, **kwds):
    arr = array(*args, **kwds)
    arr.__class__ = VArray
    return arr

class with_new_opers(object):
    def __add__(self, other): return add(self, asvarray(other)) 
    __radd__ = __add__
    def __sub__(self, other): return subtract(self, asvarray(other)) 
    def __rsub__(self, other): return subtract(asvarray(other), self) 
    def __mul__(self, other): return multiply(self, asvarray(other))
    __rmul__ = __mul__
    def __div__(self, other): return divide(self, asvarray(other)) 
    def __rdiv__(self, other): return divide(asvarray(other), self) 
    def __pow__(self,other): return power(self, asvarray(other)) 

# comparisons: should we have these?
#    def __eq__(self,other): return equal(self,other) 
#    def __ne__(self,other): return not_equal(self,asvarray(other)) 
#    def __lt__(self,other): return less(self,asvarray(other)) 
#    def __le__(self,other): return less_equal(self,asvarray(other)) 
#    def __gt__(self,other): 
#        print >>sys.stderr, self, other
#        return greater(self,asvarray(other)) 
#    def __ge__(self,other): return greater_equal(self,asvarray(other))
        
NumArray = type(array([0.]))

class VArray(with_new_opers, NumArray):
    pass

class MkArray(with_new_opers, Attr.Bytes):
    """
    a = MkArray(view, prop, col)

    Supports at least:

    a[n] = 134
    a[n:m] = 2
    a[n:m] = [3,4,5]    # sequence must have correct size

    a[n]      # if n is out of range, returns nan
    a[n:m]    # padded with nan's if out of range

    slices have n < m, no extended slices. Missing values (a[:n]) allowed.
    """    

    def __init__(self, *args):
        Attr.Bytes.__init__(self, *args)
#        self.view, self.prop, self.row = view, prop, row
#        self.start, self.end = start, end

    def __setitem__(self, key, value):
        """Set the column data.

        `key` can be:
            - an integer: change a single value
            - a slice: arr[i:j] change a range of values.
        `value` can be a scalar or a sequence.
        """

        if isinstance(key, int):
            start = key
            length = 1
        elif isinstance(key, slice):
            if key.start is None:
                start = 0
            else:
                start = key.start
            if key.stop is None:
                try:
                    length = len(value)
                except TypeError:
                    length = 1
            else:
                length = abs(key.start - key.stop)
        elif hasattr(key, '__getitem__'):
            #XXX: works, but...
            arr = self[:]
            arr[key] = value
            self[:] = arr
            return

        # adjust size
        if start > len(self):
            buf = array([nan]*(start-len(self)), type=Float64).tostring()
            self.set(buf, len(self)*8)
#            self.view.modify(self.prop, self.row, buf, len(self)*8)
        
        arr = asvarray(value, type=Float64)
        if arr.shape == ():
            arr = asvarray([value]*length, type=Float64)
        buf = arr.tostring()

        if isinstance(key, slice) and key.start is None and key.stop is None:
            self.data = buf
#            setattr(self.view[self.row], self.prop.name, buf)
        else:
            self.set(buf, start*8)
#            self.view.modify(self.prop, self.row, buf, start * 8)

    def __len__(self):
#        return self.view.itemsize(self.prop, self.row)/8
        return Attr.Bytes.__len__(self)/8

    def __getitem__(self, key):
        # integer and (non-extended) slice keys supported
        if isinstance(key, int):
            if key >= len(self):
                return nan
            if key <0:
                key = len(self)-key
            buf = self.get(key*8, 8)
#            buf = self.view.access(self.prop, self.row, key*8, 8)
            value = struct.unpack('d', buf)[0]
        elif isinstance(key, slice):
            if key.start is None:
                start = 0
            else:
                start = key.start
            if key.stop is None:
                stop = start+len(self)
            elif key.stop < 0:
                stop = len(self)+key.stop
            else:
                stop = key.stop
#            buf = self.view.access(self.prop, self.row, start*8, (stop-start)*8)
            buf = self.get(start*8, (stop-start)*8)
            value = fromstring(buf, type=Float64)
        elif hasattr(key, '__getitem__'):
#            buf = self.view.access(self.prop, self.row, 0, len(self)*8)
            buf = self.get(0, len(self)*8)
            value = fromstring(buf, type=Float64)
            if len(key) == 0:
                return array([], 'd')
            else:
                return value[key]
        return value

    def __repr__(self):
        return repr(self[:]).replace(repr(nan), '--')
