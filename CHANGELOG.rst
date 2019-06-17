###########
Change Log
###########

All notable changes to this project will be documented in this file.
This project adheres to `Semantic Versioning <http://semver.org/>`_.

0.8.0
*****

Changed
-------

* Rename YmmslDocument to Configuration
* Rename version field to ymmsl_version

0.7.0
*****

Changed
-------

* Significant API changes/cleanup (not backwards compatible!)
* Small fixes


0.6.0
*****

Changed
-------

* Easier-to-use API (not backwards compatible!)

Fixed
-----

* Boolean-valued Experiment parameter values
* Improved output formatting of list and array settings values


0.5.1
*****

Changed
-------

* Remove MAP operator (mappers should use F_INIT and O_F)

Added
-----

* Support for slots on Conduits
* Support for simulation parameters of type bool
* Export ParameterValue type


0.5.0
*****

Changed
-------

* Add multiplicity to ComputeElementDecl

Fixed
-----

* ComputeElementDecl has a Reference for its name
* Savorizing issue in ComputeElementDecl


0.4.0
*****

Changed
-------

* Reference is now (intended to be) an immutable sequence of parts
* Reference is hashable
* Reference is equality comparable


0.3.0
*****

Fixed
-----

* Renamed Endpoint to Port
* Simplified Conduit


0.2.1
*****

Added
-----

* Endpoint class


0.2.0
*****

Added
-----

* Operator enum


0.1.0
*****

Added
-----

* Initial version with basic functionality
