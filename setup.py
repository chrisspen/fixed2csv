#!/usr/bin/env python
import os
import urllib

from setuptools import setup, find_packages, Command

import fixed2csv

setup(
    name = "fixed2csv",
    version = fixed2csv.__version__,
    packages = find_packages(),
    author = "Chris Spencer",
    author_email = "chrisspen@gmail.com",
    description = "Converts data files formatted in fixed-width columns to CSV.",
    license = "LGPL",
    url = "https://github.com/chrisspen/fixed2csv",
    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: LGPL License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    zip_safe = False,
    #install_requires = ['Django>=1.4.0', 'lxml'],
)
