def linear(x, a, b):
    return a*x + b

linear.name = 'Linear'
linear.initial_values = [1., 0.]
linear.tex = r'f(x) = \alpha x+\beta'

def ksi(x, a, T0, n):
    return a*(x-T0)**n

ksi.name = 'ksi(T)'
ksi.initial_values = [1, 100, 0.66]

functions = [linear, ksi]
