.. role:: file(literal)
.. role:: func(literal)

.. readme-start

PyDAX
=====

.. image:: https://img.shields.io/pypi/v/pydax.svg
   :target: https://pypi.python.org/pypi/pydax
   :alt: PyPI

.. image:: https://img.shields.io/pypi/pyversions/pydax
   :target: https://pypi.python.org/pypi/pydax
   :alt: PyPI - Python Version

.. image:: https://img.shields.io/pypi/implementation/pydax
   :target: https://pypi.python.org/pypi/pydax
   :alt: PyPI - Implementation

.. image:: https://badges.gitter.im/codait/pydax.svg
   :target: https://gitter.im/codait/pydax
   :alt: Gitter

.. image:: https://github.com/codait/pydax/workflows/Runtime%20Tests/badge.svg
   :target: https://github.com/CODAIT/pydax/commit/master
   :alt: Runtime Tests

.. image:: https://github.com/codait/pydax/workflows/Lint/badge.svg
   :target: https://github.com/CODAIT/pydax/commit/master
   :alt: Lint

.. image:: https://github.com/codait/pydax/workflows/Docs/badge.svg
   :target: https://github.com/CODAIT/pydax/commit/master
   :alt: Docs

.. image:: https://github.com/codait/pydax/workflows/Development%20Environment/badge.svg
   :target: https://github.com/CODAIT/pydax/commit/master
   :alt: Development Environment

PyDAX is a Python API that enables data consumers and distributors to easily use and share datasets, and establishes a
standard for exchanging data assets. It enables:

- a data scientist to have a simpler and more unified way to begin working with a wide range of datasets, and
- a data distributor to have a consistent, safe, and open source way to share datasets with interested communities.

.. sidebar:: Quick Example

   .. code-block:: python

      >>> import pydax
      >>> pydax.list_all_datasets()
      {'claim_sentences_search': ('1.0.2',),
       ..., 'wikitext103': ('1.0.1',)}
      >>> pydax.load_dataset('wikitext103')
      {...}  # Content of the dataset

Install the Package & its Dependencies
--------------------------------------

To install the latest version of PyDAX, run

.. code-block:: console

   $ pip install pydax

Alternatively, if you have downloaded the source, switch to the source directory (same directory as this README file,
``cd /path/to/pydax-source``) and run

.. code-block:: console

   $ pip install -U .

Quick Start
-----------

Import the package and load a dataset. PyDAX will download `WikiText-103
<https://developer.ibm.com/exchanges/data/all/wikitext-103/>`__ dataset (version ``1.0.1``) if it's not already
downloaded, and then load it.

.. code-block:: python

   import pydax
   wikitext103_data = pydax.load_dataset('wikitext103')

View available PyDAX datasets and their versions.

.. code-block:: python

   >>> pydax.list_all_datasets()
   {'claim_sentences_search': ('1.0.2',), ..., 'wikitext103': ('1.0.1',)}

To view your globally set configs for PyDAX, such as your default data directory, use :func:`pydax.get_config`.

.. code-block:: python

   >>> pydax.get_config()
   Config(DATADIR=PosixPath('dir/to/dowload/load/from'), ..., DATASET_SCHEMA_FILE_URL='file/to/load/datasets/from')

By default, :func:`pydax.load_dataset` downloads to and loads from
:file:`~/.pydax/data/<dataset-name>/<dataset-version>/`. To change the default data directory, use :func:`pydax.init`.

.. code-block:: python

   pydax.init(DATADIR='new/dir/to/dowload/load/from')

Load a previously downloaded dataset using :func:`pydax.load_dataset`. With the new default data dir set, PyDAX now
searches for the `Groningen Meaning Bank <https://developer.ibm.com/exchanges/data/all/groningen-meaning-bank/>`__
dataset (version ``1.0.2``) in :file:`new/dir/to/dowload/load/from/gmb/1.0.2/`.

.. code-block:: python

   gmb_data = load_dataset('gmb', version='1.0.2', download=False)  # assuming GMB dataset was already downloaded

To learn more about PyDAX, check out `the documentation <https://pydax.readthedocs.io>`__ and the
`tutorial <https://pydax.readthedocs.io#tutorial>`__.
