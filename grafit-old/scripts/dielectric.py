# Grafit dielectric tools
# $Rev: 284 $
import os
import sys
import math
import re

from qt import *

from grafit.project import project
from grafit.worksheet import Worksheet
from grafit.utils import Page

def wsname_to_temp(wnam): 
    """
    Convert a name of the form pNN or mNN into a number.
    """
    val = round(float(wnam[1:].rstrip('a').replace('_', '.')) *2.)/2.
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
    val = round(val*2.)/2.
    if int(val)==val:
        val = int(val)
    ret = str(abs(val)).replace('.', '_')
    if val<0:
        ret = 'm'+ret
    else:
        ret = 'p'+ret
    return ret

def windeta_wstemp(ws, line=1):
    """
    Try to extract the temperature from a worksheet imported from a
    WinDETA ascii file. Returns None if a temperature is not found.
    """
    try:
        return float(re.findall(r'C]=([+-]?\d*\.?\d*)', ws._header[line])[0])
    except (IndexError, ValueError):
        return None

def freq_to_name(freq):
    """
    Convert a frequency into a name of the form, e.g. 3_324KHz'
    """
    ranges = [ (1e9, 'G'), (1e6, 'M'), (1e3, 'K'), (1e0, ''), (1e-3, 'm'), (1e-6, 'u') ]
    range = ranges[[freq > r[0] for r in ranges].index(True)]
    return ('f%.3f%sHz' % (freq/range[0], range[1])).replace('.', '_')

def make_isochronal(e1_f, e2_f):
    all_temperatures = [wsname_to_temp(n) for n in [c.name for c in e1_f][1:]]
    e1_T = project.new_worksheet('_e1_T')
    e2_T = project.new_worksheet('_e2_T')
    e1_T.temp = e2_T.temp = all_temperatures
    project.mainwin.statusBar().message ("Creating e1_T")
    project.mainwin.progressbar.setTotalSteps(len(e1_f.array))
    for prog, line in enumerate(e1_f.array):
        e1_T[freq_to_name(line[0])] = line[1:]
        if prog % 5 == 0:
            project.mainwin.progressbar.setProgress(prog+1)

    project.mainwin.statusBar().message ("Creating e2_T")
    project.mainwin.progressbar.setTotalSteps(len(e2_f.array))
    for prog, line in enumerate(e2_f.array):
        e2_T[freq_to_name(line[0])] = line[1:]
        if prog % 5 == 0:
            project.mainwin.progressbar.setProgress(prog+1)

def make_e2deriv(e1_f):
    all_temperatures = [wsname_to_temp(n) for n in [c.name for c in e1_f][1:]]

    project.mainwin.statusBar().message ("Creating deriv")
    project.mainwin.progressbar.setTotalSteps(len(e1_f)-1)
    deriv = project.new_worksheet('e2deriv_f')
    deriv.freq = e1_f.freq
    
    for prog, e1 in enumerate(e1_f[1:]):
        r = 1./(10*math.log(e1_f.freq[4]/e1_f.freq[5]))

        deriv[e1.name] = None

        for i in range(len(e1))[2:-3]:
            deriv[e1.name][i] = 2*r*(e1[i+2] - e1[i-2]) + r*(e1[i+1] - e1[i-1])
        if prog % 5 == 0:
            project.mainwin.progressbar.setProgress(prog+1)

def process_windeta_dir(dir, worksheet_names):
    project.lock_undo()
    files = [dir + '/' + fil for fil in os.listdir(dir) if os.path.splitext(fil)[1] in ('.txt', '.TXT')]
    wsheets = []

    project.mainwin.statusBar().message ("Reading ASCII files")
    project.mainwin.progressbar.show()
    project.main_dict['app'].processEvents()
    project.mainwin.progressbar.setTotalSteps(len(files))

    for prog, f in enumerate(files):
        w = project.new_worksheet()
        w.import_ascii(f)
        name = windeta_wstemp(w, 1)
        if name is None:
            name = windeta_wstemp(w, 2)
            if name is None:
                p = Page(None, ('Could not determine temperature\n for ascii file '+f, ['Temperature']))
                p.run()
                try:
                    name = float(p['Temperature'])
                except ValueError:
                    continue
        name = temp_to_wsname(name)
        while name in [s.name for s in wsheets]:
            name += 'a'
        w.name = name
        wsheets.append(w)
        if prog % 5 == 0:
            project.mainwin.progressbar.setProgress(prog+1)
    e1_f = project.new_worksheet('_e1_f')
    e2_f = project.new_worksheet('_e2_f')
    e1_f.freq = e2_f.freq = None

    new_wsheets = [(windeta_wstemp(w), w) for w in wsheets]
    new_wsheets.sort()
    wsheets = [w[1] for w in new_wsheets]

    project.mainwin.statusBar().message ("Creating e1_f and e2_f")
    project.mainwin.progressbar.setTotalSteps(len(files))

    for prog, w in enumerate(wsheets):
        if len(w[0]) > len(e1_f.freq):
            e1_f.freq = w[0]
            e2_f.freq = w[0]
        e1_f[w.name] = w[1]
        e2_f[w.name] = w[2]
        project.remove(w)
        if prog % 5 == 0:
            project.mainwin.progressbar.setProgress(prog+1)

    if 'e1(T)' in worksheet_names or 'e2(T)' in worksheet_names:
        make_isochronal(e1_f, e2_f)
    	if 'e1(T)' in worksheet_names: project.w._e1_T.name = 'e1_T'
    	else: project.remove(project.w._e1_T)
    	if 'e2(T)' in worksheet_names: project.w._e2_T.name = 'e2_T'
    	else: project.remove(project.w._e2_T)
    if 'e2deriv(f)' in worksheet_names:
        make_e2deriv(e1_f)

    if 'e1(f)' in worksheet_names: project.w._e1_f.name = 'e1_f'
    else: project.remove(project.w._e1_f)
    if 'e2(f)' in worksheet_names: project.w._e2_f.name = 'e2_f'
    else: project.remove(project.w._e2_f)

    project.unlock_undo()
    project.mainwin.progressbar.hide()

class ImportWindetaDir(object):
    def do(self):
        dir = QFileDialog.getExistingDirectory("/home", project.mainwin, "get existing directory"
                    "Choose a directory")
        worksheet_names = ['e1(f)', 'e2(f)', 'e1(T)', 'e2(T)', 'e2deriv(f)', 'e2deriv(T)']
        p = Page(None,
                 ('Create worksheets',
                    ['?'+n for n in worksheet_names]))
        for n in worksheet_names:
            p[n] = True
        p.run()
        
        process_windeta_dir(str(dir), [n for n in worksheet_names if p[n] is True])

icon = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x02\x00\x00\x00\x90\x91h6\x00\x00\x00\x06bKGD\x00\xff\x00\xff\x00\xff\xa0\xbd\xa7\x93\x00\x00\x00\tpHYs\x00\x00\x0b\x12\x00\x00\x0b\x12\x01\xd2\xdd~\xfc\x00\x00\x00\x07tIME\x07\xd4\x01\x0e\r\x0b\x10n_\xf0\xe6\x00\x00\x01=IDATx\x9c\x85\x921K\xc3P\x10\xc7\x7f\xaf>\x1d*\x82A(\xb4H\x86\x82H\xe2 \x14\xa4 \xae\xa1S\xc1\xcd\xc9\xc5\xa1\x83\xf5\xdb\x988\x14\xf43\x08\xc1\xa1\xf4\x13\xb8\x14\xfa \t"8\x94\xda\x82\x0eE\xc4-R\x87\xbe&\xb1F\xfds\xbc\xf7\xbb\xe3\x8e\xbb{<\x81\n\x98\xcb\xf5\x00.\xda\xa9\x9bpF\x05}7\x1cn:)\xbb\x1e\xfem\xcaY@\x05\x94+\xfaLL\xcaeV\x01\xadsTP\xf8\xd1\x13\xba=\xceZ9\x9c\x8e\xd4\xed\xd1p\x00\x9a\xc7\xf9\x9c\x00\x88t\xe9D\r\x8bI\xd6\x8fP\xa9#sF\x9a\x88\x9c\xe0_\x05*\xd4P\xb3\x891N\xcc)\xc3\xef;\xe4\xaaf\x13\x83\x0c\xb9\xc6\xa8\x9a\xcb\x1d\x8c\xaa\xe9\x17\xd7\x93\xe8\xd1\x9a06\xf1\xeff\x1cX\xc0\xa1\x10[Us\xfa4$\xbb\xb4t)\xf9\x00\xe3W\x9b\x18IX*\xeb\xfa\x87Gkw\'\x02^\x9a\x8b\x02\xe92\xe8\x00\xecc\xc7\x00ae\xd1mtoE\xf5h>\x8d\xd3Gf\xb3\x1d\xacX\xa7\xd9c\r\xb3\xedz\xd4\x03$^\x9f1\xac\xc8\xcf\xf6`\xf1\x89\xde)>\xb3\xba\x01\x89\x9d\xf2q\xc9\xdb<\xfb\n\x00!U0\xf8\xf5\xa5\xb4<t6 c\xd8\xfb\xaf \xab/\xc3\x91h\xd2\x8c:\x1e\x0f\x00\x00\x00\x00IEND\xaeB`\x82'

def qpixmap_from_data(data):
    tempfile = '/tmp/graphite-mimetex'
    f = open(tempfile, 'wb')
    f.write (data)
    f.close()
    pix = QPixmap(tempfile)
    os.remove(tempfile)
    return pix

def install():
    action = project.mainwin.action_from_tuple([ "Import WinDETA directory", "Import WinDETA directory...", 
                                     qpixmap_from_data(icon), ImportWindetaDir, False, None])
    action.addTo(project.mainwin.menus['&Tools'])


description = """
<b>Grafit Dielectric Tools</b>
<hr>
At the moment this plugin allows you to:
<ul>
<li>Import ascii files saved by WinDETA, reading also the temperatures</li>
<li>Automatically create worksheets with the data vs. frequency or temperature</li>
</ul>
"""

install()
