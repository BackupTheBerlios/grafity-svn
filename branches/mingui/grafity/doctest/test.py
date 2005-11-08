#!/usr/bin/env python2.4

import doctest
import os
import sys

sys.path.append('..')
sys.path.append('../grafit/thirdparty')

red = '\x1b[1;31m'
green = '\x1b[1;32m'
default = '\x1b[0m'


def _test():
    for f in [fn for fn in os.listdir('doctest/') if fn.endswith('.txt')]:
        print >>sys.stderr, 'Testing', f,
        failed, total = doctest.testfile(f)
        if failed == 0:
            print >>sys.stderr, green+'ok!, '+ str(total)+ ' tests passed' + default
        else:
            print >>sys.stderr, red+str(failed), 'tests failed'+default

if __name__=='__main__':
    _test()
