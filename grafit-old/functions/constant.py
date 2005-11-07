from Numeric import *

def constant(x, cnst):
    return cnst * x/x

constant.name = 'Constant'
constant.initial_values = (1,)
constant.tex = r'f(x) = c'
                
def move(x, y, cnst):
    return (y,)

constant.move = move

functions = [constant]
