import sys

from qt import *

from grafity.arrays import *
from grafity.extend import extension, options
from grafity.ui.graph_tools import GraphTool

def integrate(x, y):
    dx = x[1:]-x[:-1]
    dy = y[1:]-y[:-1]

    r = y[1:] * dx
    t = dy * dx

    return concatenate([[0], add.accumulate(r+t)])

class Eraser(GraphTool):
    def __init__(self, graph, view, plot):
        self.graph, self.view, self.plot = graph, view, plot
    name = "Erase data points"
    image = 'eraser'
extension('graph-mode', Eraser)

@extension('dataset-tool')
@options(name='Hide')
def hide(graph, view):
    for d in view.datasets:
        d.range = (0, -1)

@extension('dataset-tool')
@options(name='Full Range')
def full(graph, view):
    range_l = min(d.minx for d in view.datasets)
    range_r = max(d.maxx for d in view.datasets)
    for d in view.datasets:
        d.range = (range_l, range_r)
    
@extension('dataset-tool')
@options(name='Show Only')
def only(graph, view):
    range_l = min(d.minx for d in view.datasets)
    range_r = max(d.maxx for d in view.datasets)
    for d in view.datasets:
        d.range = (range_l, range_r)
    for d in set(graph.datasets)-set(view.datasets):
        d.range = (0, -1)
