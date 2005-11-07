import re
import string
import sys
import os.path
import sets

#from numarray import *
#from numarray.ieeespecial import nan
from scipy import *

def most_frequent(seq):
    """returns the element in a sequence that appears the most times"""
    freq = {}
    for l in seq:
        freq[l] = 1 + freq.get (l, 0)
    l = [(f[1], f[0]) for f in freq.items()]
    l.sort()
    return l[-1][1]

def parse_float(st):
    """Same as float(st) but returns nan instead of raising an exception
       on invalid input"""
    try:
        return float (st)
    except (ValueError, TypeError):
        return nan

def isnan(x):
    return [xi is nan for xi in x]
     
def import_ascii(str, delimiter=None, decimal_symbol='.', max_lines = None):
    """Read data from a delimited ascii file. Returns the data and header.
       We try to guess the delimiter by finding the one that occurs the
       most times. The argument can be a file object, a filename or the
       ascii data as a string

       Limitations:
       - loads the entire file into memory. not useful for huge files
       - doesn't handle free-format delimited text

       Eventually I want it to handle everything in 
       http://mail.gnome.org/archives/guppi-list/1998-November/msg00000.html
    """

    # guess the type of argument
    if hasattr(str, 'readlines'):  # a file object
        text = str.readlines()
    elif os.path.exists(str): # a filename
        text = open(str).readlines()
    else: # a string
        text = str.splitlines()
        if len(text) == 1:
            return None, None

    # remove commented portions and empty lines. We save the lines we change
    # in case they are part of the header
    commented = {}
    for n, line in zip(range(len(text))[::-1], text[::-1]):
        if '#' in line:
            text[n] = line[0:line.index('#')]
            commented[n] = line
        if line.strip() == '':
            del text[n]
    if len(text) == 0:
        return None, None

    if delimiter is None:
        # find delimiters
        number_rexp = re.compile(r'[-+]?(?:[0-9]*%s)?[0-9]*(?:[eE][-+]?[0-9]+)?'
                                 % re.escape(decimal_symbol)) # matches numbers
        delimiters = []
        for line in text:
            for d in number_rexp.split(line.strip()):
                delimiters.append (d)
            
        delim = most_frequent (delimiters)
    else:
        delim = delimiter

    # if the delimiter is all whitespace, accept any whitespace
    # otherwhise, strip whitespace
    if sum([x in string.whitespace for x in delim]) == len(delim):
        delim = None
    else:
        delim = delim.strip()

    # extract numbers
    numbers = [[parse_float(s.replace(decimal_symbol, '.')) for s in line.strip().split(delim)] 
                    for line in text[:max_lines]]

    # make all lines the same length
    columns = max (len(l) for l in numbers)
    for n in numbers:
        n.extend ([nan] * (columns - len(n)))

    # build array from non-empty lines and columns
    validlines = [i for i, j in enumerate(numbers) if isnan(j) != [True]*columns]
    validcols = [c for c in xrange(columns) 
                 if isnan([numbers[l][c] for l in validlines]) != [True]*len(validlines)]
    arr = array([[numbers[lin][c] for c in validcols] for lin in validlines], 'd')

    # build header from initial lines
    header = []
    for i in xrange (validlines[0]):
        if i in commented:
            header.append(commented[i])
        else:
            header.append(text[i])

    return transpose(arr), header
