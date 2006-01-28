from setuptools import setup, Extension

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
