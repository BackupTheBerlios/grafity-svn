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
rubberband_end()
rangemarker_begin(x0, direction)
rangemarker_continue(x)
rangemarker_end()
coords(coor)
transform(x, y, coor_f, coor_t)

from:
-----
mouse_event(event_type, button, clicks, keys)
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


class GLGraphWidget(QGLWidget):
    def __init__(self,parent=None, name=None):
        fmt = QGLFormat()
#        fmt.setDoubleBuffer(False)
        QGLWidget.__init__(self, fmt, parent, name)

        # mouse rubberbanding coordinates
        self.sx = None
        self.px = None
        self.sy = None
        self.py = None


        self.buf =  False
        self.res = self.size().width()/100.
        self.i = 0

        self.x = {}
        self.y = {}
        self.range = {}

        self.x[0] = arange(1000.)/1000
        self.y[0] = sin(self.x[0])

        self.set_range(0.1, 0.5)
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
        glScalef(1.8/(self.xmax-self.xmin), 1., 1.)
        glTranslate(-self.xmin, 0, 0)

        glBegin(GL_LINES)
        for x in tics(self.xmin, self.xmax):
            glVertex3f(x, 0.0, 0.0)
            glVertex3f(x, 0.03, 0.0)
        glEnd()
        glPopMatrix()

        #y tics

        glPushMatrix()
        glScalef(1., 1.8/(self.ymax-self.ymin), 1.)
        glTranslate(0, -self.ymin, 0)

        glBegin(GL_LINES)
        for y in tics(self.ymin, self.ymax):
            glVertex3f(0, y, 0.0)
            glVertex3f(0.03, y, 0.0)
        glEnd()

        glPopMatrix()

#        glDepthRange( 0, 0 )
        glLoadIdentity()

        glTranslatef(-1., -1., 0.)
        glTranslatef(0.1, 0.1, 0.)

        for x in tics(self.xmin, self.xmax):
            glPushMatrix()
            glScalef(1.8/(self.xmax-self.xmin), 1., 1.)
            glTranslatef(-self.xmin, 0., 0.)

            glPushMatrix()
            
            glTranslatef(x, -0.07, 0)
            glScalef((self.xmax-self.xmin)/1.8, 1., 1.)
            
            output(str(x), 3000)

            glPopMatrix()
            glPopMatrix()

        for y in tics(self.ymin, self.ymax):
            glPushMatrix()
            glScalef(1., 1.8/(self.ymax-self.ymin), 1.)
            glTranslatef(0, -self.ymin, 0.)

            glPushMatrix()
            
            glTranslatef(-0.07, y, 0)
            glScalef(1., (self.ymax-self.ymin)/1.8, 1.)
            
            output(str(y), 3000)

            glPopMatrix()
            glPopMatrix()


        glPushMatrix()
        glLoadIdentity()

        self.initmatrix = glGetDoublev(GL_PROJECTION_MATRIX)

        # go to origin
        glTranslatef(-0.9, -0.9, 0.)

        # scale to coordinates
        glScalef(1.8/(self.xmax-self.xmin), 1.8/(self.ymax-self.ymin), 1)

        # go to (0, 0)
        glTranslatef(-self.xmin, -self.ymin, 0)
#
#            glTranslate(-1., -1., 0)
#            glScalef(2./(self.xmax-self.xmin), 2./(self.ymax-self.ymin), 1.)
#            glTranslatef(-self.xmin, -self.ymin, 0)
        
        self.projmatrix = glGetDoublev(GL_PROJECTION_MATRIX)

        glPopMatrix()

    def paintGL(self):
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
            glEnable(GL_LINE_SMOOTH)

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

    def resizeGL(self,width,height):
        self.w, self.h = width, height
        self.marginx = int(self.w * 0.1)
        self.marginy = int(self.h * 0.1)
        glViewport( 0, 0, width, height )
        self.viewport = glGetIntegerv(GL_VIEWPORT)
        self.res = self.w/100.

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glDisable(GL_DEPTH_TEST)
        glMatrixMode (GL_PROJECTION)
        glLoadIdentity ()
        gluOrtho2D (0, self.size().width(), 0, self.size().height())
        self.make_data_list()

        self.mvmatrix = glGetDoublev(GL_MODELVIEW_MATRIX)
        self.viewport = glGetIntegerv(GL_VIEWPORT)

    def make_data_list(self):
        V3f = glVertex3f
        t = time.time()

        dx =  self.res * (self.xmax-self.xmin)/self.size().width()
        dy =  self.res * (self.ymax-self.ymin)/self.size().height()
        glColor3f(0.7,0.0,0.1)

        glNewList(1, GL_COMPILE)
        glBegin(GL_QUADS)
        for x,y in izip(self.x[0], self.y[0]):
            V3f(x, y, 0)
            V3f(x + dx, y, 0)
            V3f(x + dx, y + dy, 0)
            V3f(x, y + dy, 0)
        glEnd()
        glEndList()

        print time.time()-t

    def mouse_to_ident(self, xm, ym):
        realy = self.viewport[3] - ym - 1
        x, y, _ = gluUnProject(xm, realy, 0.0, self.mvmatrix, self.initmatrix, self.viewport)
        return x, y

    def mouse_to_real(self, xm, ym):
        realy = self.viewport[3] - ym - 1
        x, y, _ = gluUnProject(xm, realy, 0.0, self.mvmatrix, self.projmatrix, self.viewport)
        return x, y

    def autoscale(self):
        self.xmin = min(self.x[0])
        self.ymin = min(self.y[0])
        self.xmax = max(self.x[0])
        self.ymax = max(self.y[0])

    def set_range(self, fr, to):
        self.fr, self.to  = fr, to

 
    def zoomout(self,x1, x2,x3, x4):
        a = (x2-x1)/(x4-x3); c = x1 - a*x3;
        f1 = a*x1 + c; f2 = a*x2 + c;
        return min(f1, f2), max(f1, f2)


    def mouseMoveEvent(self, e):
#        x, y = self.mouse_to_real(e.x(), e.y())
#        self.set_range(x, self.to)
#        self.updateGL()
#        return
        if self.px is not None:
            self.buf = True
            self.px, self.py = self.sx, self.sy
            self.sx, self.sy = self.mouse_to_ident(e.x(), e.y())
            self.updateGL()
            self.buf = False

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton or e.button() == Qt.RightButton:
            self.ix, self.iy = self.mouse_to_ident(e.x(), e.y())
            self.px, self.py, self.sx, self.sy = self.ix, self.iy, self.ix, self.iy
            self.mouseMoveEvent(e)
            self.zix, self.ziy = self.mouse_to_real(e.x(), e.y())

    def mouseReleaseEvent(self, e):
#        x, y = self.mouse_to_real(e.x(), e.y())
#        self.set_range(x, self.to)
#        self.updateGL()
#        return
        if e.button() == Qt.MidButton:
            self.autoscale()
            self.make_data_list()
            self.updateGL()
        elif e.button() == Qt.LeftButton or e.button() == Qt.RightButton:
            self.px, self.py = self.sx, self.sy
            self.sx, self.sy = self.ix, self.iy
            self.mouseMoveEvent(e)
            if self.px == self.sx or self.py == self.sy: #can't zoom!
                self.px, self.py = None, None
                return

            self.zfx, self.zfy = self.mouse_to_real(e.x(), e.y())

            self._xmin, self._xmax = min(self.zix, self.zfx), max(self.zix, self.zfx)
            self._ymin, self._ymax = min(self.zfy, self.ziy), max(self.zfy, self.ziy)

            if e.button() == Qt.RightButton:
                self.xmin, self.xmax = self.zoomout(self.xmin, self.xmax, self._xmin, self._xmax)
                self.ymin, self.ymax = self.zoomout(self.ymin, self.ymax, self._ymin, self._ymax)
            else:
                self.xmin, self.xmax, self.ymin, self.ymax = self._xmin, self._xmax, self._ymin, self._ymax

            self.make_data_list()
            self.updateGL()
        self.px, self.py = None, None

class glGraph(object):
    def __init__(self, parent=None):
        self.win = QTabWidget(parent)
        self.win.setTabShape(self.win.Triangular)
        self.win.setTabPosition(self.win.Bottom)
        self.win.graph = self

        self.main = QHBox(self.win)
        self.win.addTab(self.main, 'graph')

        self.gwidget = GLGraphWidget(self.main)


##############################################################################
if __name__=='__main__':
    app=QApplication(sys.argv)
    g = glGraph()
    app.setMainWidget(g.win)
    g.win.show()
    app.exec_loop()
