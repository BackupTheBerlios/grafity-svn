import inspect
import types
import sys

try:
    sys.modules['__main__'].splash_message('loading Function')
except:
    pass

class FitFunction (object):
    """function onject with memory"""
    def __init__ (self, name, params, initial):
        self.name = name
        self.params = params
        self.initparams = initial
        for name, value in zip (params, initial):
            setattr(self, name, value)
        self.locked = [0]*len(params)
        self.varshare = [True]*len(params)
        self.inst_name = None

        self.saved = {}
        self.last = None

    def call(self, x):
        raise NotImplementedError

    # TODO: make these properties?
    def lock (self, id, locked):
        self.locked[id] = locked

    def is_locked (self, id):
        return self.locked[id]

    def set_params (self, paramlist):
        for i in range(len(self.params)):
            setattr(self, self.params[i], paramlist[i])

    def get_params (self):
        return [getattr(self, name) for name in self.params]


    def save (self, id):
        """ save the parameters and locks to the slot 'id'"""
        self.saved[id] = (self.get_params (), self.locked)
        self.last = id

    def load (self, id):
        """ load the parameters and locks from the slot 'id'"""
        try:
            paramlist = self.saved[id][0]
            for i in range(len(self.params)):
                if not self.varshare[i]:
                    setattr(self, self.params[i], paramlist[i])
            self.locked = self.saved[id][1]
        except KeyError:
            if self.last is not None:
                self.load(self.last)
            else:
                self.set_params(self.initparams)
                self.locked = [0]*len(self.params)
                self.save(id)

def decorate(func):
    if not hasattr(func, 'args'):
        if type(func) is types.FunctionType:
            func.args = inspect.getargspec(func)[0][1:]
        elif hasattr(func, __call__):
            func.args = inspect.getargspec(func.__call__)[0][2:]
        else:
            raise TypeError
    if not hasattr(func, 'name'):
        func.name = func.__name__
    if not hasattr(func, 'initial_values'):
        func.initial_values = (1.0,) * len(func.args)

def function_class_from_function(func):
    decorate(func)

    class NewFunction (FitFunction):
        def __init__ (self):
            FitFunction.__init__ (self, func.name, func.args, func.initial_values)

        def call(self, x):
            try:
                return func(x, *self.get_params())
            except OverflowError:
                print >>sys.stderr, 'Overflow'
                return x
            

        if hasattr(func, 'move'):
            def move(self, x, y):
                self.set_params (func.move (x, y, *self.get_params()))
        if hasattr(func, 'horiz'):
            def horiz(self, x):
                self.set_params (func.horiz (x, *self.get_params()))
        if hasattr(func, 'vert'):
            def vert(self, x):
                self.set_params (func.vert (x, *self.get_params()))
        if hasattr(func, 'tex'):
            tex = func.tex
        if hasattr(func, 'desc'):
            desc = func.desc
        if hasattr(func, 'extra'):
            extra = func.extra

    return NewFunction

def special_case(func, name, **kwds):
    decorate(func)
    args = [func.args[n] for n, aa in enumerate(func.args) if aa not in kwds.keys()]
    initial_values = [func.initial_values[n] for n, aa in enumerate(func.args) if aa in args]
    
    class SpecialCaseFunction(object):
        def __init__(self):
            self.args = args
            self.initial_values = initial_values
            self.special = kwds
            self.allargs = func.args
            self.name = name

        def callargs(self, args):
            calldict = {}
            for i, arg in enumerate(self.args):
                calldict[arg] = args[i]
            callargs = []
            for arg in self.allargs:
                if arg in self.args:
                    callargs.append(args[self.args.index(arg)])
                else:
                    callargs.append(eval(self.special[arg], calldict))
            return callargs

        def __call__(self, x, *args):
            try:
                return func(x, *self.callargs(args))
            except OverflowError:
                print >>sys.stderr, 'Overflow'
                return x
            

        if hasattr(func, 'move'):
            def move(self, x, y, *args):
                return func.move (x, y, *self.callargs(args))

#        if hasattr(func, 'extra'):
#            extra = func.extra
        
    return SpecialCaseFunction()
