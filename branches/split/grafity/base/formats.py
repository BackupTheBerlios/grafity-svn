import sys
import os
import zlib
import bz2
import StringIO
import pickle

import cElementTree as xml

from grafity import Worksheet, Graph
from grafity.graph import attrs, attr_values

def pyget (elem, name):
    return eval (elem.get (name), {"__builtins__": { 'True': True, 'False':False, 'None':None, 'nan':0.0 }})

def load(project, filename, progress=None, message=None): 
    f = open(filename)
    header = f.read(10)

    data = f.read()
    if header == 'GRAPHITEGZ':
        data = zlib.decompress(data)
    elif header == 'GRAPHITEBZ':
        data = bz2.decompress(data)

    sio = StringIO.StringIO(data)
    try:
        tree = xml.parse(sio)
    finally:
        f.close()
        sio.close()

    root = tree.getroot()

    totalprogress = len(root)
    prog = 0

    for welem in root.findall('Worksheet'):
        wsheet = project.new(Worksheet, welem.get("name"))
        print >>sys.stderr, 'loading worksheet %s' % wsheet.name
        prog += 100./totalprogress
        if progress:
            progress(prog)

        for celem in welem:
            if celem.tag == 'CalcColumn':
                setattr(wsheet, celem.get("name"), [])
                wsheet[celem.get("name")]._expr = celem.text
            elif celem.tag == 'Column':
                safedict = {"__builtins__": { 'True':True, 'False':False, 'None':None}}
                setattr(wsheet, celem.get("name"), pickle.loads(eval(celem.text, safedict)))

    for w in project.top.contents():
        for c in w:
            if hasattr(c, '_expr'):
                c.expr = c._expr
                del c._expr

    for gelem in root.findall('Graph'):
        graph = project.new(Graph, eval(gelem.get("name")))
        print >>sys.stderr, 'loading graph %s'% graph.name
        prog += 100./totalprogress
        if progress:
            progress(prog)

        # axes
        for aelem in gelem.findall('Axis'):
            axisid = pyget(aelem, "id")
            if axisid == 2: # QwtPlot.xBottom
                xmin, xmax = pyget(aelem, "limits")
                graph.xtype = ['linear', 'log'][pyget(aelem, 'logscale')]
                graph.xtitle = pyget(aelem, 'title')
            elif axisid == 0: # QwtPlot.yLeft
                ymin, ymax = pyget(aelem, "limits")
                graph.ytype = ['linear', 'log'][pyget(aelem, 'logscale')]
                graph.ytitle = pyget(aelem, 'title')
        graph.zoom(xmin, xmax, ymin, ymax)

        # datasets
        for delem in gelem.findall('Dataset'):
            # data
            wsheet = project.top[pyget(delem, "worksheet")]
            colx = pyget(delem, "xcolumn")
            coly = pyget(delem, "ycolumn")
            rangemin, rangemax = pyget(delem, "range")
            ds = graph.add(wsheet[colx], wsheet[coly])
            ds = graph.datasets[ds]

            ds.set_style('fill', ['open', 'filled'][pyget(delem, 'symbol_fill')])
            ds.set_style('symbol', ['none', 'circle', 'square', 'diamond', 'triangleup', 
                          'triangledown', 'triangleleft', 'triangleright', '+', 'x'][pyget(delem, 'symbol_style')])
            ds.set_style('size', pyget(delem, 'symbol_size'))
            ds.set_style('linewidth', pyget(delem, 'line_width'))
            ds.set_style('color', attr_values['color'][pyget(delem, 'symbol_color')])
            ds.set_style('linetype', attr_values['linetype'][pyget(delem, 'line_type')])
            ds.set_style('linestyle', attr_values['linestyle'][pyget(delem, 'line_style')])

    if progress:
        progress(100)

if __name__ == '__main__':
    load(sys.argv[1])
