#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

setup(
    name='ymmsl',
    version='0.11.0',
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    test_suite='tests',
    install_requires=[
        'ruamel.yaml<=0.16.12',
        'yatiml>=0.7.0'
    ],
    setup_requires=[
        # dependency for `python setup.py test`
        'pytest-runner',
        # dependencies for `python setup.py build_sphinx`
        'sphinx',
        'recommonmark',
        'sphinx_rtd_theme'
    ],
    tests_require=[
        'pytest>=3.3,<6.2',
        'pytest-cov',
        'pytest-mypy',
        'pytest-flake8',
        'importlib-metadata==2.1.0'
    ],
)
