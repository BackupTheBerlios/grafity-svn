from grafit.fit import register_fit_function
from scipy import *

def conductivity(x, sigma, s):
    return sigma*x**(-s)

conductivity.name = 'Dielectric/Conductivity'
conductivity.initial_values = (1e-9, 1.0)
conductivity.tex = r'cond(f) = \sigma f^{-s}'
                
def move(x, y, sigma, s):
    return (y*x**s, s)

def horiz(x, sigma, s):
    return (sigma, s-x)

conductivity.move = move
conductivity.horiz = horiz

register_fit_function(conductivity)
