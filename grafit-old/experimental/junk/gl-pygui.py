import sys
import time
import math
from itertools import izip
from qt import *
from qtcanvas import *
from qtgl import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from Numeric import *
from p import makedata


import math
from GUI import Window, Task, application
from GUI.GL import GLView
from OpenGL import GL

#----------------------------------------------------------------------------






class Mouse:
    Left, Right, Middle = range(3)
    Press, Release, Move = range(3)

class Key:
    Shift, Ctrl, Alt = range(3)

class Direction:
    Left, Right, Top, Bottom = range(4)

class Coordinates:
    Pixel, Data, Physical = range(3)


# Coordinate systems
# ------------------
# cm (centimeters, origin is bottom left corner)
# mouse (pixels, origin is top left corner)
# data (x and y, log if nescessary, origin is 0, 0)


"""
GraphWidget
-------------

to:
---
clear()
render_data(x, y, range, style)
render_line(x1, y1, x2, y2)
update()
rubberband_begin(x0, y0)
rubberband_continue(x, y)
rubberband_end(x, y)
rangemarker_begin(x0, direction)
rangemarker_continue(x)
rangemarker_end(x, y)
coords(coor)
transform(x, y, coor_f, coor_t)

from:
-----
mouse_event(event_type, x, y, clicks, button, keys)
key_event(key)
"""

##############################################################################

# symbols are reasonably fast for 100000 points total. Still slower than PyQwt

def output(text, size):
    glPushMatrix()
    glScale(1./size, 1./size, 1./size)

    w = 0.
    for char in text:
        w += glutStrokeWidth(GLUT_STROKE_ROMAN,ord(char))
    glTranslatef(-w/2., 0., 0.)
    for c in text:
        glutStrokeCharacter(GLUT_STROKE_ROMAN,ord(c))
    glPopMatrix()


def tics(fr, to):
    # 5-8 major tics
    # order of preference: 1eN, 5eN, 4eN, 3eN, 2eN
    if fr == to:
        return [fr]
    exponent = floor(log10(to-fr)) - 1

    for interval in (1,5,4,6,7,8,9,3,2):
        interval = interval * (10**exponent)
        if fr%interval == 0:
            first = fr
        else:
            first = fr + (interval-fr%interval)
        rng = arange(first, to, interval)
        if 5 <= len(rng) <= 8:
            return rng

    exponent += 1
    for interval in (1,5,4,6,7,8,9,3,2):
        interval = interval * (10**exponent)
        if fr%interval == 0:
            first = fr
        else:
            first = fr + (interval-fr%interval)
        rng = arange(first, to, interval)
        if 5 <= len(rng) <= 8:
            return rng
    return []


class GLGraphWidget(GLView):
    def __init__(self, *args, **kwds):
        fmt = QGLFormat()
#        fmt.setDoubleBuffer(False)
        GLView.__init__(self, *args, **kwds)

        # mouse rubberbanding coordinates
        self.sx = None
        self.px = None
        self.sy = None
        self.py = None
#        self.graph = graph


        self.buf =  False
        self.res = self.size[0]/100.
        self.i = 0

        self.xx = {}
        self.yy = {}
        self.range = {}

        self.xx[0] = arange(9000.)/1000
        self.yy[0] = sin(self.xx[0])

        self.xx[1] = arange(10000.)/1000
        self.yy[1] = cos(self.xx[1])

        self.xx[2] = arange(1000.)/1000
        self.yy[2] = tan(self.xx[2])


        self.colors = {}
        self.colors[0] = (0.0, 0.1, 0.6)
        self.colors[1] = (0.4, 0.0, 0.1)

        self.set_range(0.0, 100.5)
        self.autoscale()
 
    def paint_axes(self):
        glLoadIdentity()

        glTranslatef(-1., -1., 0.)
        glTranslatef(0.1, 0.1, 0.)

        glColor3f(0.0,0.0,0.0)

        glBegin(GL_LINES)
        glVertex3f(    0.0,    0.0, 0.0)
        glVertex3f(    1.8,    0.0, 0.0)

        glVertex3f(    0.0,    0.0, 0.0)
        glVertex3f(    0.0,    1.8, 0.0)

        glVertex3f(    0.0,    1.8, 0.0)
        glVertex3f(    1.8,    1.8, 0.0)

        glVertex3f(    1.8,    1.8, 0.0)
        glVertex3f(    1.8,    0.0, 0.0)
        glEnd()

        #x tics

        glPushMatrix()
        glScalef(1.8/(self.xxmax-self.xxmin), 1., 1.)
        glTranslate(-self.xxmin, 0, 0)

        glBegin(GL_LINES)
        for x in tics(self.xxmin, self.xxmax):
            glVertex3f(x, 0.0, 0.0)
            glVertex3f(x, 0.03, 0.0)
        glEnd()
        glPopMatrix()

        #y tics

        glPushMatrix()
        glScalef(1., 1.8/(self.yymax-self.yymin), 1.)
        glTranslate(0, -self.yymin, 0)

        glBegin(GL_LINES)
        for y in tics(self.yymin, self.yymax):
            glVertex3f(0, y, 0.0)
            glVertex3f(0.03, y, 0.0)
        glEnd()

        glPopMatrix()

#        glDepthRange( 0, 0 )
        glLoadIdentity()

        glTranslatef(-1., -1., 0.)
        glTranslatef(0.1, 0.1, 0.)

        for x in tics(self.xxmin, self.xxmax):
            glPushMatrix()
            glScalef(1.8/(self.xxmax-self.xxmin), 1., 1.)
            glTranslatef(-self.xxmin, 0., 0.)

            glPushMatrix()
            
            glTranslatef(x, -0.07, 0)
            glScalef((self.xxmax-self.xxmin)/1.8, 1., 1.)
            
            output(str(x), 3000)

            glPopMatrix()
            glPopMatrix()

        for y in tics(self.yymin, self.yymax):
            glPushMatrix()
            glScalef(1., 1.8/(self.yymax-self.yymin), 1.)
            glTranslatef(0, -self.yymin, 0.)

            glPushMatrix()
            
            glTranslatef(-0.07, y, 0)
            glScalef(1., (self.yymax-self.yymin)/1.8, 1.)
            
            output(str(y), 3000)

            glPopMatrix()
            glPopMatrix()


        glPushMatrix()
        glLoadIdentity()

        self.initmatrix = glGetDoublev(GL_PROJECTION_MATRIX)

        # go to origin
        glTranslatef(-0.9, -0.9, 0.)

        # scale to coordinates
        glScalef(1.8/(self.xxmax-self.xxmin), 1.8/(self.yymax-self.yymin), 1)

        # go to (0, 0)
        glTranslatef(-self.xxmin, -self.yymin, 0)
#
#            glTranslate(-1., -1., 0)
#            glScalef(2./(self.xxmax-self.xxmin), 2./(self.yymax-self.yymin), 1.)
#            glTranslatef(-self.xxmin, -self.yymin, 0)
        
        self.projmatrix = glGetDoublev(GL_PROJECTION_MATRIX)

        glPopMatrix()

    def render(self):
        self.mvmatrix = glGetDoublev(GL_MODELVIEW_MATRIX)
        self.viewport = glGetIntegerv(GL_VIEWPORT)
        if not self.buf:
            glClear(GL_COLOR_BUFFER_BIT)
            self.paint_axes()

            glPushMatrix()
            glLoadIdentity()

            x, _, _ = gluProject(self.fr, 0.0, 0.0, self.mvmatrix, self.projmatrix, self.viewport)
            x1, _ = self.mouse_to_ident(x, 0.)

            x, _, _ = gluProject(self.to, 0.0, 0.0, self.mvmatrix, self.projmatrix, self.viewport)
            x2, _ =  self.mouse_to_ident(x, 0.)

            glClipPlane(GL_CLIP_PLANE0, [  1.,  0.,  0.,  min(0.9, -x1) ])
            glClipPlane(GL_CLIP_PLANE1, [ -1.,  0.,  0.,  min(0.9, x2) ])
            glClipPlane(GL_CLIP_PLANE2, [  0.,  1.,  0.,  0.9 ])
            glClipPlane(GL_CLIP_PLANE3, [  0., -1.,  0.,  0.9 ])

            glEnable(GL_CLIP_PLANE0)
            glEnable(GL_CLIP_PLANE1)
            glEnable(GL_CLIP_PLANE2)
            glEnable(GL_CLIP_PLANE3)

            glLoadMatrixd(self.projmatrix)
            glPointSize(5)
            glCallList(1)

            glDisable(GL_CLIP_PLANE0)
            glDisable(GL_CLIP_PLANE1)
            glDisable(GL_CLIP_PLANE2)
            glDisable(GL_CLIP_PLANE3)

            glPopMatrix()
        else:
            glPushMatrix()
            glLoadIdentity()

            glColor3f(1.0,1.0,0.0)
            glLineStipple (1, 0x4444) # dotted
            glEnable(GL_LINE_STIPPLE)
            glLogicOp(GL_XOR)
            glEnable(GL_COLOR_LOGIC_OP)

            glBegin(GL_LINE_LOOP)
            glVertex3f(self.ix, self.iy, 0.0)
            glVertex3f(self.ix, self.py, 0.0)
            glVertex3f(self.px, self.py, 0.0)
            glVertex3f(self.px, self.iy, 0.0)
            glEnd()

            glBegin(GL_LINE_LOOP)
            glVertex3f(self.ix, self.iy, 0.0)
            glVertex3f(self.ix, self.sy, 0.0)
            glVertex3f(self.sx, self.sy, 0.0)
            glVertex3f(self.sx, self.iy, 0.0)
            glEnd()

            glDisable(GL_LINE_STIPPLE)
            glDisable(GL_COLOR_LOGIC_OP)
            glPopMatrix()


    def viewport_changed(self):
        self.w, self.h = self.width, self.height
        print >>sys.stderr, self.width, self.height
        self.marginx = int(self.w * 0.1)
        self.marginy = int(self.h * 0.1)
        glViewport( 0, 0, self.width, self.height )
        self.viewport = glGetIntegerv(GL_VIEWPORT)
        self.res = self.w/100.

    def init_context(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glDisable(GL_DEPTH_TEST)
        glMatrixMode (GL_PROJECTION)
        glLoadIdentity ()
        gluOrtho2D (0, self.width, 0, self.height)
        self.make_data_list()

        self.mvmatrix = glGetDoublev(GL_MODELVIEW_MATRIX)
        self.viewport = glGetIntegerv(GL_VIEWPORT)

    def make_data_list(self):
        V3f = glVertex3f
        t = time.time()

        dx =  self.res * (self.xxmax-self.xxmin)/self.width
        dy =  self.res * (self.yymax-self.yymin)/self.height

        if False:
            glNewList(1, GL_COMPILE)
            for k in self.xx.keys():
                glBegin(GL_QUADS)
                for x,y in izip(self.xx[k], self.yy[k]):
                    V3f(x, y, 0)
                    V3f(x+dx, y, 0)
                    V3f(x+dx, y+dy, 0)
                    V3f(x, y+dy, 0)
                glEnd()
            glEndList()
        else:
            glNewList(1, GL_COMPILE)
            for k in self.xx.keys():
                makedata(self.xx[k], self.yy[k], dx, dy)
            glEndList()
 

        print 300000./(time.time()-t), "vertices per second"

    def mouse_to_ident(self, xm, ym):
        realy = self.viewport[3] - ym - 1
        x, y, _ = gluUnProject(xm, realy, 0.0, self.mvmatrix, self.initmatrix, self.viewport)
        return x, y

    def mouse_to_real(self, xm, ym):
        realy = self.viewport[3] - ym - 1
        x, y, _ = gluUnProject(xm, realy, 0.0, self.mvmatrix, self.projmatrix, self.viewport)
        return x, y

    def autoscale(self):
        self.xxmin = min(self.xx[0])
        self.yymin = min(self.yy[0])
        self.xxmax = max(self.xx[0])
        self.yymax = max(self.yy[0])

    def set_range(self, fr, to):
        self.fr, self.to  = fr, to

    def zoom(self, xmin, xmax, ymin, ymax):
        self.xxmin, self.xxmax, self.yymin, self.yymax = xmin, xmax, ymin, ymax

 
    def zoomout(self,x1, x2,x3, x4):
        a = (x2-x1)/(x4-x3); c = x1 - a*x3;
        f1 = a*x1 + c; f2 = a*x2 + c;
        return min(f1, f2), max(f1, f2)

    def rubberband_begin(self, x, y):
        self.buf = True
        self.pixx, self.pixy = x, y
        self.ix, self.iy = self.mouse_to_ident(x, y)
        self.px, self.py, self.sx, self.sy = self.ix, self.iy, self.ix, self.iy
        self.zix, self.ziy = self.mouse_to_real(x, y)
        self.rubberband_continue(x, y)

    def rubberband_active(self):
        return self.px is not None
        

    def rubberband_continue(self, x, y):
        self.px, self.py = self.sx, self.sy
        self.sx, self.sy = self.mouse_to_ident(x, y)
        self.updateGL()

    def rubberband_end(self, x, y):
        self.rubberband_continue(x, y)
        self.buf = False
        return self.pixx, self.pixy, x, y

    btns = {Qt.LeftButton: Mouse.Left, Qt.MidButton: Mouse.Middle, Qt.RightButton: Mouse.Right, 0:None}

    def mouseMoveEvent(self, e):
        self.graph.mouse_event(Mouse.Move, e.x(), e.y(), self.btns[e.button()])
    def mousePressEvent(self, e):
        self.graph.mouse_event(Mouse.Press, e.x(), e.y(), self.btns[e.button()])

    def mouseReleaseEvent(self, e):
        self.graph.mouse_event(Mouse.Release, e.x(), e.y(), self.btns[e.button()])
#        x, y = self.mouse_to_real(e.x(), e.y())
#        self.set_range(x, self.to)
#        self.updateGL()
#        return

    def mouse_down(self,event, *args, **kwds):
        print dir(event)
        print args, kwds

#        for event in self.track_mouse():
            
class glGraph(object):
    def __init__(self, parent=None):
        self.win = QTabWidget(parent)
        self.win.setTabShape(self.win.Triangular)
        self.win.setTabPosition(self.win.Bottom)
        self.win.graph = self

        self.main = QHBox(self.win)
        self.win.addTab(self.main, 'graph')

        self.gwidget = GLGraphWidget(self, self.main)

    def mouse_event(self, event, x, y, button):
        if event == Mouse.Press:
            if button in [Mouse.Left, Mouse.Right]:
                self.gwidget.rubberband_begin(x, y)

        elif event == Mouse.Move:
            if self.gwidget.rubberband_active():
                self.gwidget.rubberband_continue(x, y)
#        x, y = self.mouse_to_real(e.x(), e.y())
#        self.set_range(x, self.to)
#        self.updateGL()
#        return
        elif event == Mouse.Release:
            if button == Mouse.Middle:
                self.gwidget.autoscale()
                self.gwidget.make_data_list()
                self.gwidget.update()
            elif button == Mouse.Left or button == Mouse.Right:
#                self.px, self.py = self.sx, self.sy
#                self.sx, self.sy = self.ix, self.iy
#                self.mouseMoveEvent(e)
#                if self.px == self.sx or self.py == self.sy: #can't zoom!
#                    self.px, self.py = None, None
#                    return
                self.zix, self.ziy, self.zfx, self.zfy = self.gwidget.rubberband_end(x, y)

                self.zix, self.ziy = self.gwidget.mouse_to_real(self.zix, self.ziy)
                self.zfx, self.zfy = self.gwidget.mouse_to_real(self.zfx, self.zfy)
#
                self._xmin, self._xmax = min(self.zix, self.zfx), max(self.zix, self.zfx)
                self._ymin, self._ymax = min(self.zfy, self.ziy), max(self.zfy, self.ziy)

                if button == Mouse.Right:
                    self.xxmin, self.xxmax = self.gwidget.zoomout(self.xxmin, self.xxmax, self._xmin, self._xmax)
                    self.yymin, self.yymax = self.gwidget.zoomout(self.yymin, self.yymax, self._ymin, self._ymax)
                else:
                    self.xxmin, self.xxmax, self.yymin, self.yymax = self._xmin, self._xmax, self._ymin, self._ymax
                self.gwidget.zoom(self.xxmin, self.xxmax, self.yymin, self.yymax)

                self.gwidget.make_data_list()
                self.gwidget.updateGL()
            self.px, self.py = None, None



##############################################################################
view = GLGraphWidget(size = (300, 300))
win = Window(title = "Gears")
win.place(view, sticky = "nsew")
view.become_target()
win.shrink_wrap()
win.show()

application().run()


#    app=QApplication(sys.argv)
#    g = glGraph()
#    app.setMainWidget(g.win)
#    g.win.show()
#    app.exec_loop()

