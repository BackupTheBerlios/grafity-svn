import sys
import os
try:
   sys.modules['__main__'].splash.message('loading functions')
except:
    pass

from grafity.thirdparty import odr

from grafity.signals import HasSignals
from grafity.arrays import zeros, nan
from grafity.actions import action_from_methods, StopAction, action_from_methods2
from grafity.settings import DATADIR, USERDATADIR

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
        self.scan()

    def rescan(self):
        """Rescan the directory and check for changed functions"""
        names = []
        for dir in self.dirs:
            for f in os.listdir(dir):
                try:
                    func = Function()
                    func.fromstring(open(dir+'/'+f).read())
                    func.filename = dir + '/' + f
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

    def scan(self, dirs=None):
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
        def __fitfunction(*args):
            if len(args) == 3:
                niter, actred, wss = args
                message  = 'Fitting: Iteration %d, xsqr=%g, reduced xsqr=%g' % (niter, wss, actred)
                self.emit('status-message', message)
                return
            else:
                params, x = args

            params = splitlist(params, [len(t.parameters) for t in self.terms])

            for p, t in zip(params, self.terms):
                t.parameters = p

            return self(x)
                
        model = odr.Model(__fitfunction)
        data = odr.RealData(x, y)
        initial = flatten(t.parameters for t in self.terms)

        odrobj = odr.ODR(data, model, beta0=initial,  ifixb=[not k for k in lock], 
                         partol=1e-100, sstol=1e-100, maxit=maxiter)
        odrobj.set_job (fit_type=2)
        odrobj.set_iprint (iter=3, iter_step=1)
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
            

"""
    functions [
        id:S,
        func:S,
        name:S,
        params:S,
        lock:S,
        use:I
    ]
]
"""

from grafity.project import create_id

class MFunctionSum(FunctionSum):
    def __init__(self, data):
        FunctionSum.__init__(self)
        self.data = data
        for f in self.data:
            if f.func in registry and not f.id.startswith('-'):
                self.add(f.func, f.name)
                self.terms[-1].data = f
            elif not f.id.startswith('-'):
                print >>sys.stderr, "function '%s' not found." %f.func, registry
        self.connect('add-term', self.on_add_term)
        self.connect('remove-term', self.on_remove_term)

    def on_add_term(self, state, term):
        if hasattr(term, 'data') and term.data.id.startswith('-'):
            raise StopAction
        row = self.data.append(id=create_id(), func=term.function.name, name=term.name)
        term.data = self.data[row]
        state['term'] = term
    def undo_add_term(self, state):
        term = state['term']
        term.data.id = '-'+term.data.id
        self.terms.remove(term)
        self.emit('remove-term', term)
    def redo_add_term(self, state):
        term = state['term']
        self.terms.append(term)
        self.emit('add-term', term)
        term.data.id = term.data.id[1:]
    on_add_term = action_from_methods2('graph/add-function-term', on_add_term, undo_add_term, redo=redo_add_term)

    def on_remove_term(self, state, term):
        if hasattr(term, 'data') and term.data.id.startswith('-'):
            raise StopAction
        term.data.id = '-'+term.data.id
        state['term'] = term
    undo_remove_term = redo_add_term
    redo_remove_term = undo_add_term
    on_remove_term = action_from_methods2('graph/remove-function-term', on_remove_term, undo_remove_term, redo=redo_remove_term)
    
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

"""
class FunctionsWindow(gui.Window):
    def __init__(self):
        gui.Window.__init__(self, title='Functions', size=(500, 300))
        box = gui.Box(self, 'horizontal')

#        split = gui.Splitter(box, 'horizontal', stretch=1)
#        self.categories = gui.List(split)
        self.category = gui.List(box, model=RegModel(registry), stretch=1)
        self.category.connect('selection-changed', self.on_select_function)
        self.category.connect('item-activated', self.on_item_activated)

        rbox = gui.Box(box, 'vertical', stretch=2)

        toolbar = gui.Toolbar(rbox, stretch=0)
        toolbar.append(gui.Command('New', '', self.on_new, 'new.png'))
        toolbar.append(gui.Command('Delete', '', self.on_remove, 'remove.png'))
        toolbar.append(gui.Command('Save', '', self.on_save, 'save.png'))
        toolbar._widget.Realize()

        book = gui.Notebook(rbox)

        edit = gui.Box(book, 'vertical', page_label='edit')
        g = gui.Grid(edit, 2, 2, stretch=0, expand=True)
        g.layout.AddGrowableCol(1)
        gui.Label(g, 'Name', pos=(0,0))
        gui.Label(g, 'Parameters', pos=(1,0))
        self.name = gui.Text(g, pos=(0,1), expand=True)
        self.params = gui.Text(g, pos=(1,1), expand=True)

#        self.text = gui.Text(edit, multiline=True, stretch=1)
        self.text = gui.PythonEditor(edit, stretch=1)

        extra = gui.Box(book, 'vertical', page_label='extra')
#        self.extra = gui.Text(extra, multiline=True, stretch=1)
        self.extra = gui.PythonEditor(extra, stretch=1)

        self.functions = functions
        self.function = None

    def on_new(self):
        num = 0
        while 'function%d.function'%num in (f.filename.split('/')[-1] for f in registry):
            num += 1
        self.function = Function('function%d'%num, [], 'y=f(x)', '')
        open(USERDATADIR+'/functions/function%d.function'%num, 'wb').write(self.function.tostring())
#        self.scan('functions')
        registry.rescan()
        self.update_gui()

    def on_remove(self):
        os.remove(self.function.filename)
        registry.rescan()

    def on_save(self):
        self.function.name = self.name.text
        self.function.parameters = [p.strip() for p in self.params.text.split(',')]
        self.function.extra = self.extra.text
        self.function.text = self.text.text

        self.function.save()
#        self.function.to_module()
        registry.rescan()

    def update_gui(self):
        self.name.text = self.function.name
        self.params.text = ', '.join(self.function.parameters)
        self.extra.text = self.function.extra
        self.text.text = self.function.text

    def on_select_function(self):
        try:
            self.function = self.category.model[self.category.selection[0]]
        except IndexError:
            return
#        if self.function is not None:
#            print 'are you sure?'
#        self.function = [f for f in self.functions if f.name == name][0]
        self.update_gui()

    def on_item_activated(self, ind):
        self.emit('function-activated', self.category.model[ind])


if __name__ == '__main__':
    gui.Application().run(FunctionsWindow)
"""
