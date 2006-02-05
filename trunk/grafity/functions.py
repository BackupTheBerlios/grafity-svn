import sys
import os
import Numeric

from pkg_resources import resource_string

from grafity.signals import HasSignals
from grafity.arrays import zeros, nan, array, log10
from grafity.actions import action_from_methods, StopAction, action_from_methods2
from grafity.settings import USERDATADIR
from grafity.project import create_id, wrap_attribute
from grafity.mpfit import mpfit
from grafity.data import scan_functions

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
        for res, f in scan_functions(self.dirs):
            try:
                func = Function()
                if res:
                    func.fromstring(resource_string('grafity', f))
                    func.filename = None
                else:
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


class FunctionInstance(HasSignals):
    """
    functions [
        id:S, func:S, name:S,
        params:S, lock:S, use:I
    ],
    """
    def __init__(self, data):
        self.data = data
        self.function = registry[self.data.func]
        self._old = None
        self.__old = None
        self.reg = False

    name = wrap_attribute('name')
    id = wrap_attribute('id')
    enabled = wrap_attribute('use')

    @staticmethod
    def new_row(function_name, name):
        func = registry[function_name]
        nparams = len(func.parameters)
        return {'id': create_id(), 
                'func': function_name, 
                'name': name, 
                'params': str([1.]*nparams),
                'lock': str([False]*nparams),
                'use': True }

    def move(self, x, y):
        if not hasattr(self.function, 'move'):
            return
        self.parameters = self.function.move(x, y, *self.parameters)
        self.emit('modified')

    def __call__(self, arg):
        try:
            return self.function(arg, *self.parameters)
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

    def _get_parameters(self):
        try:
            return eval(self.data.params)
        except SyntaxError:
            return [1.]*len(self.function.parameters)
    def _set_parameters(self, params):
        self.data.params = str(params)
    _parameters = property(_get_parameters, _set_parameters)


class FunctionSum(HasSignals):
    def __init__(self, data):
        self.data = data
        self.terms = []
        for row in data:
            if row.func in registry and not row.id.startswith('-'):
                self.terms.append(FunctionInstance(row))
                self.terms[-1].connect('modified', self.on_term_modified)

    def add(self, state, func, name):
        print >>sys.stderr, FunctionInstance.new_row(func, name)
        ind = self.data.append(**FunctionInstance.new_row(func, name))
        self.terms.append(FunctionInstance(self.data[ind]))
        self.emit('add-term', self.terms[-1])
        self.terms[-1].connect('modified', self.on_term_modified)
        state['term'] = terms[-1]
    def undo_add(self, state):
        term = state['term']
        term.data.id = '-'+term.data.id
        self.terms.remove(term)
        term.disconnect('modified', self.on_term_modified)
        self.emit('remove-term', term)
    def redo_add(self, state):
        term = state['term']
        self.terms.append(term)
        term.connect('modified', self.on_term_modified)
        term.data.id = term.data.id[1:]
        self.emit('add-term', term)

    add = action_from_methods2('graph/add-function-term', add, undo_add, redo=redo_add)

    def on_term_modified(self):
        self.emit('modified')

    def remove(self, state, ind):
        t = self.terms[ind]
        self.emit('remove-term', t)
        del self.terms[ind]
        t.id = '-'+t.id
        t.disconnect('modified', self.on_term_modified)
        state['term'] = t

    undo_remove = redo_add
    redo_remove = undo_add
    remove = action_from_methods2('graph/remove-function-term', remove, undo_remove, redo=redo_remove)


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

    def fit(self, xx, yy, lock, maxiter):
        def __fitfunction(params, fjac=None):
            params = splitlist(params, [len(t.parameters) for t in self.terms if t.enabled])
            for p, t in zip(params, self.terms):
                t.parameters = p
            ret = Numeric.array(list(yy-self(xx)))
            return [0, ret]

        def __itercall(myfunct, p, iter, fnorm, functkw=None, parinfo=None, quiet=0, dof=None):
            message = "Fitting: iteration %d, reduced xsqr=%g"%(iter, fnorm)
            self.emit('status-message', message)
                
        parinfo = []
        n = 0
        for term in self.terms:
            if term.enabled:
                for par in term.parameters:
                    info =  { 'value': par,
                              'fixed': lock[n],
                              'limited': [True, True],
                              'limits': [-10, 10], }
                    parinfo.append(info)
                    n += 1

        for term in self.terms:
            term.set_reg(False)
        try:
            fit = mpfit(__fitfunction, parinfo=parinfo, iterfunct=__itercall)
            print >>sys.stderr, "Fit done", fit.status, fit.fnorm, fit.covar, fit.errmsg, fit.nfev, fit.niter, fit.perror
        finally:
            for term in self.terms:
                term.set_reg(True)

class Function(HasSignals):
    def __init__(self, name='', parameters=[], text='', extra=''):
        self.name = name
        self.parameters = parameters
        self.text = text
        self.extra = extra
        self.desc = ''
        self.tex = ''

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Function %s(%s)>' % (self.name, ', '.join(self.parameters))

    def __call__(self, *args):
        return self.callable(*args)

    def get_callable(self):
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
        if self.filename is not None:
            file(self.filename, 'wb').write(self.tostring())

    def fromstring(self, s):
        self.name, self.desc, param, self.text, self.tex, self.extra = s.split('\n------\n')
        if '/' in self.name:
            self.category, self.short = self.name.split('/')
        else:
            self.category, self.short = None, self.name
        self.parameters = param.split(', ')
        self.callable = self.get_callable()

    def tostring(self):
        st = []
        st.append(self.name)
        st.append(self.desc)
        st.append(', '.join(self.parameters))
        st.append(self.text)
        st.append(self.tex)
        st.append(self.extra)
        st = '\n------\n'.join(st)
        return st

registry = FunctionsRegistry([os.path.join(USERDATADIR, 'functions')])
