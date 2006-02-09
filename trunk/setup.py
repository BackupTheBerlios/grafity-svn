import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages
setup(
    name = "grafity",
    version = "0.1",
    packages = find_packages(),
    install_requires = ["mimetex"],

    entry_points = {
        'gui_scripts': [ 'grafity = grafity.ui.start:main', ]
    },

    include_package_data = True,

    package_data = {
        'grafity': ['data/scripts/*.py'], 
    },
    author = "Daniel Fragiadakis",
    author_email = "danielf@gmail.com",
#    description = "",
    license = "GPL",
    url = "http://grafity.berlios.de",
)
