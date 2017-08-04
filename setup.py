#!/usr/bin/python
"""Install the polar2tcx script

Run

  python setup.py install

to install. Then you can run the script from everywhere by typing

  polar2tcx.py

"""

from setuptools import setup

setup(name='Polar2tcx',
      version='1.0',
      description='Convert polar xml and gpx files to tcx',
      author='Eirik Marthinsen, Frank Meffert',
      author_email='eirikma@gmail.com',
      url='https://github.com/marthinsen/polar2tcx',
      scripts=['polar2tcx.py'])
