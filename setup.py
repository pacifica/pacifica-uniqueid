#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Setup and install the UniqueID service."""
from os import path
from setuptools import setup, find_packages


setup(
    name='pacifica-uniqueid',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description='Pacifica UniqueID',
    url='https://github.com/pacifica/pacifica-uniqueid/',
    long_description=open(path.join(
        path.abspath(path.dirname(__file__)),
        'README.md')).read(),
    long_description_content_type='text/markdown',
    author='David Brown',
    author_email='david.brown@pnnl.gov',
    packages=find_packages(include=['pacifica.*']),
    namespace_packages=['pacifica'],
    entry_points={
        'console_scripts': [
            'pacifica-uniqueid=pacifica.uniqueid.__main__:main',
            'pacifica-uniqueid-cmd=pacifica.uniqueid.__main__:cmd'
        ]
    },
    install_requires=[
        'cherrypy',
        'pacifica-namespace',
        'peewee>2'
    ]
)
