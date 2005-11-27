from signals import HasSignals

def active_property(a,fget, fset=None, fdel=None, fdoc=None):
    if fset is not None:
        def replace_set(self, value):
            fset(self, value)
            self.emit('modified', a)
    return property(fget, replace_set, fdel, fdoc)
            
class o(HasSignals):
    def __init__(self):
        self.connect('modified', self.on_a)

    def on_a(self, val):
        print 'ona!', val

    def geta(self):
        return self._a
    def poutana(self, value):
        print 'ca'
        self._a = value
    a = active_property('a', geta, poutana)
    

c = o()
c.a = 123
print c.a
