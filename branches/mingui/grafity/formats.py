import sys
import os
import zlib
import bz2
import StringIO
import pickle

import cElementTree as xml

from grafity import Worksheet, Graph

def pyget (elem, name):
    return eval (elem.get (name), {"__builtins__": { 'True': True, 'False':False, 'None':None, 'nan':0.0 }})

def load(project, filename): 
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

    for welem in root.findall('Worksheet'):
        wsheet = project.new(Worksheet, welem.get("name"))

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
            # line and symbol styles
#            for prop in Dataset.props:
#                ds.set_curve_style(prop, pyget(delem, prop))

"""
    def from_element(self, elem):
        self.destroy_ui()
        self.functions = []
        try:
            instnames = pyget(elem, "inst_names")
        except:
            instnames = [None for f in pyget(elem, "names")]

        try:
            self.extra_properties = pyget(elem, "extra_properties")
        except:
            pass

        try:
            self.maxiter = pyget(elem, "max_iterations")
        except:
            pass

        try:
            self.resultsws = pyget(elem, "resultsws")
        except:
            pass

        for name, varshare, instname in zip(pyget(elem, "names"), pyget(elem, "varshares"), instnames):
            try:
                id = [f.name for f in self.available_functions].index(name)
            except ValueError: # function not available
                print >>sys.stderr, "Function not available: %s" % (name,)
                continue
            func = function_class_from_function(self.available_functions[id])()
            func.varshare = varshare
            func.inst_name = instname
            self.functions.append(func)
        self.graph.fitdatasets = [self.graph.datasets[i] for i in pyget(elem, "datasets")]
        self.params_flat_to_func(pyget(elem, "params")[0])
        self.build_ui()
"""


if __name__ == '__main__':
    load(sys.argv[1])
