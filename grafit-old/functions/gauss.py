# quadratic.py
# Example of a fit function for Grafit.

# You define a fit function just like an ordinary python function.
# The first parameter is x (a Numeric array), the rest are the fit parameters:

from scipy import *

def gauss(x, A, m, s):
    return (A/(sqrt(2*pi)*s)) * exp(-((x-m)**2)/(2*s**2))

# The function can hava a few (optional) attributes:

gauss.name = 'Peak/Gaussian'                # Function name
gauss.initial_values = [1., 0., 1.]     # Initial parameter values
gauss.tex = r'f(x) = \frac{A}{\sigma \sqrt{2 \pi}} e^{\frac{(x-\mu)^2}{2 \sigma^2}}'

# We must define a list called 'functions' containing the fit functions
# we want to add:

functions = [gauss]
