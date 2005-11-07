import sys
import time
import string
import tempfile

from grafit.arrays import *
from OpenGL.GL import *

from grafit.signals import HasSignals
from grafit.project import Item, wrap_attribute, register_class, create_id
from grafit.actions import action_from_methods, action_from_methods2, StopAction
from grafit.graph_axis import Axis, Grid
from grafit.graph_objects import Rubberband, Cross, Line, Text, Move, DrawFunction, Rangehandle
from grafit.graph_dataset import Dataset, Function
from grafit.graph_text import FONTFILE, TextPainter, encodeTTFasPS
from grafit.graph_render import *
from grafit.settings import DATADIR
from grafit.thirdparty.ft2font import FT2Font

import wx

log = False

if log:
    def wrap_func(func):
        def r(*args, **kwds):
            print func.__name__, args, kwds
            return func(*args, **kwds)
        return r

    g = {}
    for name, func in dict(globals()).iteritems():
        if name.startswith('gl') and hasattr(func, '__call__'):
            g[name] = wrap_func(func)

    globals().update(g)

class Graph(Item, HasSignals):
    def __init__(self, project, name=None, parent=None, location=None):
        Item.__init__(self, project, name, parent, location)
    
        self.paint_xor_objects =  False
        self.selected_datasets = []

        self.mode = 'arrow'

        self.graph_objects = []
        self.dragobj = None

        self.selected_object = None

        self.plot_height = 100
        self.plot_width = 100

        self.datasets = []
        if location is not None:
            for i, l in enumerate(self.data.datasets):
                if not l.id.startswith('-'):
                    self.datasets.append(Dataset(self, i))
                    self.datasets[-1].connect('modified', self.on_dataset_modified)
            for l in self.data.lines:
                if not l.id.startswith('-'):
                    self.graph_objects.append(Line(self, l))
            for l in self.data.text:
                if not l.id.startswith('-'):
                    self.graph_objects.append(Text(self, l))

        self.functions = []
#        if location is not None:
#            for i in range(len(self.data.functions)):
#                if not self.data.functions[i].id.startswith('-'):
#                    f = Function(self, i)
#                    self.functions.append(f)
#                    f.connect('modified', self.on_dataset_modified)
#                    f.func.connect('modified', self.on_dataset_modified)

        self.ps = False

        self.axis_top = Axis('top', self)
        self.axis_bottom = Axis('bottom', self)
        self.axis_right = Axis('right', self)
        self.axis_left = Axis('left', self)

        self.axes = [self.axis_top, self.axis_right, self.axis_bottom, self.axis_left]

        self.grid_h = Grid('horizontal', self)
        self.grid_v = Grid('vertical', self)

        self.set_range(0.0, 100.5)
        if location is None:
            self.xmin, self.ymin = 0,0  
            self.ymax, self.xmax = 10, 10
        self.newf()

        if self.xtype == '':
            self._xtype = 'linear'
        if self.ytype == '':
            self._ytype = 'linear'
        self.selected_function = None

        self.rubberband = Rubberband(self)
        self.cross = Cross(self)
        self.rangehandle = Rangehandle(self)

        self.objects = [self.rubberband, self.cross, self.rangehandle]
        self.textpainter = TextPainter(self)

        self.axis_title_font_size = 12.
        self.background_color = (1., 1., 1., 1.)
        self.pwidth = 120.
        self.pheight = 100.

        self.recalc = True

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

    def newf(self):
#        ind = self.data.functions.append(id=create_id())
        f = Function(self)
        f.connect('modified', self.on_dataset_modified)
        f.func.connect('modified', self.on_dataset_modified)
        f.func.connect('add-term', self.on_dataset_modified)
        f.func.connect('remove-term', self.on_dataset_modified)
        self.functions.append(f)
        self.emit('add-function', f)
        return f

    def create_legend(self):
        legend = self.new_object(Text)
        legend.text = '\n'.join('@%d@'%i + str(d) for i, d in enumerate(self.datasets))

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

    def pos2y(self, pos):
        if pos.endswith('%'):
            return float(pos[:-1])*self.plot_height/100., '%'
        elif pos.endswith('y'):
            return self.data_to_phys(self.ymin, float(pos[:-1]))[1], 'y'
        elif pos.endswith('mm'):
            return float(pos[:-2]), 'mm'
        else:
            return float(pos), 'mm'

    def pos2x(self, pos):
        if pos.endswith('%'):
            return float(pos[:-1])*self.plot_width/100., '%'
        elif pos.endswith('x'):
            return self.data_to_phys(float(pos[:-1]), self.xmin)[0], 'x'
        elif pos.endswith('mm'):
            return float(pos[:-2]), 'mm'
        else:
            return float(pos), 'mm'

    def x2pos(self, x, typ):
        if typ=='%':
            return str(x*100./self.plot_width)+'%'
        elif typ=='x':
            return str(self.phys_to_data(x, 0)[0])+'x'
        elif typ=='mm':
            return str(x)+'mm'

    def y2pos(self, y, typ):
        if typ=='%':
            return str(y*100./self.plot_height)+'%'
        elif typ=='y':
            return str(self.phys_to_data(0, y)[1])+'y'
        elif typ=='mm':
            return str(y)+'mm'

    def data_to_phys(self, x, y):
        """
        Takes a point x,y in data coordinates and transforms to
        physical coordinates
        """
        x, xmin, xmax = map(self.axis_bottom.transform, (x, self.xmin, self.xmax))
        y, ymin, ymax = map(self.axis_left.transform, (y, self.ymin, self.ymax))

        px = self.plot_width * (x-xmin)/(xmax-xmin)
        py = self.plot_height * (y-ymin)/(ymax-ymin)

#        bt = self.axis_bottom.transform
#        lt = self.axis_left.transform
#
#        px = self.plot_width * (bt(x) - bt(self.xmin)) / (bt(self.xmax) - bt(self.xmin))
#        py = self.plot_height * (bt(y) - bt(self.ymin)) / (bt(self.ymax) - bt(self.ymin)) 

        return px, py

    def phys_to_data(self, x, y):
        """
        Takes a point x,y in physical coordinates and transforms to
        data coordinates
        """
        xmin, xmax = map(self.axis_bottom.transform, (self.xmin, self.xmax))
        ymin, ymax = map(self.axis_left.transform, (self.ymin, self.ymax))

        px = x*(xmax-xmin)/self.plot_width + xmin
        py = y*(ymax-ymin)/self.plot_height + ymin

        return self.axis_bottom.invtransform(px), self.axis_left.invtransform(py)

    def mouse_to_phys(self, xm, ym):
        x = (xm / self.res) - self.marginl
        y = ((self.height_pixels-ym) / self.res) - self.marginb
        return x, y

    def mouse_to_data(self, xm, ym):
        x, y = self.mouse_to_phys(xm, ym)
        return self.phys_to_data(x, y)

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

    def zoom_redo(self, state):
        self.xmin, self.xmax, self.ymin, self.ymax = state['new']
        self.reshape()
        self.redraw(True)

    def zoom_undo(self, state):
        self.xmin, self.xmax, self.ymin, self.ymax = state['old']
        self.reshape()
        self.redraw(True)

    def zoom_combine(self, state, other):
        return False

    zoom = action_from_methods2('graph-zoom', zoom_do, zoom_undo, redo=zoom_redo, combine=zoom_combine)

 
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

    def display(self, width=-1, height=-1):
        if not hasattr(self, 'listno'):
            return
        if width == -1 and height == -1:
            width, height = self.last_width, self.last_height
        else:
            self.last_width, self.last_height = width, height

        if not self.paint_xor_objects:
            if self.recalc:
                if not self.ps:
                    for i, d in enumerate(self.datasets):
                        glClearColor(*self.background_color)
                        glClear(GL_COLOR_BUFFER_BIT)

                        w, h, _, renderer=self.textpainter.render_text_chunk_symbol(str(i))
                        if renderer is not None:
                            renderer((w/2)/self.res, (h/2)/self.res)

                            i = wx.EmptyImage(w, h)
                            data = glReadPixels(int(self.marginl*self.res), int(self.marginb*self.res), 
                                                   int(w), int(h), GL_RGB, GL_UNSIGNED_BYTE)
                            i.SetData(data)
                            d._legend_wxbitmap = i.ConvertToBitmap()
                    self.emit('shape-changed')

                glDeleteLists(self.listno, 1)
                glNewList(self.listno, GL_COMPILE)

                glClearColor(*self.background_color)
                glClear(GL_COLOR_BUFFER_BIT)

                # set up clipping
                glClipPlane(GL_CLIP_PLANE0, [  1,  0,  0,  0 ])
                glClipPlane(GL_CLIP_PLANE1, [ -1,  0,  0,  self.plot_width ])
                glClipPlane(GL_CLIP_PLANE2, [  0,  1,  0,  0 ])
                glClipPlane(GL_CLIP_PLANE3, [  0, -1,  0,  self.plot_height ])

                if len(self.datasets):
		    for plane in [GL_CLIP_PLANE0, GL_CLIP_PLANE1, GL_CLIP_PLANE2, GL_CLIP_PLANE3]:
		       glEnable(plane)

                for d in self.datasets:
                    d.paint()
                for f in self.functions:
                    f.paint()

                if len(self.datasets):
	            for plane in [GL_CLIP_PLANE0, GL_CLIP_PLANE1, GL_CLIP_PLANE2, GL_CLIP_PLANE3]:
		        glDisable(plane)

                self.paint_axes()

                glEndList()
                self.recalc = False

            glCallList(self.listno)

            for axis in self.axes:
                axis.paint_text()
                axis.paint_title()

            for o in self.graph_objects:
                o.draw()
                if self.mode == 'arrow' and self.selected_object == o:
                    o.draw_handles()
        else:
            glLogicOp(GL_XOR)
            glEnable(GL_COLOR_LOGIC_OP)
            for o in self.objects:
                o.redraw()
            glDisable(GL_COLOR_LOGIC_OP)

    def reshape(self, width=-1, height=-1):
        if not hasattr(self, 'listno'):
            return
        t = time.time()
        if width == -1 and height == -1:
            width, height = self.last_width, self.last_height
        else:
            self.last_width, self.last_height = width, height

        # aspect ratio (width/height)
        self.aspect = self.pwidth/self.pheight 

        # resolution (in pixels/mm)
        self.res = min(width/self.pwidth, height/self.pheight)
        displaydpi = 100.
        self.displayres = displaydpi / 25.4     # 25.4 = mm/inch
        self.magnification = self.res / self.displayres

        # set width and height
        self.width_pixels, self.height_pixels = width, height
        self.width_mm = width / self.res
        self.height_mm = height / self.res

        # measure titles
        facesize = self.axis_title_font_size*self.magnification
        if self.xtitle != '':
            _, tith = self.textpainter.render_text(self.xtitle, facesize, 0, 0, 
                                                   measure_only=True)
        else:
            tith=0

        if self.ytitle != '':
            titw, _ = self.textpainter.render_text(self.ytitle, facesize, 0, 0, 
                                                 measure_only=True, orientation='v')
        else:
            titw=0

        # measure tick labels
        try:
            self.ticw = max(self.textpainter.render_text(self.axis_left.totex(y), 
                                                         facesize, 0, 0, measure_only=True)[0] 
                            for y in self.axis_left.tics(self.ymin, self.ymax)[0]) # :-)
        except ValueError:
            self.ticw = 0

        try:
            self.tich = max(self.textpainter.render_text(self.axis_bottom.totex(x), 
                                                         facesize, 0, 0, measure_only=True)[1] 
                            for x in self.axis_bottom.tics(self.xmin, self.xmax)[0])
        except ValueError:
            self.tich = 0

        # set margins (units are in mm)
        self.marginb = tith + self.tich + self.axis_title_font_size*self.magnification/2 + 2 
        self.margint = self.height_mm * 0.03
        self.marginl = titw + self.ticw + self.axis_title_font_size*self.magnification/2 + 2
        self.marginr = self.width_mm * 0.03

        if self.width_mm/self.height_mm > self.aspect:
            self.marginr += (self.width_mm - self.height_mm*self.aspect)/2
            self.marginl += (self.width_mm - self.height_mm*self.aspect)/2
        else:
            self.margint += (self.height_mm - self.width_mm/self.aspect)/2
            self.marginb += (self.height_mm - self.width_mm/self.aspect)/2

        self.plot_width = self.width_mm - self.marginl - self.marginr
        self.plot_height = self.height_mm - self.margint - self.marginb

        # resize the viewport
        glViewport(0, 0, int(width), int(height))
        self.viewport = glGetIntegerv(GL_VIEWPORT)

        # set opengl projection matrix with the origin
        # at the bottom left corner # of the graph 
        # and scale in mm
        glMatrixMode (GL_PROJECTION)
        glLoadIdentity()
        glTranslated(-1.+2.*self.marginl/self.width_mm, 
                     -1.+2.*self.marginb/self.height_mm, 0)
        glScaled(2./self.width_mm, 2./self.height_mm, 1)
#        print >>sys.stderr, 'R: ', time.time()-t, "seconds"


    def export_ascii(self, outfile):
        # mathtext is not rendered directly
        self.pstext = []

        save = self.width_pixels, self.height_pixels
        self.reshape(self.pwidth*self.displayres, self.pheight*self.displayres)

        d = tempfile.mkdtemp()
        filename = self.name + '.eps'
        f = open(os.path.join(d, filename), 'wb')

        gl2ps_BeginPage("Title", "Producer", self.viewport, f, filename)
        self.ps = True
        self.recalc = True
        self.display()
        self.ps = False
        gl2ps_EndPage()
        
        f.close()

        self.reshape(*save)

        f = open(d+'/'+filename, 'rb')
        for line in f:
            if line == '%%EndProlog\n':
                # insert encoded mathtext fonts
                # at the end of the prolog
                type42 = []
                type42.append(FONTFILE)
                for fn in ['r', 'ex', 'mi', 'sy', 'tt']:
                    type42.append(os.path.join(DATADIR, 'data', 'fonts', 
                                               'bakoma-cm', 'cm%s10.ttf'%fn))
                for font in type42:
                    print >>outfile, "%%BeginFont: "+FT2Font(str(font)).postscript_name
                    print >>outfile, encodeTTFasPS(font)
                    print >>outfile, "%%EndFont"
                outfile.write(line)
            elif line == 'showpage\n':
                # insert mathtext chunks
                # at the end of the file
                outfile.write(''.join(self.pstext))
                outfile.write(line)
            else:
                # copy lines
                outfile.write(line)
        f.close()

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

    def key_down(self, keycode):
        import wx
        if keycode == wx.WXK_DELETE and self.selected_object is not None:
            self.delete_object(self.selected_object)
    
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
        symbol:S, color:I, size:I, linetype:S,
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

import string
for w in string.whitespace:
    desc = desc.replace(w, '')

register_class(Graph, desc)
