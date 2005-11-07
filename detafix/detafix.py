from import_ascii import import_ascii



# we need these lines for cx_Freeze to work on numarray!
import numarray._bytes,     numarray._ufuncBool,      numarray._ufuncInt32, numarray._ufuncUInt8
import numarray._chararray, numarray._ufuncComplex32, numarray._ufuncInt64, numarray.libnumarray
import numarray._conv,      numarray._ufuncComplex64, numarray._ufuncInt8,  numarray.memory
import numarray._ndarray,   numarray._ufuncFloat32,   numarray._ufuncUInt16
import numarray._numarray,  numarray._ufuncFloat64,   numarray._ufuncUInt32
import numarray._sort,      numarray._ufuncInt16,     numarray._ufuncUInt64


from numarray import *
from numarray.ieeespecial import nan
import os
import sys
import re

import wx
import gui

def wsname_to_temp(wnam): 
    """
    Convert a name of the form pNN or mNN into a number.
    """
    val = around(float(wnam[1:].rstrip('a').replace('_', '.')) *2.)/2.
    if int(val)==val:
        val = int(val)
    if wnam[0] in ['m', 'n']: 
        val = -val 
    elif wnam[0] == 'p': 
        pass 
    else: 
        return None
    return val 

def temp_to_wsname(val):
    """
    Convert a number to a name of the form pNN or mNN.
    """
    val = float(around(val*2.)/2.)
    if int(val)==val:
        val = int(val)
    ret = str(abs(val)).replace('.', '_')
    if val<0:
        ret = 'm'+ret
    else:
        ret = 'p'+ret
    return ret

def windeta_wstemp(header, line=1):
    """
    Try to extract the temperature from a worksheet imported from a
    WinDETA ascii file. Returns None if a temperature is not found.
    """
    try:
        return float(re.findall(r'C]=([+-]?\d*\.?\d*)', header[line])[0])
    except (IndexError, ValueError):
        return None

def freq_to_name(freq):
    """
    Convert a frequency into a name of the form, e.g. 3_324KHz'
    """
    ranges = [ (1e9, 'G'), (1e6, 'M'), (1e3, 'K'), (1e0, ''), (1e-3, 'm'), (1e-6, 'u') ]
    range = ranges[[freq > r[0] for r in ranges].index(True)]
    return ('f%.3f%sHz' % (freq/range[0], range[1])).replace('.', '_')

def process_windeta_dir(dir, progress):
    files = [dir + '/' + fil for fil in os.listdir(dir) if os.path.splitext(fil)[1].lower() =='.txt']
    freqs = None
    temps = []
    names = []
    e1 = []
    e2 = []

    progress.range = len(files)

    for f in files:
#        print 'reading', f,
        data, header = import_ascii(f)

        # read temperature
        temp = windeta_wstemp(header, 1)
        if temp is None:
            temp = windeta_wstemp(header, 2)
        temps.append(temp)
        name = temp_to_wsname(temp)
        while name in names:
            name += 'a'
        names.append(name)
#        print temp, name,

        # read frequencies
        if freqs is None:
            freqs = data[0]
        else:
            l = min(len(data[0]), len(freqs))
            if not alltrue(data[0][:l] == freqs[:l]):
                raise RuntimeError, 'frequencies not the same in file', f
            elif len(data[0])>len(freqs):
                freqs = data[0]
            else:
                pass
        
        e1.append(data[1])
        e2.append(data[2])

        progress.value += 1

    e1 = [concatenate([e, [nan]*(len(freqs)-len(e))]) for e in e1]
    e2 = [concatenate([e, [nan]*(len(freqs)-len(e))]) for e in e2]

#        print 'frequencies ok',
#        print

    e1 = zip(temps, e1) ; e1.sort() ; e1 = [z[1] for z in e1]
    e2 = zip(temps, e2) ; e2.sort() ; e2 = [z[1] for z in e2]
    names = zip(temps, names) ; names.sort() ; names = [z[1] for z in names]
    temps.sort()

    e1 = array(e1)
    e2 = array(e2)
    temps = array(temps)

    deriv = zeros(e1.shape, 'd')

    for col, e in enumerate(e1):
        r = 1./(10*log10(freqs[4]/freqs[5]))
        for i in range(len(e))[2:-2]:
            deriv[col][i] = 2*r*(e[i+2] - e[i-2]) + r*(e[i+1] - e[i-1])

    rnan = str(nan)

    fil = file('e1.dat', 'w')
    print >>fil, 'frequency\t%s' % '\t'.join(names)
    for f, e in zip(freqs, transpose(e1)):
        print >>fil, "%s\t%s" % (str(f), '\t'.join([str(p) for p in e]).replace(rnan, '--'))

    fil = file('e2.dat', 'w')
    print >>fil, 'frequency\t%s' % '\t'.join(names)
    for f, e in zip(freqs, transpose(e2)):
        print >>fil, "%s\t%s" % (str(f), '\t'.join([str(p) for p in e]).replace(rnan, '--'))

    fil = file('deriv.dat', 'w')
    print >>fil, 'frequency\t%s' % '\t'.join(names)
    for f, e in zip(freqs[2:-2], transpose(deriv)[2:-2]):
        print >>fil, "%s\t%s" % (str(f), '\t'.join([str(p) for p in e]).replace(rnan, '--'))

    fil = file('tand.dat', 'w')
    print >>fil, 'frequency\t%s' % '\t'.join(names)
    for f, e, ee in zip(freqs, transpose(e1), transpose(e2)):
        print >>fil, "%s\t%s" % (str(f), '\t'.join([str(p) for p in ee/e]).replace(rnan, '--'))

    fil = file('m1.dat', 'w')
    print >>fil, 'frequency\t%s' % '\t'.join(names)
    for f, e, ee in zip(freqs, transpose(e1), transpose(e2)):
        print >>fil, "%s\t%s" % (str(f), '\t'.join([str(p) for p in e/(e*e+ee*ee)]).replace(rnan, '--'))

    fil = file('m2.dat', 'w')
    print >>fil, 'frequency\t%s' % '\t'.join(names)
    for f, e, ee in zip(freqs, transpose(e1), transpose(e2)):
        print >>fil, "%s\t%s" % (str(f), '\t'.join([str(p) for p in ee/(e*e+ee*ee)]).replace(rnan, '--'))

    fil = file('cond.dat', 'w')
    print >>fil, 'frequency\t%s' % '\t'.join(names)
    for f, ee in zip(freqs, transpose(e2)):
        print >>fil, "%s\t%s" % (str(f), '\t'.join([str(p) for p in ee*f*8.854e-12/100]).replace(rnan, '--'))

    progress.value = 0


class App(wx.App):
    def OnInit(self):
        w = wx.Frame(None)
        self.SetTopWindow(w)

        dlg = wx.DirDialog(w)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            process_windeta_dir(path)
        dlg.Destroy()
        return True

class MainWin(gui.Window):
    def __init__(self):
        gui.Window.__init__(self, size=(200, 150),title='Detafix')
        box = gui.Box(self, 'vertical')

        b = gui.Button(box, 'Select directory...')
        b.connect('clicked', self.on_sel_dir)

        self.progress = gui.Progressbar(box, stretch=0.)

    def on_sel_dir(self):
        dlg = wx.DirDialog(self._widget, 'Select a directory', defaultPath='.')
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            process_windeta_dir(path, self.progress)
        dlg.Destroy()
 
if __name__ == '__main__':
    gui.Application().run(MainWin)
