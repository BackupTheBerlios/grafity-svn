"""
Signal / Slot framework
"""

import sys
import weakref
try:
    import wx
except ImportError:
    pass

class Slot(object):
    """
    A Slot wraps a function or method, using a weak reference.
    We have to work around the fact that:

        >>> obj.method is obj.method
        False

    So if we are wrapping a object's method, we store a weakref to the 
    _object_ and the method name.

    Slots compare equal to the method/function they wrap, so that:

        >>> func in [Slot(func)]
        True

    Slots "expire" when the function or object wrapped is garbage-collected.
    Test for expiration with is_expired().
    """ 

    def __init__(self, call, keepref=False):
        if hasattr(call, 'im_self'):
            self.method = True
            if keepref:
                self.obj = call.im_self
            else:
                self.obj = weakref.proxy(call.im_self)#, self.destroyed)
            self.name = call.__name__
        else:
            self.method = False
            if keepref:
                self.call = call
            else:
                self.call = weakref.proxy(call)#, self.destroyed)

    def __call__(self, *args, **kwds):
        if self.method:
            return getattr(self.obj, self.name)(*args, **kwds)
        else:
            return self.call(*args, **kwds)

    def __eq__(self, other):
        # We want slots to compare equal if they reference the same function/method
        if isinstance(other, Slot):
            if self.method and not other.method or not self.method and other.method:
                return False
            elif self.method and other.method:
                return self.obj == other.obj and self.name == other.name
            else:
                return self.call == other.call
        # We also want slots to compare equal _to_ the function or method they reference
        else:
            if self.method:
                if hasattr(other, 'im_self'):
                    return self.obj in weakref.getweakrefs(other.im_self) and self.name == other.__name__ 
                else: # `other` is not a method
                    return False
            else:
                return self.call in weakref.getweakrefs(other)

    def is_expired(self):
        """
        Tests if the slot has expired 
        (i.e. if the function or method has been deleted).
        """
        try:
            _ = self == self  # This calls __eq__ and fails if the slot has expired
            return False
        except ReferenceError:
            return True
        
class HasSignals(object):
    """Base class for an object that can emit signals"""

    def connect(self, signal, slot, keepref=False):
        """
        Connect a signal to a slot.  'signal' is a string, `slot` is any callable.
        """
#        print "CONNECT: ", self, signal, slot
        if not isinstance(signal, basestring) and hasattr(signal, '__len__'):
            return [self.connect(sig, slot) for sig in signal]
        if not hasattr(self, '_signals'):
            self._signals = {}
        if signal not in self._signals:
            self._signals[signal] = []
        self._signals[signal].append(Slot(slot, keepref))

    def disconnect(self, signal, slot):
        """
        Disconnect a slot from a signal.
        """
#        print "DISCONNECT: ", self, signal, slot
        if not hasattr(self, '_signals'):
            raise NameError, "TODO"
        if signal not in self._signals:
            raise NameError, "TODO"
        try:
            if slot not in self._signals[signal]:
                raise NameError, "TODO"
            self._signals[signal].remove(slot)
        except ReferenceError:
            pass

    def emit(self, signal, *args, **kwds):
        """
        Emit a signal. All slots connected to the signal will be called.
        *args and **kwds are passed to the slot unmodified.
        """
#        print >>sys.stderr, "SIGNAL:", self, "emitted", signal
        if not hasattr(self, '_signals'):
            return []
        if signal not in self._signals:
            return []

        results = []
        for slot in self._signals[signal]:
            # Lazy handling of expired slots.
            # We don't care about them until they are called,
            # then we remove them from the slots list.
            try:
                results.append(slot(*args, **kwds))
            except (ReferenceError, wx.PyDeadObjectError):
                # We can't do self._signals[signal].remove(slot) because that calls slot.__eq__
                # and raises another ReferenceError. So we might as well remove all expired slots.
#                print >>sys.stderr, "garbage collected slot", slot
                self._signals[signal] = [s for s in self._signals[signal] if not s.is_expired()]
        return results
