from distutils.core import setup
from distutils.extension import Extension
#from Pyrex.Distutils import build_ext
import platform

if platform.system() == 'Linux':
    opengllib = 'GL'
elif platform.system() == 'Windows':
    opengllib = 'OpenGL32'


setup(name="graph_render", 
      ext_modules=[Extension("graph_render", ["graph_render.c", "thirdparty/gl2ps.c"], 
      libraries=[opengllib])],
      include_dirs='thirdparty',
)
#      cmdclass={'build_ext': build_ext })
