import sys
import os
try:
   sys.modules['__main__'].splash.message('loading functions')
except:
    pass

import odr

from grafity.signals import HasSignals
from grafity.arrays import zeros, nan
from grafity.actions import action_from_methods, StopAction, action_from_methods2
from grafity.settings import DATADIR, USERDATADIR
from grafity.project import create_id
from data import scan_functions

def gen_flatten(s):
    try:
        iter(s)
    except TypeError:
        yield s
    else:
        for elem in s:
            for subelem in flatten(elem):
                yield subelem

def flatten(l):
    return list(gen_flatten(l))

def splitlist(seq, sizes):
    "Split list into list of lists with specified sizes"
    sumsizes = [sum(sizes[:i]) for i in range(len(sizes)+1)]
    slices = [sumsizes[i:i+2] for i in range(len(sizes))]
    return [list(seq)[s[0]:s[1]] for s in slices]



class FunctionsRegistry(HasSignals):
    def __init__(self, dirs):
        """Create a new function registry from a directory"""
        self.functions = []
        self.dirs = dirs
        self.rescan()

    def rescan(self):
        """Rescan the directory and check for changed functions"""
        names = []
        for f in scan_functions(self.dirs):
            try:
                func = Function()
                func.fromstring(open(f).read())
                func.filename = f
                names.append(func.name)
            except IOError, s:
                continue

            if func.name not in [f.name for f in self.functions]:
                self.functions.append(func)
                self.emit('added', func)
            else:
                for i, f in enumerate(self.functions):
                    if f.name == func.name:
                        self.functions[i] = func
                        self.emit('modified', func)

        for f in self:
            if f.name not in names:
                self.functions.remove(f)
                self.emit('removed', f)

#            self.functions.sort()

    def aaaaaaaascan(self, dirs=None):
        if dirs == None:
            dirs = self.dirs
        self.functions = []

        for dir in dirs:

            for f in os.listdir(dir):
                try:
                    func = Function()
                    func.fromstring(open(dir+'/'+f).read())
                    func.filename = dir + '/' + f
                except IOError, s:
                    continue

                self.functions.append(func)
#        self.functions.sort()

    def __getitem__(self, name):
        return [f for f in self.functions if f.name == name][0]

    def __contains__(self, name):
        return name in [f.name for f in self.functions]

    def __len__(self):
        return len(self.functions)

    def __iter__(self):
        for f in self.functions:
            yield(f)

    """emits 'modified'(function) : a function definition has been modified"""



class RegModel(HasSignals):
    def __init__(self, registry):
        self.registry = registry
        self.registry.connect('modified', self.mod)
        self.registry.connect('added', self.mod)
        self.registry.connect('removed', self.mod)

    def mod(self, *args, **kwds):
        self.emit('modified')

    def __len__(self):
        return len(self.registry)

#    def get(self, row, column):
#        return self.registry.functions[row].name
#
    def __getitem__(self, item):
        return self.registry.functions[item]

functions = []

def mod_property(name):
    def mod_get(self):
        return getattr(self, '_'+name)
    def mod_set(self, value):
        old = mod_get(self)
        setattr(self, '_'+name, value)
#        self.emit('modified', name, value, old)
    return property(mod_get, mod_set)

class FunctionInstance(HasSignals):
    def __init__(self, function, name):
        self.name = name
        self.function = function
        self.callable = self.function.to_module()
        self._parameters = [1.]*len(function.parameters)
        self.reg = True
        self._old = None
        self.__old = None

    def update(self):
        self.emit('modified')

    def move(self, x, y):
        if not hasattr(self.function, 'move'):
            return
        self.parameters = self.function.move(x, y, *self.parameters)
        self.emit('modified')

    def __call__(self, arg):
        try:
            return self.callable(arg, *self.parameters)
        except (ValueError, OverflowError):
            # If we don't catch these errors here,
            # odr segfaults on us!
            if hasattr(arg, '__len__'):
                return array([nan]*len(arg))
            else:
                return nan

    def set_reg(self, on):
        if self.reg == on:
            return
        elif on:
            self._old = self.__old 
        else:
            self.__old = self._parameters
        self.reg = on

    def set_parameters(self, p):
#        print >>sys.stderr, self, self._parameters, p
        if self._old is not None:
            old = self._old
            self._old = None
        else:
            old = self._parameters
        self._parameters = p
        if not self.reg:
            raise StopAction
        if old == p:
            # if the values haven't changed, don't bother
            raise StopAction
        return [old, p]
    def get_parameters(self):
        return self._parameters

    def redo_set_parameters(self, state):
        old, p = state
        self._parameters = p
        self.emit('modified')

    def undo_set_parameters(self, state):
        old, p = state
        self._parameters = old
        self.emit('modified')

    def combine_set_parameters(self, state, other):
#        print state, other
#        print 'attempt to combine', state, other
        return False

    set_parameters = action_from_methods('function-change-parameters', set_parameters, 
                                        undo_set_parameters, redo_set_parameters, combine=combine_set_parameters)
    parameters = property(get_parameters, set_parameters)


class FunctionSum(HasSignals):
    def __init__(self):
        self.terms = []

    def add(self, func, name):
        self.terms.append(FunctionInstance(registry[func], name))
        self.emit('add-term', self.terms[-1])
        self.terms[-1].connect('modified', lambda: self.emit('modified'), True)
        self.terms[-1].enabled = True

    def remove(self, ind):
        t = self.terms[ind]
        self.emit('remove-term', t)
        del self.terms[ind]

    def __getitem__(self, key):
        return self.terms[key]

    def __call__(self, arg):
        try:
            res = zeros(len(arg), 'd')
        except TypeError:
            res = 0.
        for func in self.terms:
            if func.enabled:
                res += func(arg)
        return res

    def fit(self, x, y, lock, maxiter):
        def __fitfunction(params, x):
            params = splitlist(params, [len(t.parameters) for t in self.terms])

            for p, t in zip(params, self.terms):
                t.parameters = p

            return self(x)

        def __itercall(niter, beta, wss, actred):
            message  = 'Fitting: Iteration %d, xsqr=%g, reduced xsqr=%g' % (niter, wss, actred)
            print >>sys.stderr, beta
            self.emit('status-message', message)
                
        model = odr.Model(__fitfunction)
        data = odr.RealData(x, y)
        initial = flatten(t.parameters for t in self.terms)

        odrobj = odr.ODR(data, model, beta0=initial,  ifixb=[not k for k in lock], 
                         partol=1e-100, sstol=1e-100, maxit=maxiter)
        odrobj.set_job(fit_type=2)
        odrobj.set_iprint(iter=3, iter_step=1, itercall=__itercall)
        for term in self.terms:
            term.set_reg(False)
        try:
            output = odrobj.run()
        finally:
            for term in self.terms:
                term.set_reg(True)

#        except:
#            raise
#            print >>sys.stderr, 'Fit den Vogel (but no problem)'
            

    
class Function(HasSignals):
    def __init__(self, name='', parameters=[], text='', extra=''):
        self._name = name
        self._parameters = parameters
        self._text = text
        self._extra = extra

    extra = mod_property('extra')
    text = mod_property('text')
    name = mod_property('name')
    parameters = mod_property('parameters')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Function %s(%s)>' % (self.name, ', '.join(self.parameters))

    def to_module(self):
        st = []
        st.append('from numarray import *\n')

        st.append('def func(x, '+', '.join(self.parameters)+'):\n')
        for line in self.text.splitlines():
            st.append('    '+line+'\n')
        st.append('    return y\n\n')
        st.append(self.extra+'\n')

        st = ''.join(st)

        ns = {}
        exec st in ns

        if 'move' in ns:
            self.move = ns['move']
        return ns['func']

    def save(self):
        file(self.filename, 'wb').write(self.tostring())

    def fromstring(self, s):
        self.name, param, self.text, self.extra = s.split('\n------\n')
        self.parameters = param.split(', ')

    def tostring(self):
        st = []
        st.append(self.name)
        st.append(', '.join(self.parameters))
        st.append(self.text)
        st.append(self.extra)
        st = '\n------\n'.join(st)
        return st

registry = FunctionsRegistry([os.path.join(DATADIR, 'data', 'functions'), 
                              os.path.join(USERDATADIR, 'functions')])
