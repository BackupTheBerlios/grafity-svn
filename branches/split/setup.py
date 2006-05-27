import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages
setup(
    name = "grafity",
    version = "0.1",
    packages = find_packages(),

    entry_points = {
        'gui_scripts': [ 'grafity = grafity.ui.main:main', ]
    },

#    include_package_data = True,

#    package_data = {
#        'grafity': ['data/scripts/*.py', 'data/scripts'], 
#    },
    author = "Daniel Fragiadakis",
    author_email = "danielf@gmail.com",
    license = "GPL",
    url = "http://grafity.berlios.de",
)
