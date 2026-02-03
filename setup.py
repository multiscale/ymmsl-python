#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

setup(
    name='ymmsl',
    version='0.14.1-dev',
    description="Python bindings for the YAML version of the Multiscale Modeling and Simulation Language",
    long_description=readme + '\n\n',
    author="Lourens Veen",
    author_email='l.veen@esciencecenter.nl',
    url='https://github.com/multiscale/ymmsl-python',
    packages=find_packages(include=['ymmsl', 'ymmsl.*']),
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
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ],
    python_requires='>=3.7, <4',
    test_suite='tests',
    install_requires=[
        'click>=6.5',
        # 'yatiml>=0.11.1,<0.12.0',
        'yatiml @ git+https://github.com/yatiml/yatiml@develop#egg=yatiml'
    ],
    entry_points={
        'console_scripts': ['ymmsl=ymmsl.command_line:ymmsl']
    },
)
