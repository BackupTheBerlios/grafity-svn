from Numeric import *

def arrhenius(x, logf0, w):
    return logf0 - (w/.1984)*x

arrhenius.name = 'Arrhenius/Arrhenius'
arrhenius.initial_values = (12, 0.5)
arrhenius.tex = r'f_{max} = f_0 e^{-\frac{w}{T}}'

def vtf(x, logf0, b, T0):
    return logf0 - (b*log10(e)/((1000/x)-T0))

vtf.name = 'Arrhenius/VTF'
vtf.initial_values = (12, 1000, 200)
vtf.tex = r'f_{max} = f_0 e^{-\frac{\beta}{T - T_0}}'

def modvtf(x, H, T0):
    k = 8.617e-5
    T = 1000./x
    h = 4.135e-15
    pi = 3.14159

    return log10((k*T)/(2*pi*h)) - (H*0.4343/k)/(T-T0)

modvtf.name = 'Arrhenius/Starkweather VTF'
modvtf.desc = 'Eq. 6 of <i>H. W. Starkweather, Frequency-Temperature Relationships for the Glass Transition, Macromolecules 1993,26, 4805-4808</i>'
modvtf.initial_values = (1, 100)

def wlf(x, T0, C1, C2):
    T = 1000./x
    return -2.79 + C1*(T-T0) / (C2+T-T0)

wlf.name = 'Arrhenius/Willams-Landel-Ferry'
wlf.initial_values = (100, 10, 10) 

def eyring(x, DS, DH):
    k = 8.617e-5
    T = 1000./x
    h = 4.135e-15
    pi = 3.14159
    
    return log10((k*T)/(2*pi*h)) + (0.4343/k)*(DS - DH/T)
                
eyring.name = 'Arrhenius/Eyring'
eyring.initial_values = (1, 1)

functions = [arrhenius, modvtf, vtf, eyring, wlf]
