import re
from grafity.arrays import *
from OpenGL.GL import *
from OpenGL.GLU import *

from __builtin__ import round

class Grid(object):
    def __init__(self, orientation, plot):
        assert orientation in ['horizontal', 'vertical']
        self.orientation = orientation
        self.plot = plot

    def paint(self):
        if self.orientation == 'horizontal':
            glLineStipple (1, 0x4444) # dotted
            glEnable(GL_LINE_STIPPLE)
            if self.plot.ps:
                gl2ps_Enable(GL2PS__LINE_STIPPLE)
                gl2ps_LineWidth(0.01)
            glColor3f(0.3, 0.3, 0.3)
            glBegin(GL_LINES)
            for x in self.plot.axis_bottom.tics(self.plot.xmin, self.plot.xmax)[0]:
                x, _ = self.plot.data_to_phys(x, 0)
                glVertex3d(x, 0.0, 0.0)
                glVertex3d(x, self.plot.plot_height, 0.0)
            glEnd()
            if self.plot.ps:
                gl2ps_Disable(GL2PS__LINE_STIPPLE)
                gl2ps_LineWidth(0.1)
            glDisable(GL_LINE_STIPPLE)

        elif self.orientation == 'vertical':
            glLineStipple (1, 0x4444) # dotted
            glEnable(GL_LINE_STIPPLE)
            if self.plot.ps:
                gl2ps_Enable(GL2PS__LINE_STIPPLE)
                gl2ps_LineWidth(0.01)
            glColor3f(0.3, 0.3, 0.3)
            glBegin(GL_LINES)
            for y in self.plot.axis_left.tics(self.plot.ymin, self.plot.ymax)[0]:
                _, y = self.plot.data_to_phys(0, y)
                glVertex3d(0, y, 0.0)
                glVertex3d(self.plot.plot_width, y, 0.0)
            glEnd()
            glDisable(GL_LINE_STIPPLE)
            if self.plot.ps:
                gl2ps_Disable(GL2PS__LINE_STIPPLE)
                gl2ps_LineWidth(0.1)

class Axis(object):
    def __init__(self, position, plot):
        self.position = position
        self.plot = plot
        self.fmt = "%g"
#        self.font = AXISFONT

    def transform(self, data):
        if self.position in ['bottom', 'top'] and self.plot.xtype == 'log':
            return log10(data)
        if self.position in ['left', 'right'] and self.plot.ytype == 'log':
            return log10(data)
        return data

    def invtransform(self, data):
        if self.position in ['bottom', 'top'] and self.plot.xtype == 'log':
            return 10**data
        if self.position in ['left', 'right'] and self.plot.ytype == 'log':
            return 10**data
        return data

    def paint_frame(self):
        glColor3d(0.0, 0.0, 0.0) # axis color

        # Axis lines
        w, h = self.plot.plot_width, self.plot.plot_height
        p1, p2 = {'bottom': ((0, 0, 0), (w, 0, 0)),
                  'right':  ((w, 0, 0), (w, h, 0)),
                  'top':    ((0, h, 0), (w, h, 0)),
                  'left':   ((0, 0, 0), (0, h, 0)) } [self.position]
        glBegin(GL_LINES)
        glVertex3d(*p1)
        glVertex3d(*p2)
        glEnd()

        # Tics
        if self.position == 'bottom':
            major, minor = self.tics(self.plot.xmin, self.plot.xmax)
            glBegin(GL_LINES)
            for x in major:
                x, _ = self.plot.data_to_phys(x, 0)
                glVertex3d(x, 0, 0)
                glVertex3d(x, 2, 0)
            for x in minor:
                x, _ = self.plot.data_to_phys(x, 0)
                glVertex3d(x, 0, 0)
                glVertex3d(x, 1, 0)
            glEnd()

        elif self.position == 'left':
            major, minor = self.tics(self.plot.ymin, self.plot.ymax)
            glBegin(GL_LINES)
            for y in major:
                _, y = self.plot.data_to_phys(0, y)
                glVertex3d(0, y, 0)
                glVertex3d(2, y, 0)
            for y in minor:
                _, y = self.plot.data_to_phys(0, y)
                glVertex3d(0, y, 0)
                glVertex3d(1, y, 0)
            glEnd()

#        self.paint_text()
#        self.paint_title()

    def paint_title(self):
        facesize = round(self.plot.axis_title_font_size * self.plot.magnification)
        if self.position == 'bottom':
            self.plot.textpainter.render_text(self.plot.xtitle, facesize, 
                                              self.plot.plot_width/2, self._bottommargin-self._margin,
                                              align_x='center', align_y='top')
        elif self.position == 'left':
            self.plot.textpainter.render_text(self.plot.ytitle, facesize, 
                                              -facesize/2.-self.plot.ticw, self.plot.plot_height/2, 
                                              align_x='right', align_y='center', orientation='v')


    rexp = re.compile(r'([-?\d\.]+)e([\+\-])(\d+)')

    def totex(self, num):
        st = self.fmt%num
        match = self.rexp.match(st)
        if match is not None:
            mant = match.group(1)
            if float(mant) == 1.:
                mant = ''
                cdot = ''
            elif float(mant) == -1.:
                mant = '-'
                cdot = ''
            else:
                mant = str(float(mant))
                cdot = r' \cdot '

            exp = str(int(match.group(3)))

            sign = match.group(2)
            if sign == '+':
                sign = ''
            return r'$%s%s10^{%s%s}$' % (mant, cdot, sign, exp)
        return r'$%s$' % st

    def paint_text(self):
        facesize = round(self.plot.axis_title_font_size * self.plot.magnification)
        margin = self.plot.axis_title_font_size * 0.3514598/6.
        self._margin = margin

        if self.position == 'bottom':
            tics = self.tics(self.plot.xmin, self.plot.xmax)[0]
            h = []
            for x in tics:
                st = self.totex(x)
                xm, _ = self.plot.data_to_phys(x, 0.)
                _, height = self.plot.textpainter.render_text(st, facesize, 0, 0, measure_only=True)
                h.append(height)

            for x in tics:
                st = self.totex(x)
                xm, _ = self.plot.data_to_phys(x, 0.)
                self.plot.textpainter.render_text(st, facesize, xm, -margin-max(h), 'center', 'bottom')
                self._bottommargin = -margin-max(h)


        elif self.position == 'left':
            for y in self.tics(self.plot.ymin, self.plot.ymax)[0]:
                st = self.totex(y)
                _, ym = self.plot.data_to_phys(0., y)
                self.plot.textpainter.render_text(st, facesize, -margin, ym, 'right', 'center')

 
    def tics(self, fr, to):
        if (self.position in ['right', 'left'] and self.plot.ytype == 'log') or\
           (self.position in ['bottom', 'top'] and self.plot.xtype == 'log'):
            return self.logtics(fr, to)
        else:
            return self.lintics(fr, to)


    def logtics(self, fr, to, cache={}):
        if fr <= 0 or to <= 0:
            return [], []
        if fr == to:
            return [fr], []

        if (fr, to) in cache:
            return cache[fr, to]

        bottom = floor(log10(fr))
        top = ceil(log10(to)) + 1

        r = 1
        l = 100
        while l>8:
            major = 10**arange(bottom, top, r)
            if r > 1:
                minor = 10**array(list(set(range(bottom, top))-set(range(bottom, top, r))))
            else:
                minor = array([])
            major = array([n for n in major if fr<=n<=to])
            minor = array([n for n in minor if fr<=n<=to])
            l = len(major)
            r += 1

        cache[fr, to] = major, minor
        return major, minor

    def lintics(self, fr, to, cache={}):
        if fr == to:
            return [fr], []

        if (fr, to) in cache:
            return cache[fr, to]

        exponent = floor(log10(to-fr)) - 1

        for exponent in (exponent, exponent+1):
            for interval in (1,5,2):#,4,6,7,8,9,3):
                interval = interval * (10**exponent)
                if fr%interval == 0:
                    first = fr
                else:
                    first = fr + (interval-fr%interval)
                first -= interval
                rng = arange(first, to, interval)
                if 4 <= len(rng) <= 8:
                    minor = []
                    for n in rng:
                        minor.extend(arange(n, n+interval, interval/5))
                    rng = array([n for n in rng if fr<=n<=to])
                    minor = array([n for n in minor if fr<=n<=to])
                    cache[fr, to] = rng, minor
                    return rng, minor

        print "cannot tick", fr, to, len(rng)
        return [], []


