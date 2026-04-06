.. yMMSL Python bindings documentation master file, created by
   sphinx-quickstart on Thu Jun 21 11:07:11 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

yMMSL Python bindings
=====================

Welcome to the documentation pages for yMMSL, the YAML version of the Multiscale
Modeling and Simulation Language. At the moment, yMMSL is mainly the
configuration language for the MUSCLE3 multiscale coupling library.

This library provides Python bindings for yMMSL. With it, you can read and write
yMMSL files, and manipulate them using a Python object representation of their
contents. This documentation gives an overview of the format, and a description
of the Python API.

This documentation describes the latest version of the ``ymmsl`` package, which supports
yMMSL version 0.2. There is `documentation for the old version 0.1`_ as well, or click
the downward arrow in the blue box at the top left, and select ``release-0.14.0``.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   basic_usage
   data_model_overview
   describing_models
   describing_scenarios
   describing_programs
   describing_runs
   creating_from_python
   functionality
   upgrading_to_v0_2


API Reference
=============

.. toctree::
  :maxdepth: 2

  API reference <api.rst>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _documentation for the old version 0.1: https://ymmsl-python.readthedocs.io/en/release-0.14.0/
