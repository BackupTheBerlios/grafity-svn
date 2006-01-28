import __mimetex
import os
import qt

def mimetex(expression):
    filename = __mimetex.mimetex_data(expression)
    pix = qt.QPixmap(filename)
    os.remove(filename)
    return pix
