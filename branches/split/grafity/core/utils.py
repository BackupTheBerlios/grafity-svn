import doctest
import os
import sys


def test(filename):
    red = '\x1b[1;31m'
    green = '\x1b[1;32m'
    default = '\x1b[0m'
    print >>sys.stderr, 'Testing', filename,
    failed, total = doctest.testfile(filename)
    if failed == 0:
        print >>sys.stderr, green+'ok!, '+ str(total)+ ' tests passed' + default
    else:
        print >>sys.stderr, red+str(failed), 'tests failed'+default
