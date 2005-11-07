# quadratic.py
# Example of a fit function for Grafit.

# You define a fit function just like an ordinary python function.
# The first parameter is x (a Numeric array), the rest are the fit parameters:

def quadratic(x, a, b, c):
    return a**2 + b*x + c

# The function can hava a few (optional) attributes:

quadratic.name = 'Quadratic'                # Function name
quadratic.initial_values = [1., 2., 3.]     # Initial parameter values
quadratic.tex = r'f(x) = \alpha x^2+\beta x + \gamma'                 # Function expression in TeX

# We must define a list called 'functions' containing the fit functions
# we want to add:

functions = [quadratic]
