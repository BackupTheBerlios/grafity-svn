from Numeric import *
from grafit.function import special_case
                
def havriliak_negami (x, f0, de, a, b, real):
    cmp =  de/((1 + (1j*x/(10**f0))**(1-a) )**b)
    if real > 0:
        return cmp.real
    else:
        return -cmp.imag
        

havriliak_negami.name = 'Dielectric/Havriliak-Negami (complex)'
havriliak_negami.initial_values = (5.7, 1.0, 0.5, 0.5, -1.0)
havriliak_negami.tex = r'hn^*(f)=\frac{\Delta\epsilon}{(1+(if/f_0)^\alpha)^\beta}'

def move(x, y, f0, de, a, b, real):
    f0 = log10(x*( sin((1-a)*b*pi/(2+2*b)) / sin((1-a)*pi/(2+2*b)) )**(1/(1-a)))
    de = de * y/havriliak_negami(x, f0, de, a, b, real)
    return f0, de, a, b, real

def peak(f0, de, a, b):
    fmax = 10**f0 * ( sin((1-a)*pi/(2+2*b)) /  sin((1-a)*b*pi/(2+2*b)) )**(1/(1-a))
    emax = havriliak_negami(fmax, f0, de, a, b, real)
    return fmax, emax

def horiz(x, f0, de, a, b):
    if (a+x)*b > 1:
        return None
    fmax, emax = peak(f0, de, a, b)
    return move(fmax, emax, f0, de, a-x, b, real)

def vert(x, f0, de, a, b):
    if a*(b+x) > 1:
        return None
    fmax, emax = peak(f0, de, a, b)
    return move(fmax, emax, f0, de, a, b+x, real)

havriliak_negami.move = move
havriliak_negami.horiz = horiz
havriliak_negami.vert = vert

cole_cole = special_case(havriliak_negami, 'Dielectric/Cole-Cole (complex)', b='1')
kwwapprox = special_case(havriliak_negami, 'Dielectric/KWW-approx (complex)', b='1-.812*a**.387')
hnhn2 = special_case(havriliak_negami, 'HnHn2', real='-1')

functions = [havriliak_negami, cole_cole, kwwapprox, hnhn2]
