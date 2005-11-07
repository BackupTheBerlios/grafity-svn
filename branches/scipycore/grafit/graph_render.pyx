# A small C extension for the inner loop.
# with the rest in pure python, we can easily handle a few million points 
# (lines are even faster)

import time

# math functions
cdef extern from "math.h":
    double sin(double x)
    double cos(double y)
    int isnan(double x)
    double log10(double x)

# numarray
#cdef extern from "numarray/libnumarray.h":
#    ctypedef class numarray._numarray._numarray [object PyArrayObject]:
#        cdef int *dimensions
#    void import_libnumarray()
#    void *NA_OFFSETDATA(_numarray)
#import_libnumarray()

# scipy.base
cdef extern from "scipy/arrayobject.h":
    struct PyArray_Descr:
        int type_num, elsize
        char type
    ctypedef class scipy.ArrayType [object PyArrayObject]:
        cdef char *data
        cdef int nd
        cdef int *dimensions, *strides
        cdef object base
        cdef PyArray_Descr *descr
        cdef int flags

# convert a python file to a FILE
cdef extern from "stdio.h":
    cdef struct FILE:
        pass

cdef extern from "Python.h":
    FILE* PyFile_AsFile(object)

# OpenGL
cdef extern from "GL/gl.h":
    void glVertex3d(double x, double y, double z)
    void glPointSize(double size)
    void glBegin(int mode)
    void glEnd()
    void glCallList(int id)
    void glEnable(int)
    void glPolygonMode(int, int)
    void glTranslated(double x, double y, double z)
    int GL_COMPILE, GL_QUADS, GL_LINES, GL_POLYGON, GL_TRIANGLES, GL_LINE_STRIP, GL_POINTS, GL_POINT_SMOOTH
    int GL_BACK, GL_LINE, GL_FRONT, GL_FILL, GL_RGBA

# gl2ps wrapper (only the stuff we need)
cdef extern from "gl2ps.h":
    int GL2PS_LINE_STIPPLE, GL2PS_TEXT_BL, GL2PS_EPS, GL2PS_SIMPLE_SORT, GL2PS_NONE
    void gl2psEndPage()
    int gl2psPointSize(float value)
    int gl2psEnable(int mode)
    int gl2psDisable(int mode)
    int gl2psLineWidth(float value)
    int gl2psTextOpt(char *str, char *fontname,
                     short fontsize, int align, float angle)
    int gl2psBeginPage(char *title, char *producer,
                       int viewport[4], int format, int sort,
                       int options, int colormode,
                       int colorsize, void *colormap,
                       int nr, int ng, int nb, int buffersize,
                       FILE *stream, char *filename)

GL2PS__LINE_STIPPLE = GL2PS_LINE_STIPPLE 
GL2PS__TEXT_BL = GL2PS_TEXT_BL
GL2PS__EPS = GL2PS_EPS
GL2PS__SIMPLE_SORT = GL2PS_SIMPLE_SORT
GL2PS__NONE = GL2PS_NONE

def gl2ps_BeginPage(char *title, char *producer, viewport, file, char *filename):
    cdef int vport[4], n

    for n from 0<=n<4:
        vport[n] = viewport[n]

    return gl2psBeginPage(title, producer, vport,
                          GL2PS_EPS, GL2PS_SIMPLE_SORT, GL2PS_NONE,
                          GL_RGBA, -1, NULL, 0, 0, 0, 21055000, PyFile_AsFile(file), filename)

def gl2ps_Enable(int mode): return gl2psEnable(mode)
def gl2ps_Disable(int mode): return gl2psDisable(mode)
def gl2ps_TextOpt(str, fontname, fontsize, align, angle): return gl2psTextOpt(str, fontname, fontsize, align, angle)
def gl2ps_PointSize(float value): return gl2psPointSize(value)
def gl2ps_LineWidth(float value): return gl2psLineWidth(value)
def gl2ps_EndPage(): gl2psEndPage()

cdef enum:
    CIRCLE, SQUARE, DIAMOND, UPTRIANGLE, DOWNTRIANGLE, LEFTTRIANGLE, RIGHTTRIANGLE

def render_symbols(ArrayType sx, ArrayType sy, int sym, int fill, int size, 
                   double xmin, double xmax, double ymin, double ymax,
                   double pw, double ph, double pxmin, double pxmax, double pymin, double pymax, int logx, int logy):
    cdef int n, m, l
    cdef double *xd, *yd
    cdef int i
    cdef double pi
    cdef int shape
    cdef double si
    cdef double x, y
    cdef double circlex[11], circley[11]


    si = size/5.
    pi = 3.14159265358979

    for n from 0<=n<11:
        circlex[n] = cos(n*2*pi/10)*si
        circley[n] = sin(n*2*pi/10)*si

    if sym == SQUARE:
        shape = GL_QUADS
    elif sym == UPTRIANGLE:
        shape = GL_TRIANGLES
    elif sym == DOWNTRIANGLE:
        shape = GL_TRIANGLES
    elif sym == LEFTTRIANGLE:
        shape = GL_TRIANGLES
    elif sym == RIGHTTRIANGLE:
        shape = GL_TRIANGLES
    elif sym == CIRCLE:
        if fill == 0:
            shape = GL_LINES
        else:
            shape = GL_POINTS
            glEnable(GL_POINT_SMOOTH)
    elif sym == DIAMOND:
        shape = GL_QUADS


    if fill == 1:
        glPolygonMode(GL_BACK, GL_FILL)
        glPolygonMode(GL_FRONT, GL_FILL)
    else:
        glPolygonMode(GL_BACK, GL_LINE)
        glPolygonMode(GL_FRONT, GL_LINE)

#    xbucket, ybucket = -1, -1

    xd = <double *>sx.data
    yd = <double *>sy.data

#    xinterval = (xmax-xmin)/1000.
#    yinterval = (ymax-ymin)/1000.

    l = sx.dimensions[0]

    if logx == 1:
        pxmin = log10(pxmin)
        pxmax = log10(pxmax)
    if logy == 1:
        pymin = log10(pymin)
        pymax = log10(pymax)

    # draw symbols
    glBegin(shape)
    for n from 0 <= n < l:
        x = xd[n]
        y = yd[n]

        if logx == 1:
            x = log10(x)
        if logy == 1:
            y = log10(y)
        x = pw * (x-pxmin)/(pxmax-pxmin)
        y = ph * (y-pymin)/(pymax-pymin)

        if isnan(x) or isnan(y):
            continue

        # skip if outside limits
        if not (xmin-si/2 <= x <= xmax+si/2) or not (ymin-si/2 <= y <= ymax+si/2):
            continue

        # skip if we would land within 1/1000th of the graph from the previous point
#        xbucket_s = xbucket
#        ybucket_s = ybucket
#        xbucket = <int>((x-xmin)/xinterval)
#        ybucket = <int>((y-ymin)/yinterval)
#        if (xbucket == xbucket_s) and (ybucket == ybucket_s):
#            continue

        if sym == SQUARE:
            glVertex3d(x-si/2, y-si/2, 0)
            glVertex3d(x+si/2, y-si/2, 0)
            glVertex3d(x+si/2, y+si/2, 0)
            glVertex3d(x-si/2, y+si/2, 0)
        elif sym == UPTRIANGLE or sym == DOWNTRIANGLE or sym == LEFTTRIANGLE or sym == RIGHTTRIANGLE:
            glVertex3d(x-si/2, y-si/2, 0)
            glVertex3d(x+si/2, y-si/2, 0)
            glVertex3d(x, y+si/2, 0)
        elif sym == CIRCLE and fill == 1:
            glVertex3d(x, y, 0)
        elif sym == DIAMOND:
            glVertex3d(x-si/2, y, 0)
            glVertex3d(x, y-si/2, 0)
            glVertex3d(x+si/2, y, 0)
            glVertex3d(x, y+si/2, 0)
        elif sym == CIRCLE and fill == 0:
            for m from 0<=m<10:
                glVertex3d(x+circlex[m], y+circley[m], 0)
                glVertex3d(x+circlex[m+1], y+circley[m+1], 0)
            
    glEnd()

    return 1

def render_lines(ArrayType sx, ArrayType sy, double xmin, double xmax, double ymin, double ymax,
                   double pw, double ph, double pxmin, double pxmax, double pymin, double pymax, int logx, int logy):
    cdef int n, l
    cdef double x, y, xnext, ynext
    cdef double *xd, *yd

    xd = <double *>sx.data
    yd = <double *>sy.data
    l = sx.dimensions[0]

    if logx == 1:
        pxmin = log10(pxmin)
        pxmax = log10(pxmax)
    if logy == 1:
        pymin = log10(pymin)
        pymax = log10(pymax)


    # draw lines
    glBegin(GL_LINES)
    for n from 0 <= n < l-1:
        x = xd[n]
        y = yd[n]
        xnext = xd[n+1]
        ynext = yd[n+1]

        if logx == 1:
            x = log10(x)
            xnext = log10(xnext)
        if logy == 1:
            y = log10(y)
            ynext = log10(ynext)
        x = pw * (x-pxmin)/(pxmax-pxmin)
        y = ph * (y-pymin)/(pymax-pymin)
        xnext = pw * (xnext-pxmin)/(pxmax-pxmin)
        ynext = ph * (ynext-pymin)/(pymax-pymin)

        if isnan(x) or isnan(y):
            continue

        if isnan(xnext) or isnan(ynext):
            continue

        if (x <= xmin and xnext <= xmin) or (y <= ymin and ynext <= ymin) or \
            (x >= xmax and xnext >= xmax) or (y >= ymax and ynext >= ymax):
            continue

        # skip if outside limits
#        if n < l-1:
#            xnext = xd[n-1]
#            ynext = yd[n-1]
#            if (x <= xmin and xnext <= xmin) or \
#               (x >= xmax and xnext >= xmax) or \
#               (y <= ymin and ynext <= ymin) or \
#               (y >= ymax and ynext >= ymax):
#                continue
#        else:
#            if not (xmin <= x <= xmax) or not (ymin <= y <= ymax):
#                continue
#
        # skip if we would land within 1/1000th of the graph from the previous point
#        xbucket_s = xbucket
#        ybucket_s = ybucket
#        xbucket = <int>((x-xmin)/xinterval)
#        ybucket = <int>((y-ymin)/yinterval)
#        if (xbucket == xbucket_s) and (ybucket == ybucket_s):
#            continue
        glVertex3d(x, y, 0.1)
        glVertex3d(xnext, ynext, 0.1)

    glEnd()
    return 1


