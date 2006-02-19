import sys

from grafity.arrays import *
from grafity.signals import HasSignals
from grafity.project import Item, wrap_attribute, register_class, create_id
from grafity.actions import action_from_methods, action_from_methods2, StopAction
from grafity.functions import FunctionSum, registry
import pyx

symbols = ['none', 'square', 'circle', 'diamond', 
           'triangleup', 'triangledown', 'triangleleft', 'triangleright', '+', 'x', ]
fills = ['filled', 'open']
colors = ['#000000', '#ff0000', '#8b0000', '#00ff00', '#006400', '#0000ff', '#00008b', 
          '#00ffff', '#008b8b', '#ff00ff', '#8b008b', '#ffff00', '#bebebe', 
          '#a9a9a9', '#d3d3d3', '#7ac5cd', '#6495ed', '#ffb90f', '#bcee68', '#ff7f00', 
          '#e9967a', '#00ced1', '#ee1289', '#00bfff', '#1874cd', '#ff69b4', '#cd6090', 
          '#cd5c5c', '#90ee90', '#5d478b', ]

linetypes = ['none', 'straight', 'spline']
linestyles = ['solid', 'dash', 'dot', 'dashdot', 'dashdotdot']

attr_values = {'color': colors, 'symbol': symbols, 'fill': fills, 
               'linetype': linetypes, 'linestyle': linestyles }

attrs = ['symbol', 'fill', 'size', 'color', 'linestyle', 'linewidth', 'linetype']

class Style(object):
    def __init__(self, dataset):
        self.dataset = dataset
    attrs = ['color', 'symbol', 'size', 'fill', 'linestyle', 'linewidth', 'linetype']

    def __getattr__(self, key):
        if key in self.attrs:
            return self.dataset.get_style(key)
        else:
            raise AttributeError, key

    def __setattr__(self, key, value):
        if key in self.attrs:
            self.dataset.set_style(key, value)
        else:
            object.__setattr__(self, key, value)


class Dataset(HasSignals):
    """Handles storing the description of a dataset in the database."""
    def __init__(self, graph, ind):
        self.graph, self.ind = graph, ind
        self.data = self.graph.data.datasets[ind]

        self.worksheet = self.graph.project.items[self.data.worksheet]
        self.x, self.y = self.worksheet[self.data.x], self.worksheet[self.data.y]

        self.style = Style(self)

    def on_x_rename(self, oldname, name):
        """Our x column was renamed in the workshet"""
        self.data.x = name.encode('utf-8')

    def on_y_rename(self, oldname, name):
        """Our x column was renamed in the workshet"""
        self.data.y = name.encode('utf-8')

    def on_data_changed(self):
        """Our data has changed"""
        self.recalculate()
        self.emit('modified', self)

    def connect_signals(self):
        self.x.connect('rename', self.on_x_rename)
        self.y.connect('rename', self.on_y_rename)
        self.x.connect('data-changed', self.on_data_changed)
        self.y.connect('data-changed', self.on_data_changed)

    def disconnect_signals(self):
        self.x.disconnect('rename', self.on_x_rename)
        self.y.disconnect('rename', self.on_y_rename)
        self.x.disconnect('data-changed', self.on_data_changed)
        self.y.disconnect('data-changed', self.on_data_changed)

    def active_data(self):
        length = min(len(self.x), len(self.y))
        x = asarray(self.x)[:length]
        y = asarray(self.y)[:length]
        ind = isfinite(x) & isfinite(y) & (self.xfrom <= x) & (x <= self.xto)
        return ind

    def recalculate(self):
        length = min(len(self.x), len(self.y))
        x = asarray(self.x)[:length]
        y = asarray(self.y)[:length]
        self.minx, self.maxx = min(x), max(x)
        ind = isfinite(x) & isfinite(y) & (self.xfrom <= x) & (x <= self.xto)
        xx = x[ind]
        yy = y[ind]
        self.graph.emit('data-changed', self, xx, yy)

    def set_range(self, _state, range):
        _state['old'] = self.xfrom, self.xto
        self.xfrom, self.xto = range
        self.recalculate()

    def undo_set_range(self, _state):
        self.xfrom, self.xto = _state['old']
        self.recalculate()

    def get_range(self):
        return self.xfrom, self.xto

    set_range = action_from_methods2('dataset-set-range', set_range, undo_set_range)

    range = property(get_range, set_range)

    id = wrap_attribute('id')
    xfrom = wrap_attribute('xfrom')
    xto = wrap_attribute('xto')

    # this is nescessary! see graph.remove
    def __eq__(self, other):
        return self.id == other.id

    def set_worksheet(self, ws): self.data.worksheet = ws.id
    def get_worksheet(self): return self.graph.project.items[self.data.worksheet]

    def __str__(self):
        return self.x.worksheet.name+':'+self.y.name+'('+self.x.name+')'

    def set_defaults(self):
        self.data.color = 0
        self.data.symbol = 'square'
        self.data.size = 5
        self.data.fill = 'filled'
        self.data.linetype = 'straight'
        self.data.linestyle = 'solid'
        self.data.linewidth = 1
        self.data.xfrom, self.data.xto = -inf, inf

    def get_style(self, style):
        if style == 'color':
            return "#%06x"%self.data.color
        elif style == 'symbol':
            return self.data.symbol
        elif style == 'size':
            return self.data.size
        elif style == 'fill':
            return self.data.fill
        elif style == 'linestyle':
            return self.data.linestyle
        elif style == 'linewidth':
            return self.data.linewidth
        elif style == 'linetype':
            return self.data.linetype

    def set_style(self, style, value):
        if style == 'color':
            self.data.color = int(value.replace('#', ''), 16)
        elif style == 'symbol':
            self.data.symbol = value
        elif style == 'size':
            self.data.size = value
        elif style == 'fill':
            self.data.fill = value
        elif style == 'linestyle':
            self.data.linestyle = value
        elif style == 'linewidth':
            self.data.linewidth = value
        elif style == 'linetype':
            self.data.linetype = value


#! /usr/bin/env python

from pyx import *

# The new symbol: just a vertical line
#
# Note that, as for all internal PyX methods, coordinates are passed in PS
# points, and we hence have to use the corresponding path classes.
def _linesymbol(c, x_pt, y_pt, size_pt, attrs):
    c.draw(path.line_pt(x_pt, y_pt-0.5*size_pt, x_pt, y_pt+0.5*size_pt), attrs)

# the symbol style expects a changeable attribute as argument, 
# so we create a dummy one consisting of a single symbol
linesymbol = pyx.attr.changelist([_linesymbol])

class Line:
    pass

class Text(HasSignals):
    def __init__(self, graph, data):
        self.graph, self.data = graph, data
        
    def get_text(self): 
        return self.data.text.decode('utf-8')

    def set_text(self, state, value):
        state['old'] = self.data.text
        self.data.text = value.encode('utf-8')
        state['new'] = self.data.text
        self.emit('modified')
        self.graph.emit('redraw')
    def undo_set_text(self, state):
        self.data.text = state['old']
        self.emit('modified')
        self.graph.emit('redraw')
    def redo_set_text(self, state):
        self.data.text = state['new']
        self.emit('modified')
        self.graph.emit('redraw')
    set_text = action_from_methods2('graph/text/set-text', set_text, undo_set_text, redo=redo_set_text)

    text = property(get_text, set_text)



class Graph(Item, HasSignals):
    def __init__(self, project, name=None, parent=None, location=None):
        Item.__init__(self, project, name, parent, location)
    
        self.datasets = []
        self.graph_objects = []
        if location is not None:
            for i, l in enumerate(self.data.datasets):
                if not l.id.startswith('-'):
                    self.datasets.append(Dataset(self, i))
                    self.datasets[-1].connect('modified', self.on_dataset_modified)
            for l in self.data.text:
                if not l.id.startswith('-'):
                    self.graph_objects.append(Text(self, l))

        self.function = FunctionSum(self.data.functions)

        if self.xtype == '':
            self._xtype = 'linear'
        if self.ytype == '':
            self._ytype = 'linear' 

    default_name_prefix = 'graph'

    def topyx(self, name=None):
        if name is None:
            name = self.name
        xaxis = pyx.graph.axis.linear(min=self.xmin, max=self.xmax, title=self.xtitle)
        yaxis = pyx.graph.axis.linear(min=self.ymin, max=self.ymax, title=self.ytitle)
        g = pyx.graph.graphxy(width=8, x=xaxis, y=yaxis)

        pyx_symbols = [ None, 'square', 'circle', 'diamond',
                        'triangle', 'triangle', 'triangle', 'triangle',  
                        'plus', 'cross' ]
        pyx_symbols = dict(zip(symbols, pyx_symbols))

        for ds in self.datasets:
            active = ds.active_data()
            data = pyx.graph.data.list(sorted(zip(ds.x[active], ds.y[active])), x=1, y=2)
            line = pyx.graph.style.line([pyx.style.linewidth.Thin, pyx.style.linestyle.solid])
            color = pyx.color.rgb(*[int(s, 16)/256. for s in (ds.style.color[a:b] for a,b in ((1,3),(3,5),(5,7)))])

#            symbol = pyx.graph.style.symbol(symbol=linesymbol, size=0.1,
#                                            symbolattrs=[pyx.deco.filled([color]), pyx.deco.stroked([color]),],)
            if ds.style.symbol != 'none':
                symbol = pyx.graph.style.symbol(getattr(pyx.graph.style.symbol, pyx_symbols[ds.style.symbol]), size=0.1,
                                                symbolattrs=[
                                                pyx.deco.filled([color]), 
                                                pyx.deco.stroked([color, pyx.style.linewidth.Thin,]),],
                                                )
                g.plot(data, [symbol])
            if ds.style.linetype != 'none':
                g.plot(data, [line])

        g.writeEPSfile(name)


    def togri(self):
        gri_symbols_open = [ None, 'box', 'circ', 'diamond',
                             'triangleup', 'triangledown', 'triangleleft', 'triangleright',  
                             'plus', 'times' ]
        gri_symbols_filled = [ None, 'filledbox', 'bullet', 'filleddiamond', 
                             'filledtriangleup', 'filledtriangledown', 'filledtriangleleft', 'filledtriangleright',  
                             'plus', 'times' ]

        gri_symbols = {'open' : dict(zip(symbols, gri_symbols_open)),
                       'filled' : dict(zip(symbols, gri_symbols_open)) }
                              
        gri_linestyles = dict(zip(linestyles, [ 'off', '', '14', '0.5 0.1 0.1 0.1', '0.5 0.1 0.1 0.1 0.1 0.1']))


        gri = []

        gri.append('# Generated by grafity')
        gri.append('set clip on')
        gri.append('set tics in')

        if self.xtype == 'log':
            gri.append('set x type log')
        if self.xtype == 'log':
            gri.append('set y type log')

        gri.append('set x axis %g %g' % (self.xmin, self.xmax))
        gri.append('set y axis %g %g' % (self.ymin, self.ymax))

        gri.append('set x name "%s"' % self.xtitle)
        gri.append('set y name "%s"' % self.ytitle)

        gri.append('draw axes')

        for ds in self.datasets:
            gri.append('read columns x y')
            active = ds.active_data()
            for x, y in sorted(zip(ds.x[active], ds.y[active])):
                 gri.append('%g %g' %(x, y))
            gri.append('')

            gri.append('set symbol size %g' % (ds.style.size / 30.))
            gri.append('set color rgb %f %f %f' % tuple([int(s, 16)/256. for s in 
                                                          (ds.style.color[a:b] for a,b in ((1,3),(3,5),(5,7)))]))
            shape = gri_symbols[ds.style.fill][ds.style.symbol]
            if shape is not None:
                gri.append('draw symbol %s' % shape)
            if ds.style.linetype == 'spline' and self.xtype != 'log':
                gri.append('convert columns to spline')
            gri.append('set dash %s' % gri_linestyles[ds.style.linestyle])

            if ds.style.linetype != 'none':
                gri.append('draw curve')
            gri.append('')

        gricode = '\n'.join(gri)
        return gricode

    def get_xmin(self): 
        try: return float(self._zoom.split()[0])
        except IndexError: return 0.0
    def get_xmax(self): 
        try: return float(self._zoom.split()[1])
        except IndexError: return 1.0
    def get_ymin(self): 
        try: return float(self._zoom.split()[2])
        except IndexError: return 0.0
    def get_ymax(self): 
        try: return float(self._zoom.split()[3])
        except IndexError: return 1.0
    def set_xmin(self, value): 
        self._zoom = ' '.join([str(f) for f in [value, self.xmax, self.ymin, self.ymax]])
    def set_xmax(self, value): 
        self._zoom = ' '.join([str(f) for f in [self.xmin, value, self.ymin, self.ymax]])
    def set_ymin(self, value): 
        self._zoom = ' '.join([str(f) for f in [self.xmin, self.xmax, value, self.ymax]])
    def set_ymax(self, value): 
        self._zoom = ' '.join([str(f) for f in [self.xmin, self.xmax, self.ymin, value]])
    xmin = property(get_xmin, set_xmin)
    xmax = property(get_xmax, set_xmax)
    ymin = property(get_ymin, set_ymin)
    ymax = property(get_ymax, set_ymax)


    # axis scales

    def set_xtype(self, _state, tp):
#        if tp == 'log' and (self.xmin <= 0 or self.xmax <= 0):
#            raise StopAction
        _state['old'] = self._xtype
        self._xtype = tp
        self.emit('set-scale', 'x', self.xtype)
    def undo_set_xtype(self, _state):
        self._xtype = _state['old']
        self.emit('set-scale', 'x', self.xtype)
    set_xtype = action_from_methods2('graph-set-xaxis-scale', set_xtype, undo_set_xtype)
    def get_xtype(self):
        return self._xtype
    xtype = property(get_xtype, set_xtype)

    def set_ytype(self, _state, tp):
#        if tp == 'log' and (self.xmin <= 0 or self.xmax <= 0):
#            raise StopAction
        _state['old'] = self._ytype
        self._ytype = tp
        self.emit('set-scale', 'y', self.ytype)
    def undo_set_ytype(self, _state):
        self._ytype = _state['old']
        self.emit('set-scale', 'y', self.ytype)
    set_ytype = action_from_methods2('graph-set-xaxis-scale', set_ytype, undo_set_ytype)
    def get_ytype(self):
        return self._ytype
    ytype = property(get_ytype, set_ytype)


    # titles

    def set_xtitle(self, state, title):
        state['old'], state['new'] = self._xtitle, title
        self._xtitle = title
        self.emit('set-title', 'x', self.xtitle)
    def undo_set_xtitle(self, state):
        self._xtitle = state['old']
        self.emit('set-title', 'x', self.xtitle)
    def redo_set_xtitle(self, state):
        self._xtitle = state['new']
        self.emit('set-title', 'x', self.xtitle)
    def get_xtitle(self):
        return self._xtitle
    set_xtitle = action_from_methods2('graph/set-xtitle', set_xtitle, undo_set_xtitle, redo=redo_set_xtitle)
    xtitle = property(get_xtitle, set_xtitle)

    def set_ytitle(self, state, title):
        state['old'], state['new'] = self._ytitle, title
        self._ytitle = title
        self.emit('set-title', 'y', self.ytitle)
    def undo_set_ytitle(self, state):
        self._ytitle = state['old']
        self.emit('set-title', 'y', self.ytitle)
    def redo_set_ytitle(self, state):
        self._ytitle = state['new']
        self.emit('set-title', 'y', self.ytitle)
    def get_ytitle(self):
        return self._ytitle
    set_ytitle = action_from_methods2('graph/set-ytitle', set_ytitle, undo_set_ytitle, redo=redo_set_ytitle)
    ytitle = property(get_ytitle, set_ytitle)

    def __repr__(self):
        return '<Graph %s%s>' % (self.name, '(deleted)'*self.id.startswith('-'))

    # add and remove graph objects
    def new_object(self, state, typ):
        location = { Line: self.data.lines, Text: self.data.text }[typ]
        ind = location.append(id=create_id())
        obj = typ(self, location[ind])
        self.graph_objects.append(obj)
        state['obj'] = obj
        return obj

    def undo_new_object(self, state):
        obj = state['obj']
        self.graph_objects.remove(obj)
        obj.id = '-'+obj.id

    def redo_new_object(self, state):
        obj = state['obj']
        self.graph_objects.append(obj)
        location =  { Line: self.data.lines, Text: self.data.text }[type(obj)]
        obj.id = obj.id[1:]

    new_object = action_from_methods2('graph/new-object', new_object, undo_new_object, 
                                       redo=redo_new_object)
    def delete_object(self, state, obj):
        obj.id = '-'+obj.id
        self.graph_objects.remove(obj)
        state['obj'] = obj
    delete_object = action_from_methods2('graph/delete-object', delete_object, redo_new_object,
                                          redo=undo_new_object)

    def set_style(self, state, datasets, series=None, **kwds):
        for d in datasets:
            state[d] = dict((attr, d.get_style(attr)) for attr in kwds)
        if series is None:
            series = []
        for attr in ['color', 'symbol', 'fill', 
                     'linestyle', 'linetype']:
            if attr in kwds:
                if attr in series:
                    for i, d in enumerate(datasets):
                        values = attr_values[attr]
                        value = values[(values.index(kwds[attr])+i)%len(values)]
                        d.set_style(attr, value)
                else:
                    for d in datasets:
                        d.set_style(attr, kwds[attr])
        for attr in ['size', 'linewidth']:
            if attr in kwds:
                if attr in series:
                    for i, d in enumerate(datasets):
                        d.set_style(attr, kwds[attr]+i)
                else:
                    for d in datasets:
                        d.set_style(attr, kwds[attr])

        self.emit('style-changed', datasets)


    def undo_set_style(self, state):
        for d, style in state.iteritems():
            for attr, value in style.iteritems():
                d.set_style(attr, value)
        self.emit('style-changed', state.keys())

    set_style = action_from_methods2('graph_set_style', set_style, undo_set_style)
        


    # add and remove datasets
    def add(self, state, x, y):
        ind = self.data.datasets.append(worksheet=x.worksheet.id, id=create_id(), 
                                        x=x.name.encode('utf-8'), y=y.name.encode('utf-8'))

        d = Dataset(self, ind)
        d.set_defaults()
        self.datasets.append(d)
        pos = len(self.datasets)-1

        d.connect('modified', self.on_dataset_modified)
        d.connect_signals()

        self.on_dataset_modified(d)
        self.emit('add-dataset', d)

        state['obj'] = d

        return pos

    def undo_add(self, state):
        d = state['obj']

        self.datasets.remove(d)
        d.disconnect_signals()
        d.disconnect('modified', self.on_dataset_modified)
        self.emit('remove-dataset', d)
        d.id = '-'+d.id
#        self.data.datasets.delete(d.ind)

    def redo_add(self, state):
        d = state['obj']
        d.id = d.id[1:]
        self.datasets.append(d)
        d.connect('modified', self.on_dataset_modified)
        d.connect_signals()
        self.emit('add-dataset', d)

    add = action_from_methods2('graph_add_dataset', add, undo_add, redo=redo_add)

    def remove(self, dataset):
        # we can do this even if `dataset` is a different object
        # than the one in self.datasets, if they have the same id
        # (see Dataset.__eq__)
        # TODO: why bother? just keep the object itself in the state
        ind = self.datasets.index(dataset)
        dataset.id = '-'+dataset.id
        self.datasets.remove(dataset)
        try:
            dataset.disconnect('modified', self.on_dataset_modified)
        except NameError:
            pass
        self.emit('remove-dataset', dataset)
        return (dataset.ind, ind), None

    def undo_remove(self, data):
        ind, pos = data
        dataset = Dataset(self, ind)
        dataset.id = dataset.id[1:]
        self.on_dataset_modified(dataset)
        self.datasets.insert(pos, dataset)
        dataset.connect('modified', self.on_dataset_modified)
        self.emit('add-dataset', dataset)

    remove = action_from_methods('graph_remove_dataset', remove, undo_remove)

    def on_dataset_modified(self, d=None):
        pass

    def paint_axes(self):
        for a in self.axes:
            a.paint_frame()

        self.grid_h.paint()
        self.grid_v.paint()


    def autoscale(self):
        if len(self.datasets):
            xmin = min(d.xx.min() for d in self.datasets)
            xmax = max(d.xx.max() for d in self.datasets)
            ymin = min(d.yy.min() for d in self.datasets)
            ymax = max(d.yy.max() for d in self.datasets)
            self.zoom(xmin, xmax, ymin, ymax)

    def set_range(self, fr, to):
        self.fr, self.to  = fr, to

    #####################
    # zoom action      #
    #####################

    def zoom_do(self, state, xmin, xmax, ymin, ymax):
        eps = 1e-24
        state['old'] = (self.xmin, self.xmax, self.ymin, self.ymax)
        if abs(xmin-xmax)<=eps or abs(ymin-ymax)<=eps:
            return
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax
        state['new'] = (xmin, xmax, ymin, ymax)
        self.emit('zoom-changed', self.xmin, self.xmax, self.ymin, self.ymax)

    def zoom_redo(self, state):
        self.xmin, self.xmax, self.ymin, self.ymax = state['new']
        self.emit('zoom-changed', self.xmin, self.xmax, self.ymin, self.ymax)

    def zoom_undo(self, state):
        self.xmin, self.xmax, self.ymin, self.ymax = state['old']
        self.emit('zoom-changed', self.xmin, self.xmax, self.ymin, self.ymax)

    def zoom_combine(self, state, other):
        return False

    zoom = action_from_methods2('graph-zoom', zoom_do, zoom_undo, redo=zoom_redo, combine=zoom_combine)

    def zoom_out(self, xmin, xmax, ymin, ymax):
        xmin, xmax = self.zoomout(self.xmin, self.xmax, xmin, xmax, log=self.xtype=='log')
        ymin, ymax = self.zoomout(self.ymin, self.ymax, ymin, ymax, log=self.ytype=='log')
        self.zoom(xmin, xmax, ymin, ymax)
        
    def zoomout(self,x1, x2,x3, x4, log=False):
        if log:
            x1, x2, x3, x4 = log10(x1), log10(x2), log10(x3), log10(x4)
        if x3 == x4:
            return x1, x2
        a = (x2-x1)/(x4-x3)
        c = x1 - a*x3
        f1 = a*x1 + c
        f2 = a*x2 + c
        if log:
            f1, f2 = 10.**f1, 10.**f2
        return min(f1, f2), max(f1, f2)

    _xtype = wrap_attribute('xtype')
    _ytype = wrap_attribute('ytype')
    _xtitle = wrap_attribute('xtitle')
    _ytitle = wrap_attribute('ytitle')
    _zoom = wrap_attribute('zoom')

desc="""
graphs [
    name:S, id:S, parent:S, zoom:S, 
    xtype:S, ytype:S, xtitle:S, ytitle:S,
    datasets [
        id:S, worksheet:S, x:S, y:S,
        symbol:S, fill:S, color:I, size:I, linetype:S, linestyle:S, linewidth:I,
        xfrom:D, xto:D 
    ],
    functions [
        id:S, func:S, name:S,
        params:S, lock:S, limit:S, use:I
    ],
    lines [ id:S, position:S ],
    text [ id:S, x:D, y:D, text:S ]
]
"""
register_class(Graph, desc)

