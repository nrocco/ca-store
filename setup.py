#!/usr/bin/env python
from setuptools import setup
import ca

#long_description = open('README.rst').read(),
#license = open('LICENSE').read(),

setup(
    name = 'ca',
    version = ca.__version__,
    packages = [
        'ca'
    ],
    entry_points = {
        'console_scripts': [
            'ca = ca.commands:main',
        ]
    },
    install_requires = [
        'pycli-tools>=1.6.0',
    ],
    download_url = 'http://github.com/nrocco/pycli-tools',
    url = 'http://nrocco.github.io/',
    author = ca.__author__,
    author_email = 'dirocco.nico@gmail.com',
    description = 'A python module to be your own CA',
    include_package_data = True,
    zip_safe = False,
    classifiers = [
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
