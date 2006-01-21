import sys
import time
import string
import tempfile

try:
   sys.modules['__main__'].splash.message('loading graph')
except:
    pass

from grafity.arrays import *

from grafity.signals import HasSignals
from grafity.project import Item, wrap_attribute, register_class, create_id
from grafity.actions import action_from_methods, action_from_methods2, StopAction
from grafity.settings import DATADIR

from grafity.arrays import *
from grafity.signals import HasSignals
from grafity.actions import action_from_methods2, action_from_methods
from grafity.functions import MFunctionSum
from grafity.project import wrap_attribute
from numarray.ieeespecial import isfinite

class Dataset(HasSignals):
    """Handles storing the description of a dataset in the database."""
    def __init__(self, graph, ind):
        self.graph, self.ind = graph, ind
        self.data = self.graph.data.datasets[ind]

        self.worksheet = self.graph.project.items[self.data.worksheet]
        self.x, self.y = self.worksheet[self.data.x], self.worksheet[self.data.y]

        self.x.connect('rename', self.on_x_rename)
        self.y.connect('rename', self.on_y_rename)

        self.xfrom, self.xto = -inf, inf

        self.style = Style(self)

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
        ind = isfinite(x) & isfinite(y) & (self.xfrom <= x) & (x <= self.xto)
        xx = x[ind]
        yy = y[ind]
        self.graph.emit('data-changed', self, xx, yy)
#        self.xx = asarray(self.x)
#        self.yy = asarray(self.y)

    def set_range(self, _state, range):
        _state['old'] = self.xfrom, self.xto
        self.xfrom, self.xto = range
#        self.recalculate(s)
        self.recalculate()
#        self.emit('modified', self)

    def undo_set_range(self, _state):
        self.xfrom, self.xto = _state['old']
#        self.recalculate()
#        self.emit('modified', self)
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

        self.graph.emit('style-changed', self, style, value)

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


log = False

class Graph(Item, HasSignals):
    def __init__(self, project, name=None, parent=None, location=None):
        Item.__init__(self, project, name, parent, location)
    
        self.datasets = []
        if location is not None:
            for i, l in enumerate(self.data.datasets):
                if not l.id.startswith('-'):
                    self.datasets.append(Dataset(self, i))
                    self.datasets[-1].connect('modified', self.on_dataset_modified)

        self.functions = []

    default_name_prefix = 'graph'

    def redraw(self, recalc=False):
        if recalc:
            self.recalc = True
        self.emit('redraw')

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
        if tp == 'log' and (self.xmin <= 0 or self.xmax <= 0):
            raise StopAction
        _state['old'] = self._xtype
        self._xtype = tp
        self.redraw(True)
    def undo_set_xtype(self, _state):
        self._xtype = _state['old']
        self.redraw(True)
    set_xtype = action_from_methods2('graph-set-xaxis-scale', set_xtype, undo_set_xtype)
    def get_xtype(self):
        return self._xtype
    xtype = property(get_xtype, set_xtype)

    def set_ytype(self, _state, tp):
        if tp == 'log' and (self.xmin <= 0 or self.xmax <= 0):
            raise StopAction
        _state['old'] = self._ytype
        self._ytype = tp
        self.redraw(True)
    def undo_set_ytype(self, _state):
        self._ytype = _state['old']
        self.redraw(True)
    set_ytype = action_from_methods2('graph-set-xaxis-scale', set_ytype, undo_set_ytype)
    def get_ytype(self):
        return self._ytype
    ytype = property(get_ytype, set_ytype)


    # titles

    def set_xtitle(self, state, title):
        state['old'], state['new'] = self._xtitle, title
        self._xtitle = title
        self.reshape()
        self.redraw()
    def undo_set_xtitle(self, state):
        self._xtitle = state['old']
        self.reshape()
        self.redraw()
    def redo_set_xtitle(self, state):
        self._xtitle = state['new']
        self.reshape()
        self.redraw()
    def get_xtitle(self):
        return self._xtitle
    set_xtitle = action_from_methods2('graph/set-xtitle', set_xtitle, undo_set_xtitle, redo=redo_set_xtitle)
    xtitle = property(get_xtitle, set_xtitle)

    def reshape(self):
        pass

    def set_ytitle(self, state, title):
        state['old'], state['new'] = self._ytitle, title
        self._ytitle = title
        self.reshape()
        self.redraw()
    def undo_set_ytitle(self, state):
        self._ytitle = state['old']
        self.reshape()
        self.redraw()
    def redo_set_ytitle(self, state):
        self._ytitle = state['new']
        self.reshape()
        self.redraw()
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
        self.redraw()

    def redo_new_object(self, state):
        obj = state['obj']
        self.graph_objects.append(obj)
        location =  { Line: self.data.lines, Text: self.data.text }[type(obj)]
        obj.id = obj.id[1:]
        self.redraw()

    new_object = action_from_methods2('graph/new-object', new_object, undo_new_object, 
                                       redo=redo_new_object)
    def delete_object(self, state, obj):
        obj.id = '-'+obj.id
        self.graph_objects.remove(obj)
        state['obj'] = obj
        self.redraw()
    delete_object = action_from_methods2('graph/delete-object', delete_object, redo_new_object,
                                          redo=undo_new_object)


    # add and remove datasets
    def add(self, state, x, y):
        ind = self.data.datasets.append(worksheet=x.worksheet.id, id=create_id(), 
                                        x=x.name.encode('utf-8'), y=y.name.encode('utf-8'))

        d = Dataset(self, ind)
        self.datasets.append(d)
        pos = len(self.datasets)-1
#        print 'added dataset, index %d, position %d' % (ind, pos)

        d.connect('modified', self.on_dataset_modified)
        d.connect_signals()

        self.on_dataset_modified(d)
        self.emit('add-dataset', d)

        state['obj'] = d

        return pos

    def undo_add(self, state):
        d = state['obj']

#        print 'undoing addition of dataset, index %d, position %d' % (d.ind, pos)
        self.datasets.remove(d)
        d.disconnect_signals()
        d.disconnect('modified', self.on_dataset_modified)
        self.emit('remove-dataset', d)
        self.redraw(True)
        d.id = '-'+d.id
#        self.data.datasets.delete(d.ind)

    def redo_add(self, state):
        d = state['obj']
        d.id = d.id[1:]
        self.datasets.append(d)
        d.connect('modified', self.on_dataset_modified)
        d.connect_signals()
        self.emit('add-dataset', d)
        self.redraw(True)

    add = action_from_methods2('graph_add_dataset', add, undo_add, redo=redo_add)

    def remove(self, dataset):
        # we can do this even if `dataset` is a different object
        # than the one in self.datasets, if they have the same id
        # (see Dataset.__eq__)
        # TODO: why bother? just keep the object itself in the state
        ind = self.datasets.index(dataset)
        print 'removing dataset, index %d, position %d' % (dataset.ind, ind)
        dataset.id = '-'+dataset.id
        self.datasets.remove(dataset)
        try:
            dataset.disconnect('modified', self.on_dataset_modified)
        except NameError:
            pass
        self.emit('remove-dataset', dataset)
        self.redraw(True)
        return (dataset.ind, ind), None

    def undo_remove(self, data):
        ind, pos = data
        print 'undoing removal of dataset, index %d, position %d' % (ind, pos)
        dataset = Dataset(self, ind)
        dataset.id = dataset.id[1:]
        self.on_dataset_modified(dataset)
        self.datasets.insert(pos, dataset)
        dataset.connect('modified', self.on_dataset_modified)
        self.emit('add-dataset', dataset)
        self.redraw(True)

    remove = action_from_methods('graph_remove_dataset', remove, undo_remove)

    def on_dataset_modified(self, d=None):
        self.redraw(True)

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
        self.reshape()
        self.redraw(True)

    def zoom_undo(self, state):
        self.xmin, self.xmax, self.ymin, self.ymax = state['old']
        self.emit('zoom-changed', self.xmin, self.xmax, self.ymin, self.ymax)
        self.reshape()
        self.redraw(True)

    def zoom_combine(self, state, other):
        return False

    zoom = action_from_methods2('graph-zoom', zoom_do, zoom_undo, redo=zoom_redo, combine=zoom_combine)

    def zoom_out(self, xmin, xmax, ymin, ymax):
        xmin, xmax = self.zoomout(self.xmin, self.xmax, xmin, xmax)
        ymin, ymax = self.zoomout(self.ymin, self.ymax, ymin, ymax)
        self.zoom(xmin, xmax, ymin, ymax)
        
 
    def zoomout(self,x1, x2,x3, x4):
        if x3 == x4:
            return x1, x2
        a = (x2-x1)/(x4-x3)
        c = x1 - a*x3
        f1 = a*x1 + c
        f2 = a*x2 + c
        return min(f1, f2), max(f1, f2)

    def init(self):
        glClearColor(*self.background_color)
        glClear(GL_COLOR_BUFFER_BIT)

        # enable transparency
        glEnable (GL_BLEND)
        glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glDisable(GL_DEPTH_TEST)
        glShadeModel(GL_FLAT)

        # we need this to render pil fonts properly
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glPixelStorei(GL_PACK_ALIGNMENT, 1)

        self.listno = glGenLists(1)

    def show(self):
        for d in self.datasets:
            if not hasattr(d, 'xx'):
                d.recalculate()

    def button_press(self, x, y, button=None):
        if self.mode == 'zoom':
            if button in (1,3):
                self.paint_xor_objects = True
                self.pixx, self.pixy = x, y
                self.ix, self.iy = self.mouse_to_phys(x, y)
                self.rubberband.show(self.ix, self.iy, self.ix, self.iy)
                self.redraw()
            if button == 2:
                self.haha = True
            else:
                self.haha = False
        elif self.mode == 'hand':
            if self.selected_function is not None:
                self.selected_function.set_reg(False)
                self.selected_function.move(*self.mouse_to_data(x, y))
#                self.emit('redraw')
                self._movefunc = DrawFunction(self, self.selected_function)
                self.objects.append(self._movefunc)
                self.paint_xor_objects = True
                self._movefunc.show(*self.mouse_to_data(x, y))
                self.redraw()
        elif self.mode == 's-reader':
            self.paint_xor_objects = True
            self.cross.show(*self.mouse_to_phys(x, y))
            self.redraw()
            self.emit('status-message', '%f, %f' % self.mouse_to_data(x, y))
        elif self.mode == 'range':
            self.paint_xor_objects = True
            self.rangehandle.show(*self.mouse_to_phys(x, y))
            self.redraw()
        elif self.mode == 'd-reader':
            qx, qy = self.mouse_to_data(x, y)

            distances = []
            closest_ind = []

            for d in self.datasets:
                dist = (d.xx-qx)*(d.xx-qx) + (d.yy-qy)*(d.yy-qy)
                arg = argmin(dist)
                closest_ind.append(arg)
                distances.append(dist[arg])

            ind = argmin(distances)
            dataset = self.datasets[ind]
            x, y = dataset.xx[closest_ind[ind]], dataset.yy[closest_ind[ind]]

            self.paint_xor_objects = True
            self.cross.show(*self.data_to_phys(x, y))
            self.redraw()
            self.emit('status-message', '%f, %f' % (x, y))
        elif self.mode == 'arrow':
            if button == 1:
                x, y = self.mouse_to_phys(x, y)
                for o in self.graph_objects:
                    if o.hittest(x, y):
                        self.selected_object = o
                        self.dragobj = o
                        self.dragobj.rec = False
                        self.dragobj_xor = Move(self.dragobj)
                        self.objects.append(self.dragobj_xor)
                        self.paint_xor_objects = True
                        self.dragobj_xor.show(x, y)
                        if o.hittest_handles(x, y):
                            self.dragobj.dragstart = None
                        break
                else:
                    self.selected_object = None
                self.redraw()
            elif button == 3:
                self.emit('right-clicked', None)
                print >>sys.stderr, 'right-clicked', None
        elif self.mode in ('draw-line', 'draw-text'):
            xi, yi = self.mouse_to_phys(x, y)
            createobj = self.new_object({'draw-line': Line, 
                                         'draw-text': Text}[self.mode])
            createobj.begin(xi, yi)

            self.dragobj = createobj
            self.dragobj_xor = Move(self.dragobj)
            self.objects.append(self.dragobj_xor)

            self.paint_xor_objects = True
            self.dragobj_xor.show(xi, yi)
            self.selected_object = createobj
            self.mode = 'arrow'
            self.redraw()
            self.emit('request-cursor', 'arrow')
      
    def button_doubleclick(self, x, y, button):
        if self.mode == 'arrow' and button == 1:
            x, y = self.mouse_to_phys(x, y)
            for o in self.graph_objects:
                if o.hittest_handles(x, y):
                    self.emit('object-doubleclicked', o)
                    o.emit('modified')
                    break
     
    def button_release(self, x, y, button):
        if self.mode == 'zoom':
            if button == 2:
                self.autoscale()
                self.redraw(True)
            elif button == 1 or button == 3:
                self.rubberband.hide()
                self.redraw()
                self.paint_xor_objects = False

                zix, ziy = self.mouse_to_data(self.pixx, self.pixy)
                zfx, zfy = self.mouse_to_data(x, y)

                _xmin, _xmax = min(zix, zfx), max(zix, zfx)
                _ymin, _ymax = min(zfy, ziy), max(zfy, ziy)

                if button == 3:
                    _xmin, _xmax = self.axis_bottom.transform(_xmin), self.axis_bottom.transform(_xmax)
                    _ymin, _ymax = self.axis_left.transform(_ymin), self.axis_left.transform(_ymax)

                    xmin, xmax = self.zoomout(self.axis_bottom.transform(self.xmin), 
                                              self.axis_bottom.transform(self.xmax), _xmin, _xmax)
                    ymin, ymax = self.zoomout(self.axis_left.transform(self.ymin), 
                                              self.axis_left.transform(self.ymax), _ymin, _ymax)

                    xmin, xmax = self.axis_bottom.invtransform(xmin), self.axis_bottom.invtransform(xmax)
                    ymin, ymax = self.axis_left.invtransform(ymin), self.axis_left.invtransform(ymax)
                else:
                    xmin, xmax, ymin, ymax = _xmin, _xmax, _ymin, _ymax
                self.zoom(xmin, xmax, ymin, ymax)
                self.reshape()
                self.redraw(True)
        elif self.mode == 'hand':
            if self.selected_function is not None:
                self.selected_function.set_reg(True)
                self.selected_function.move(*self.mouse_to_data(x, y))
                del self.objects[-1]
                self.paint_xor_objects = False
                self.redraw(True)
        elif self.mode == 's-reader':
            self.cross.hide()
            self.redraw()
            self.paint_xor_objects = False
        elif self.mode == 'd-reader':
            self.cross.hide()
            self.redraw()
            self.paint_xor_objects = False

        elif self.mode == 'arrow':
            if button == 1:
                if self.dragobj is not None:
                    self.dragobj.rec = True
                    self.dragobj.record_position()
                    self.dragobj = None
                    self.dragobj_xor.hide()
                    self.objects.remove(self.dragobj_xor)
                    self.paint_xor_objects = False
                    self.redraw()
        elif self.mode == 'range':
            if button is None:
                button = self.__button
            else:
                self.__button = button

            x, y = self.mouse_to_data(x, y)
            for d in self.selected_datasets:
                if button == 1:
                    d.range = (x, d.range[1])
                elif button == 3:
                    d.range = (d.range[0], x)
                elif button == 2:
                    d.range = (-inf, inf)
            self.rangehandle.hide()
            self.redraw()
            self.paint_xor_objects = False
  
    def button_motion(self, x, y, dragging):
        if self.mode == 'zoom' and dragging and hasattr(self, 'ix'):
            self.rubberband.move(self.ix, self.iy, *self.mouse_to_phys(x, y))
            self.redraw()
        elif self.mode == 'range' and dragging:
            self.rangehandle.move(*self.mouse_to_phys(x, y))
            self.redraw()
#            self.button_press(x, y)
        elif self.mode == 'hand' and dragging:
            if self.selected_function is not None:
                self.selected_function.move(*self.mouse_to_data(x, y))
                self._movefunc.move(*self.mouse_to_data(x, y))
                self.redraw()
        elif self.mode == 's-reader' and dragging:
            self.cross.move(*self.mouse_to_phys(x, y))
            self.redraw()
            self.emit('status-message', '%f, %f' % self.mouse_to_data(x, y))
        elif self.mode == 'd-reader' and dragging:
            qx, qy = self.mouse_to_data(x, y)
            distances = []
            closest_ind = []

            for d in self.datasets:
                dist = (d.xx-qx)*(d.xx-qx) + (d.yy-qy)*(d.yy-qy)
                arg = argmin(dist)
                closest_ind.append(arg)
                distances.append(dist[arg])

            ind = argmin(distances)
            dataset = self.datasets[ind]
            x, y = dataset.xx[closest_ind[ind]], dataset.yy[closest_ind[ind]]

            self.cross.move(*self.data_to_phys(x, y))
            self.redraw()
            self.emit('status-message', '%f, %f' % (x, y))
        elif self.mode == 'arrow':
            if not hasattr(self, 'res'):
                # not initialized yet, do nothing
                return
            x, y = self.mouse_to_phys(x, y)
            if self.dragobj is not None: # drag a handle on an object
                self.dragobj_xor.move(x, y)
                self.redraw()
                self.emit('request-cursor', 'none')
            else: # look for handles
                for o in self.graph_objects:
                    if o.hittest(x, y):
                        self.emit('request-cursor', 'hand')
                        break
                else:
                    self.emit('request-cursor', 'arrow')

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
        symbol:S, fill:S, color:I, size:I, linetype:S,
        linestyle:S, linewidth:I,
        xfrom:D, xto:D 
    ],
    functions [
        id:S, func:S, name:S,
        params:S, lock:S, use:I
    ],
    lines [ id:S, position:S ],
    text [ id:S, position:S, text:S ]
]
"""
register_class(Graph, desc)

