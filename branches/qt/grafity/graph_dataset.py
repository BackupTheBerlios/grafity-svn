from grafity.arrays import *
from grafity.signals import HasSignals
from grafity.actions import action_from_methods2, action_from_methods
from grafity.functions import MFunctionSum
from grafity.project import wrap_attribute
from numarray.ieeespecial import isfinite

class Dataset(HasSignals):
    def __init__(self, graph, ind):
        self.graph, self.ind = graph, ind
        self.data = self.graph.data.datasets[ind]

#        DrawWithStyle.__init__(self, graph, self.data)

        self.worksheet = self.graph.project.items[self.data.worksheet]
        self.x, self.y = self.worksheet[self.data.x], self.worksheet[self.data.y]

        self.x.connect('rename', self.on_x_rename)
        self.y.connect('rename', self.on_y_rename)

        self.xfrom, self.xto = -inf, inf
#        self.recalculate()

    def on_x_rename(self, oldname, name):
        self.data.x = name.encode('utf-8')

    def on_y_rename(self, oldname, name):
        self.data.y = name.encode('utf-8')

    def connect_signals(self):
        self.x.connect('data-changed', self.on_data_changed)
        self.y.connect('data-changed', self.on_data_changed)

    def disconnect_signals(self):
        self.x.disconnect('data-changed', self.on_data_changed)
        self.y.disconnect('data-changed', self.on_data_changed)

    def on_data_changed(self):
        self.recalculate()
        self.emit('modified', self)

#    def __repr__(self):
#        return '<Dataset %s (#%d in graph "%s"), (%s, %s, %s)>' % (self.id, self.graph.datasets.index(self), self.graph.name,
#                                                         self.worksheet.name, self.x.name, self.y.name)

    def active_data(self):
        length = min(len(self.x), len(self.y))
        x = asarray(self.x)[:length]
        y = asarray(self.y)[:length]
        ind = isfinite(x) & isfinite(y) & (self.xfrom <= x) & (x <= self.xto)
        return ind

    def recalculate(self):
#        length = min(len(self.x), len(self.y))
#        x = asarray(self.x)[:length]
#        y = asarray(self.y)[:length]
#        ind = isfinite(x) & isfinite(y) & (self.xfrom <= x) & (x <= self.xto)
#        self.xx = x[ind]
#        self.yy = y[ind]
        self.xx = asarray(self.x)
        self.yy = asarray(self.y)

    def set_range(self, _state, range):
        _state['old'] = self.xfrom, self.xto
        self.xfrom, self.xto = range
#        self.recalculate()
        self.emit('modified', self)

    def undo_set_range(self, _state):
        self.xfrom, self.xto = _state['old']
#        self.recalculate()
        self.emit('modified', self)

    def get_range(self):
        return self.xfrom, self.xto

    set_range = action_from_methods2('dataset-set-range', set_range, undo_set_range)

    range = property(get_range, set_range)


    def paint(self):
#        t = time.time()
#        for i in xrange(10):
#            xx, yy = self.graph.data_to_phys(self.xx, self.yy)
#        print >>sys.stderr, 'o', (t - time.time())*1000,
#        t = time.time()
#        for i in xrange(10):
        if not hasattr(self, 'xx'):
            self.recalculate()
        self.paint_lines(self.xx, self.yy)
        self.paint_symbols(self.xx, self.yy)
#        print >>sys.stderr, 'i', (t - time.time())*1000

    id = wrap_attribute('id')

    # this is nescessary! see graph.remove
    def __eq__(self, other):
        return self.id == other.id

    def set_worksheet(self, ws): self.data.worksheet = ws.id
    def get_worksheet(self): return self.graph.project.items[self.data.worksheet]

    def __str__(self):
        return self.x.worksheet.name+':'+self.y.name+'('+self.x.name+')'

class Nop:
    pass

class Function(HasSignals):
    def __init__(self, graph, totalcolor=(0, 0, 155), termcolor=(0, 0, 0)):
        self.graph = graph
        self.data =  Nop()
        self.data.color = '0'
        self.data.size = '0'
        self.data.symbol = ''
        self.data.color = 0
        self.data.linestyle = ''
        self.data.linetype = ''
        self.data.linewidth = ''
#        self.data['color']
#self.graph.data.functions[ind]

#        DrawWithStyle.__init__(self, graph, self.data)
        self.style._line_style = 'solid'
        self.style._line_type = 'straight'

        self.totalcolor, self.termcolor = totalcolor, termcolor

        self.func = MFunctionSum(self.graph.data.functions)

    def paint(self):
        npoints = 100
        if self.graph.xtype == 'log':
            x = 10**arange(log10(self.graph.xmin), log10(self.graph.xmax), 
                           (log10(self.graph.xmax/self.graph.xmin))/npoints)
        else:
            x = arange(self.graph.xmin, self.graph.xmax, 
                       (self.graph.xmax-self.graph.xmin)/npoints)

        self.style._color = self.termcolor
        if hasattr(self.func, 'terms'):
            for term in self.func.terms:
                if term.enabled:
                    y = term(x)
#                    self.paint_lines(*self.graph.data_to_phys(x, y))
                    self.paint_lines(x, y)

        self.style._color = self.totalcolor
        y = self.func(x)
#        self.paint_lines(*self.graph.data_to_phys(x, y))
        self.paint_lines(x, y)

    def set_id(self, id): self.data.id = id
    def get_id(self): return self.data.id
    id = property(get_id, set_id)

    # this is necessary! see graph.remove
    def __eq__(self, other):
        return self.id == other.id


