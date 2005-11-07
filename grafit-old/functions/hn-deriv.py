from Numeric import *
from grafit.function import special_case
                
def havriliak_negami (x, f0, de, a, b):
    W = (x/(10**f0))**(1-a)
    S = sin(0.5*pi*(1-a))
    C = cos(0.5*pi*(1-a))
    T = arctan(S / ((1/W) + C))
    num = (1-a)*b*de*W*cos(0.5*pi*(1-a)-(1+b)*T)
    den = (1 + 2*W*C + W*W)**((1+b)*0.5)
    return (pi/2)*(num/den)

havriliak_negami.name = 'Dielectric/Havriliak-Negami (deriv)'
havriliak_negami.initial_values = (5.7, 1.0, 0.5, 0.5)
havriliak_negami.tex = r'hn(f)=\Im\[\frac{\Delta\epsilon}{(1+(if/f_0)^\alpha)^\beta}\]'

def move(x, y, f0, de, a, b):
    f0 = log10(x*( sin((1-a)*b*pi/(2+2*b)) / sin((1-a)*pi/(2+2*b)) )**(1/(1-a)))
    de = de * y/havriliak_negami(x, f0, de, a, b)
    return f0, de, a, b

def peak(f0, de, a, b):
    fmax = 10**f0 * ( sin((1-a)*pi/(2+2*b)) /  sin((1-a)*b*pi/(2+2*b)) )**(1/(1-a))
    emax = havriliak_negami(fmax, f0, de, a, b)
    return fmax, emax

def horiz(x, f0, de, a, b):
    if (a+x)*b > 1:
        return None
    fmax, emax = peak(f0, de, a, b)
    return move(fmax, emax, f0, de, a-x, b)

def vert(x, f0, de, a, b):
    if a*(b+x) > 1:
        return None
    fmax, emax = peak(f0, de, a, b)
    return move(fmax, emax, f0, de, a, b+x)

havriliak_negami.move = move
havriliak_negami.horiz = horiz
havriliak_negami.vert = vert


cole_cole = special_case(havriliak_negami, 'Dielectric/Cole-Cole (deriv)', b='1')
kwwapprox = special_case(havriliak_negami, 'Dielectric/KWW-approx (deriv)', b='1-.812*a**.387')

functions = [havriliak_negami, cole_cole, kwwapprox]
