.. include:: ../../README.rst
   :start-after: readme-start


.. toctree::
   :caption: Tutorial
   :name: tutorial
   :maxdepth: 1

   tutorial/install
   tutorial/basic-usage
   tutorial/schema
   tutorial/create-schema

API References
==============

Top-Level
---------

.. autosummary::
   :caption: API References
   :toctree: api-references
   :template: our-module.rst

   pardata
   pardata.dataset
   pardata.exceptions
   pardata.schema

Loaders
-------

.. autosummary::
   :caption: API References (Loaders)
   :toctree: api-references
   :template: our-module.rst

   pardata.loaders
   pardata.loaders.table
   pardata.loaders.text

.. toctree::
   :caption: Schema File Format References
   :glob:
   :maxdepth: 1

   schema

.. toctree::
   :caption: Miscellaneous
   :glob:
   :maxdepth: 1

   miscellaneous/*

Indices and Search
==================

* :ref:`genindex`
* :ref:`search`
