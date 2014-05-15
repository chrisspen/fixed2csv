#!/usr/bin/env python
import os
import urllib

from setuptools import setup, find_packages, Command

import fixed2csv

setup(
    name = "fixed2csv",
    version = fixed2csv.__version__,
    py_modules=['fixed2csv'],
    scripts=['fixed2csv.py'],
    author = "Chris Spencer",
    author_email = "chrisspen@gmail.com",
    description = "Converts data files formatted in fixed-width columns to CSV.",
    license = "LGPL",
    url = "https://github.com/chrisspen/fixed2csv",
    #https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires = [
        'pytz>=2013.8',
        'python-dateutil>=2.2',
    ],
    zip_safe = False,
)
