import os.path
from zipfile import ZipFile
from setuptools import setup, Extension

if not os.path.exists('src'):
    z = ZipFile('mimetex.zip')
    os.mkdir('src')
    for filename in ["gifsave.c", "mimetex.c", 'mimetex.h', 'texfonts.h']:
        open(os.path.join('src', filename), 'w').write(z.read(filename))


ext = Extension('__mimetex', 
    ['pyqmimetex.c', 'src/gifsave.c', 'src/mimetex.c'], 
     define_macros=[('GIF', None), ('AA', None)],
     include_dirs=['src'],
)
    
setup(name='mimetex',
      version='0.1',
      packages=['mimetex'],
      package_dir={'mimetex': ''},
      ext_modules=[ext]
)      

for fn in os.listdir('src'):
    os.remove(os.path.join('src', fn))
os.rmdir('src')
