#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

setup(
    name='ymmsl',
    version='0.13.1-dev',
    description="Python bindings for the YAML version of the Multiscale Modeling and Simulation Language",
    long_description=readme + '\n\n',
    author="Lourens Veen",
    author_email='l.veen@esciencecenter.nl',
    url='https://github.com/multiscale/ymmsl-python',
    packages=[
        'ymmsl',
    ],
    package_dir={'ymmsl':
                 'ymmsl'},
    include_package_data=True,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='yMMSL multiscale modeling simulation YAML',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.7, <4',
    test_suite='tests',
    install_requires=[
        'yatiml>=0.11.1,<0.12.0'
    ],
)
