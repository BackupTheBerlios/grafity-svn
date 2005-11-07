from Numeric import *
                
def fd(x, f0, f1, de, a):
    return -de*((1 + (1j*x/(10**f0))**a)/(1 + (1j*x/(10**f0))**a + (1j*x/(10**f1)))).imag

fd.name = 'Dielectric/FD'
fd.initial_values = (5.7, 6, 1, 0.5)
fd.tex = r'hn(f)=\Im\[\frac{\Delta\epsilon}{(1+(if/f_0)^\alpha)^\beta}\]'

functions = [fd]
