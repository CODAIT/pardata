.. role:: file(literal)
.. role:: func(literal)

.. readme-start

ParData
=======

.. image:: https://img.shields.io/pypi/v/pardata.svg
   :target: https://pypi.python.org/pypi/pardata
   :alt: PyPI

.. image:: https://img.shields.io/pypi/pyversions/pardata
   :target: https://pypi.python.org/pypi/pardata
   :alt: PyPI - Python Version

.. image:: https://img.shields.io/pypi/implementation/pardata
   :target: https://pypi.python.org/pypi/pardata
   :alt: PyPI - Implementation

.. image:: https://badges.gitter.im/codait/pardata.svg
   :target: https://gitter.im/codait/pardata
   :alt: Gitter

.. image:: https://github.com/codait/pardata/workflows/Runtime%20Tests/badge.svg
   :target: https://github.com/CODAIT/pardata/commit/master
   :alt: Runtime Tests

.. image:: https://github.com/codait/pardata/workflows/Lint/badge.svg
   :target: https://github.com/CODAIT/pardata/commit/master
   :alt: Lint

.. image:: https://github.com/codait/pardata/workflows/Docs/badge.svg
   :target: https://github.com/CODAIT/pardata/commit/master
   :alt: Docs

.. image:: https://github.com/codait/pardata/workflows/Development%20Environment/badge.svg
   :target: https://github.com/CODAIT/pardata/commit/master
   :alt: Development Environment

ParData (homophone of *partake*) is a Python API that enables data consumers and distributors to easily use and share
datasets, and establishes a standard for exchanging data assets. It enables:

- a data scientist to have a simpler and more unified way to begin working with a wide range of datasets, and
- a data distributor to have a consistent, safe, and open source way to share datasets with interested communities.

.. sidebar:: Quick Example

   .. code-block:: python

      >>> import pardata
      >>> pardata.list_all_datasets()
      {'claim_sentences_search': ('1.0.2',),
       ..., 'wikitext103': ('1.0.1',)}
      >>> pardata.load_dataset('wikitext103')
      {...}  # Content of the dataset

Install the Package & its Dependencies
--------------------------------------

To install the latest version of ParData, run

.. code-block:: console

   $ pip install pardata

Alternatively, if you have downloaded the source, switch to the source directory (same directory as this README file,
``cd /path/to/pardata-source``) and run

.. code-block:: console

   $ pip install -U .

Quick Start
-----------

Import the package and load a dataset. ParData will download `WikiText-103
<https://developer.ibm.com/exchanges/data/all/wikitext-103/>`__ dataset (version ``1.0.1``) if it's not already
downloaded, and then load it.

.. code-block:: python

   import pardata
   wikitext103_data = pardata.load_dataset('wikitext103')

View available ParData datasets and their versions.

.. code-block:: python

   >>> pardata.list_all_datasets()
   {'claim_sentences_search': ('1.0.2',), ..., 'wikitext103': ('1.0.1',)}

To view your globally set configs for ParData, such as your default data directory, use :func:`pardata.get_config`.

.. code-block:: python

   >>> pardata.get_config()
   Config(DATADIR=PosixPath('dir/to/download/load/from'), ..., DATASET_SCHEMA_FILE_URL='file/to/load/datasets/from')

By default, :func:`pardata.load_dataset` downloads to and loads from
:file:`~/.pardata/data/<dataset-name>/<dataset-version>/`. To change the default data directory, use :func:`pardata.init`.

.. code-block:: python

   pardata.init(DATADIR='new/dir/to/download/load/from')

Load a previously downloaded dataset using :func:`pardata.load_dataset`. With the new default data dir set, ParData now
searches for the `Groningen Meaning Bank <https://developer.ibm.com/exchanges/data/all/groningen-meaning-bank/>`__
dataset (version ``1.0.2``) in :file:`new/dir/to/download/load/from/gmb/1.0.2/`.

.. code-block:: python

   gmb_data = load_dataset('gmb', version='1.0.2', download=False)  # assuming GMB dataset was already downloaded

To learn more about ParData, check out `the documentation <https://pardata.readthedocs.io>`__ and the
`tutorial <https://pardata.readthedocs.io#tutorial>`__.
