import os
import sys

def freeze():
    os.system(r'cx_Freeze-3.0.1\FreezePython.exe ../grafit/main.py '
	      r'--target-dir=dist/grafit '
	      r'--include-modules=grafit '
	      r'--include-path=.. ')

def data():
    os.system(r'xcopy ..\data dist\data\ /e')

def make_wxs():
    template = open('grafit.wxst', 'rb')
    output = open('grafit.wxs', 'wb')
    dll_line = r"<File Id='%(fileid)s' Name='%(shortname)s' LongName='%(filename)s' DiskId='1' src='%(filesrc)s' Vital='yes' />"

    for line in template:
        if line.strip() == dll_line:
            for n, f in enumerate(os.listdir('dist/grafit')):
                if not f.endswith('.exe'):
                    output.write(dll_line % {'fileid': 'dll%d' % n, 
                                             'shortname' : 'dll%d'% n,
                                             'filename' : f,
                                             'filesrc' : 'dist/grafit/'+f} + '\r\n')
                    print 'added dll: %s' % f
        else:
            output.write(line)

if __name__ == '__main__':
    if 'freeze' in sys.argv[1:]:
        freeze()
    if 'wxs' in sys.argv[1:]:
        make_wxs()
    if 'data' in sys.argv[1:]:
        data()
