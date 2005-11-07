from Numeric import *

def tsdc(T, A, W, Tmax):
    k=8.617e-5 #eV/K
    T = T+273.15
    Tmax = Tmax+273.15
    return (10.**A)*exp( -W/(k*T) - ((T*T)/(Tmax*Tmax))*exp ((W/k)*(1/Tmax-1/T)) )

tsdc.name = 'TSDC approx'
tsdc.initial_values = (1., 1., 100)

functions = [tsdc]
