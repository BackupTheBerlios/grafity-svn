from grafity.arrays import *
from grafity.resources import register_graph_mode
from grafity.ui.graph_tools import GraphTool

def integrate(x, y):
    dx = x[1:]-x[:-1]
    dy = y[1:]-y[:-1]

    r = y[1:] * dx
    t = dy * dx

    return concatenate([[0], add.accumulate(r+t)])

class AnalyzeGlassTransition(GraphTool):
    def __init__(self, graph, view, plot):
        self.graph, self.view, self.plot = graph, view, plot
    name = "Analyze Tg"
    image = 'tg'

register_graph_mode(AnalyzeGlassTransition)

class Eraser(GraphTool):
    def __init__(self, graph, view, plot):
        self.graph, self.view, self.plot = graph, view, plot
    name = "Erase data points"
    image = 'eraser'

register_graph_mode(Eraser)
