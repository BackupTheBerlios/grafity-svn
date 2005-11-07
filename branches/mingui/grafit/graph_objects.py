from grafit.signals import HasSignals
from grafit.settings import DATADIR
from grafit.project import wrap_attribute
from grafit.actions import action_from_methods2, StopAction
from grafit.graph_dataset import Function

from OpenGL.GL import *
from OpenGL.GLU import *

from math import sqrt
import sys

class XorDraw(object):
    def __init__(self, graph):
        self.graph = graph
        self.coords = None
        self.previous = None
        self.need_redraw = False

    def draw(self, *coords):
        raise NotImplementedError

    def show(self, *pos):
        self.coords = pos
        self.previous = None
        self.need_redraw = True

    def hide(self):
        self.need_redraw = True
        self.coords = None

    def move(self, *pos):
        if not self.need_redraw:
            self.previous = self.coords
        self.coords = pos
        self.need_redraw = True

    def redraw(self):
        if self.need_redraw:
            if self.previous is not None:
                self.draw(*self.previous)
            if self.coords is not None:
                self.draw(*self.coords)
            self.need_redraw = False


class Handle(object):
    def __init__(self, graph):
        self.graph = graph
        self.posx, self.posy = '0%', '0%'

    def set_posx(self, value):
        self._posx = value
        self._x, self.p = self.graph.pos2x(value)
    def get_posx(self):
        return self._posx
    posx = property(get_posx, set_posx)

    def set_posy(self, value):
        self._posy = value
        self._y, self.q = self.graph.pos2y(value)
    def get_posy(self):
        return self._posy
    posy = property(get_posy, set_posy)

    def set_x(self, value):
        self._x = value
        self._posx = self.graph.x2pos(value, self.p)
    def get_x(self):
        return self._x
    x = property(get_x, set_x)

    def set_y(self, value):
        self._y = value
        self._posy = self.graph.y2pos(value, self.q)
    def get_y(self):
        return self._y
    y = property(get_y, set_y)

    def draw(self):
        glColor3f(0, 0, 1) # blue
        glBegin(GL_LINE_LOOP)
        glVertex3d(self.x-1, self.y-1, 0.0)
        glVertex3d(self.x+1, self.y-1, 0.0)
        glVertex3d(self.x+1, self.y+1, 0.0)
        glVertex3d(self.x-1, self.y+1, 0.0)
        glEnd()

        glColor3f(.7, .2, 0)
        if self.p == 'x':
            glBegin(GL_LINES)
            glVertex3d(self.x, self.y-1, 0)
            glVertex3d(self.x, self.y+1, 0)
            glEnd()
        if self.q == 'y':
            glBegin(GL_LINES)
            glVertex3d(self.x-1, self.y, 0)
            glVertex3d(self.x+1, self.y, 0)
            glEnd()

    def hittest(self, x, y):
        return self.x-1<=x<= self.x+1 and self.y-1<=y<=self.y+1

    def move(self, x, y):
        self.x, self.y = x, y

class GraphObject(HasSignals):
    """
    The position of a graph object is completely defined by the 
    position of one or more handles.

    When the user moves a handle it may be nescessary to move some
    of the others as well.
    """
    def __init__(self, graph, location):
        self.graph, self.data = graph, location
        self.handles = []
        self.active_handle = None
        self.dragstart = None

    def read_position(self):
        if self.data.position == '':
            self.data.position = '0%;0% 50%;50%'
        for hpos, handle in zip(self.data.position.split(' '), self.handles):
            handle.posx, handle.posy = hpos.split(';')

    def record_position(self, state):
        state['prev'] = self.data.position
        self.data.position = ' '.join(h.posx+';'+h.posy for h in self.handles).encode('utf-8')
        state['pos'] = self.data.position
        self.emit('modified')
    def undo_record_position(self, state):
        self.data.position = state['prev']
        self.read_position()
        self.graph.emit('redraw')
        self.emit('modified')
    def redo_record_position(self, state):
        self.data.position = state['pos']
        self.read_position()
        self.graph.emit('redraw')
        self.emit('modified')
    record_position = action_from_methods2('graph/move-object',
                            record_position, undo_record_position, redo=redo_record_position)

    def move_active_handle(self, x, y, record=True):
        """
        Move the active handle to (x, y)
        """
        if self.active_handle is None:
            return
        self.active_handle.move(x, y)
        if record:
            self.record_position()

    def nudge(self, x, y, record=True):
        for h in self.handles:
            h.move(h.x+x, h.y+y)
        if record:
            self.record_position()

    def draw(self):
        """
        Draw the object, given the position of the handles
        """
        raise NotImplementedError

    def hittest_handles(self, x, y):
        """
        Tests if a point x, y is on a handle and sets active_handle
        """
        for h in self.handles:
            if h.hittest(x, y):
                self.active_handle = h
                return True
        self.active_handle = None
        return False

    def hittest(self, x, y):
        """
        Tests if a point x, y is on the object
        """
        raise NotImplementedError

    def bounding_box(self):
        """
        Returns the bounding box (xmin, ymin, xmax, ymax)
        of the object
        """
        raise NotImplementedError

    def draw_handles(self):
        for h in self.handles:
            h.draw()

class Line(GraphObject):
    def __init__(self, graph, data):
        GraphObject.__init__(self, graph, data)
        self.handles.append(Handle(graph))
        self.handles.append(Handle(graph))
        self.read_position()

    def draw(self):
        glColor3f(.3, .5, .7)
        glBegin(GL_LINES)
        glVertex3d(self.handles[0].x, self.handles[0].y, 0)
        glVertex3d(self.handles[1].x, self.handles[1].y, 0)
        glEnd()

    def begin(self, x, y):
        self.handles[0].move(x, y)
        self.handles[1].move(x, y)
        self.active_handle = self.handles[1]

    def hittest(self, x3, y3):
        x1, x2 = self.handles[0].x, self.handles[1].x
        y1, y2 = self.handles[0].y, self.handles[1].y

        if (x1, y1) == (x2, y2):
            return (x1-x3)*(x1-x3) + (y1-y3)*(y1-y3) <= 1
            
        u = ((x3-x1)*(x2-x1) + (y3-y1)*(y2-y1)) / ((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))
        x = x1 + u*(x2-x1)
        y = y1 + u*(y2-y1)
        if (x3-x)*(x3-x) + (y3-y)*(y3-y) <= 1:
            self.dragstart = x3, y3
            return True
        else:
            self.dragstart = None
            return False

    id = wrap_attribute('id')

    _x1 = property(lambda self: self.handles[0].posx,
                   lambda self, value: (setattr(self.handles[0], 'posx', value), 
                                        self.record_position(),
                                        self.graph.emit('redraw')))
    _y1 = property(lambda self: self.handles[0].posy,
                   lambda self, value: (setattr(self.handles[0], 'posy', value), 
                                        self.record_position(),
                                        self.graph.emit('redraw')))
    _x2 = property(lambda self: self.handles[1].posx,
                   lambda self, value: (setattr(self.handles[1], 'posx', value), 
                                        self.record_position(),
                                        self.graph.emit('redraw')))
    _y2 = property(lambda self: self.handles[1].posy,
                   lambda self, value: (setattr(self.handles[1], 'posy', value), 
                                        self.record_position(),
                                        self.graph.emit('redraw')))


class Text(GraphObject):
    def __init__(self, graph, data):
        GraphObject.__init__(self, graph, data)
        self.handles.append(Handle(graph))
        self.read_position()

    def draw(self):
        facesize = 12*self.graph.magnification
        self.graph.textpainter.render_text(self.text, facesize, 
                                           self.handles[0].x, self.handles[0].y,
                                           align_x='bottom', align_y='left')

    def get_text(self): return self.data.text.decode('utf-8')
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

    def begin(self, x, y):
        self.handles[0].move(x, y)
        self.active_handle = self.handles[0]

    def get_x1(self): return self.handles[0].posx
    def set_x1(self, value): self.handles[0].posx = value; self.emit('modified'); self.graph.emit('redraw')
    _x1 = property(get_x1, set_x1)

    def get_y1(self): return self.handles[0].posy
    def set_y1(self, value): self.handles[0].posy = value; self.emit('modified'); self.graph.emit('redraw')
    _y1 = property(get_y1, set_y1)

    def hittest(self, x, y):
        h = self.handles[0].hittest(x, y)
        if h:
            self.dragstart = x, y
        else:
            self.dragstart = None
        return h 

    id = wrap_attribute('id')


class Move(XorDraw):
    def __init__(self, obj):
        XorDraw.__init__(self, obj.graph)
        self.obj = obj

    def draw(self, x, y):
        if self.obj.dragstart:
            # move entire object
            x0, y0 = self.obj.dragstart
            self.obj.nudge(x-x0, y-y0, False)
            self.obj.dragstart = x, y
        else:
            # move handle
            self.obj.move_active_handle(x, y, False)
        self.obj.draw()

class Rubberband(XorDraw):
#    def __init__(self, graph):
#        XorDraw.__init__(self, graph)

    def draw(self, ix, iy, sx, sy):
        glColor3f(1.0,1.0,0.0) # blue
        glLineStipple (1, 0x4444) # dotted
        glEnable(GL_LINE_STIPPLE)

        glBegin(GL_LINE_LOOP)
        glVertex3d(ix, iy, 0.0)
        glVertex3d(ix, sy, 0.0)
        glVertex3d(sx, sy, 0.0)
        glVertex3d(sx, iy, 0.0)
        glEnd()

        glDisable(GL_LINE_STIPPLE)

class Rangehandle(XorDraw):
    def draw(self, x, y):
        glColor3f(1.0,0.5,1.0)
        glBegin(GL_LINES)
        glVertex3d(x, 0, 0)
        glVertex3d(x, self.graph.plot_height, 0)
        glEnd()

class Cross(XorDraw):
#    def __init__(self, graph):
#        XorDraw.__init__(self, graph)

    def draw(self, x, y):
        glColor3f(1.0,0.5,1.0)
        glBegin(GL_LINES)
        glVertex3d(x-15, y, 0)
        glVertex3d(x+15, y, 0)

        glVertex3d(x, y-15, 0)
        glVertex3d(x, y+15, 0)
        glEnd()

class DrawFunction(XorDraw):
    def __init__(self, graph, function):
        XorDraw.__init__(self, graph)
        self.f = Function(self.graph, totalcolor=(55, 255, 255))
        self.f.func = function

    def draw(self, x, y):
        self.f.func.move(x, y)
        self.f.paint()




