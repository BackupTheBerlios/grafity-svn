from distutils.core import setup
import sys,os
import glob
from distutils.core import Extension
import distutils.sysconfig


def add_ft2font_flags(module):
    'Add the module flags to build extensions which use gd'
    module.libraries.extend(['freetype'])
#, 'z' ])
#    add_base_flags(module)

    basedirs = module.include_dirs[:]  # copy the list to avoid inf loop!
    for d in basedirs:
        module.include_dirs.append(os.path.join(d, 'freetype2'))
        p = os.path.join(d, 'lib/freetype2/include')
        if os.path.exists(p): module.include_dirs.append(p)
        p = os.path.join(d, 'lib/freetype2/include/freetype2')
        if os.path.exists(p): module.include_dirs.append(p)

    basedirs = module.library_dirs[:]  # copy the list to avoid inf loop!
    for d in basedirs:
        p = os.path.join(d, 'freetype2/lib')
        if os.path.exists(p): module.library_dirs.append(p)
            
    if sys.platform == 'win32':
        module.include_dirs.append(r'..\win32\include')
        module.include_dirs.append(r'..\win32\include\freetype2')
        module.library_dirs.append(r'..\win32\lib')
#        module.libraries.append('gw32c')

    # put this last for library link order     
    module.libraries.extend(['stdc++', 'm'])

    module.include_dirs.append('/usr/include/freetype2/')
    module.include_dirs.append('.')

deps = ['src/ft2font.cpp', 'src/mplutils.cpp']
deps.extend(glob.glob('CXX/*.cxx'))
deps.extend(glob.glob('CXX/*.c'))

module = Extension('ft2font', deps)
add_ft2font_flags(module)

setup(name="ft2font",
      ext_modules = [module],
      include_dirs = ['/usr/include/freetype2/', '.'],
      )
