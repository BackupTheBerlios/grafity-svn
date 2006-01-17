#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

def test(arg):
#    sys.stderr.write('.')
    print >>sys.stderr, arg
sys.path_hooks.append(test)

# we need these lines for cx_Freeze to work on numarray!
#import numarray._bytes,     numarray._ufuncBool,      numarray._ufuncInt32, numarray._ufuncUInt8
#import numarray._chararray, numarray._ufuncComplex32, numarray._ufuncInt64, numarray.libnumarray
#import numarray._conv,      numarray._ufuncComplex64, numarray._ufuncInt8,  numarray.memory
#import numarray._ndarray,   numarray._ufuncFloat32,   numarray._ufuncUInt16
#import numarray._numarray,  numarray._ufuncFloat64,   numarray._ufuncUInt32
#import numarray._sort,      numarray._ufuncInt16,     numarray._ufuncUInt64

import logging
logging.basicConfig(format="%(asctime)s [%(name)s] %(message)s")

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-l', '--log', dest='log', help='Log program events')
options, args = parser.parse_args()

if options.log is not None:
    for l in options.log.split(','):
        logging.getLogger(l).setLevel(logging.DEBUG)

import os
import settings

sys.path.append(settings.DATADIR)
sys.path.append(os.path.join(settings.DATADIR, 'grafit', 'thirdparty'))

from thirdparty.ultraTB import VerboseTB

import gui
import mingui
import wx
import Image

import traceback
import random

titles = [
(u"Den Vogel!", 6),
(u"Le poulet!", 3),
(u"L'oiseau!", 2),
(u"The Bird!", 2),
(u"El pájaro!", 3),
(u"L'uccello!", 3),
(u"Πтица!", 1),
(u"Τον Πούλο!", 1),
]

class BirdWindow(mingui.Dialog):
    def __init__(self, typ, value, tback):
        mingui.Dialog.__init__(self, title=random.choice(reduce(list.__add__, [[t[0]]*t[1] for t in titles])))

        box = mingui.Box(self.place(), 'vertical')
        hbox = mingui.Box(box.place(), 'horizontal')

        mingui.Image(hbox.place(stretch=0), 
                     Image.open(os.path.join(settings.DATADIR, 'data', 'images', 'vogel.png')))

        book = mingui.Notebook(hbox.place(stretch=1))

        mingui.Label(book.place(label='Main'), "An error has occured!\nThis should not happen.")

        mingui.Text(book.place(label='Traceback'), multiline=True,
                    text=''.join(traceback.format_exception (typ, value, tback)),
                    enabled=False)
        details = mingui.Text(book.place(label='Details'), multiline=True,
                              text=VerboseTB('NoColor').text(typ, value, tback, context=7),
                              enabled=False)
        details.SetFont(wx.Font(8, wx.MODERN, wx.NORMAL, wx.NORMAL))


        button = mingui.Button(box.place(stretch=0), "That's OK",
                               connect={'clicked': self.close})


def excepthook(type, value, traceback):
    sys.__excepthook__(type, value, traceback)
    bw = BirdWindow(type, value, traceback)
    bw.show(modal=True)
    bw.destroy()

def main():
    sys.excepthook = excepthook
    import mgrafit
    mgrafit.main()
#    app = gui.Application()
#    app.splash()
#    from ui_main import MainWindow
#    MainWindow.args = args
#    app.run(MainWindow)

if __name__ == '__main__':
    main()
