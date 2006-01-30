from grafity.arrays import *

def integrate(x, y):
    dx = x[1:]-x[:-1]
    dy = y[1:]-y[:-1]

    r = y[1:] * dx
    t = dy * dx

    return concatenate([[0], add.accumulate(r+t)])
