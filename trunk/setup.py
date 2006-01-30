import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages
setup(
    name = "grafity",
    version = "0.1",
    packages = find_packages(),
    install_requires = ["odr", "mimetex"],

    entry_points = {
        'gui_scripts': [
            'grafity = grafity.ui.start:main',
        ]
    }
)
