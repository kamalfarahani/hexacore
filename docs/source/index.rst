hexacore
========

A hexagonal architecture framework for Python.

``hexacore`` provides reusable building blocks for applications structured
around the ports-and-adapters (hexagonal) pattern:

* a :doc:`message bus <guide/message_bus>` for dispatching commands and events,
* a :doc:`repository <guide/repository>` abstraction with a SQLAlchemy adapter,
* a :doc:`unit of work <guide/unit_of_work>` for transactional boundaries, and
* a :doc:`broker <guide/broker>` integration for publishing and listening to events.

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   guide/introduction
   guide/installation
   guide/message_bus
   guide/repository
   guide/unit_of_work
   guide/broker

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/hexacore/index

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
