from Numeric import *
                
def cole_cole_arrhenius (x, fo, w, de, a, f):
    b=1
    k=8.617e-5
    f0 = log10(10.**fo*exp(-w/(k*(x+273.15))))
    return -(de/((1 + (1j*f/(10**f0))**(1-a) )**b)).imag

cole_cole_arrhenius.name = 'Dielectric-temperature/Cole-Cole (Arrhenius)'
cole_cole_arrhenius.initial_values = (13, 0.5, 1.0, 0.5, 10)
   
def cole_cole_vtf (x, fo, B, T0, de, a, f):
    b=1
    k=8.617e-5
    f0 = log10(10.**fo*exp(-B/(x+273.15-T0)))
    return -(de/((1 + (1j*f/(10**f0))**(1-a) )**b)).imag

cole_cole_vtf.name = 'Dielectric-temperature/Cole-Cole (VTF)'
cole_cole_vtf.initial_values = (13, 1000, 100, 1.0, 0.5, 10)

functions = [cole_cole_arrhenius, cole_cole_vtf]
