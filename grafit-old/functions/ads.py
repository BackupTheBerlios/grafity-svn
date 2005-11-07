from scipy import *

def ads(x, A, m, s, g):
        a = (x-m)/s
        b = (x-m)/(s*g)
        t1 = 1./(1+exp(a))
        t2 = 1./(1+exp(b))
        return A * a * (1-b)

def move(self, x, y):
    self.sigma = y*x**self.s

def horiz(self, x):
    self.s = self.s-x

def vert(self, x):
    self.s = self.s-x

ads.name = 'Peak/Asymmetric Double Sigmoid'
ads.initial_values = [1, 1, 1, 1]
ads.tex = r'f(x) = A  \frac{(x-\mu)}{\sigma}(1-\frac{(x-\mu)}{\gamma\sigma})'

functions = [ads]
