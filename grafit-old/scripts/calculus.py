from grafit.project import project
#from Scientific.Functions.Interpolation import InterpolatingFunction
from Numeric import *

def integrate(dataset):
    x, y, indices = dataset.data()

    dx = x[1:] - x[:-1]
    dy = y[1:] - y[:-1]

    r = y[1:] * dx
    t = dy * dx

    dataset.worksheet['intg_'+dataset.coly] = []
    dataset.worksheet['intg_'+dataset.coly][indices[0]] = 0
    dataset.worksheet['intg_'+dataset.coly][list(indices[1:])] = add.accumulate(r+t)


#def interpolate(dataset, xdata):
#    x, y, indices = dataset.data()
#
#    f = InterpolatingFunction([x], y, 0.0)
#
#    dataset.worksheet.freeze()
#    dataset.worksheet['interp_x'] = xdata
#    dataset.worksheet['interp_y'] = []
#    for i, x in enumerate(xdata):
#        dataset.worksheet.interp_y[i] = f(x)
#    dataset.worksheet.unfreeze()


def installed():
    return _installed

_installed = False

def install():
    global _installed
    if _installed:
        return
    project.main_dict['integrate'] = integrate
#    project.main_dict['interpolate'] = interpolate
    _installed = True

def uninstall():
    global _installed
    if not _installed:
        return
    del project.main_dict['integrate']
#    del project.main_dict['interpolate']
    _installed = False


description = """
<b>Calculus</b>
<hr>
At the moment this plugin allows you to:
<ul>
<li>Integrate a dataset</li>
</ul>
"""

install() 
