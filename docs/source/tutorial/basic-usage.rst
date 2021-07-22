Basic Usage
-----------

To start using ParData, first import the package:

.. code-block:: python

   >>> import pardata

This implicitly calls ``pardata.init()`` and initializes ParData to be ready to retrieve datasets from the default
repository (Note: We will learn about switching to a non-default repository in :doc:`create-schema`). To see the available
datasets and their versions included in this repository, run

.. code-block:: python

   >>> pardata.list_all_datasets()
   {'claim_sentences_search': ('1.0.2',), ..., 'wikitext103': ('1.0.1',)}

To look up information about a particular dataset, use the function ``pardata.describe_dataset()`` as shown below:

.. code-block:: python

   >>> print(pardata.describe_dataset('wikipedia_category_stance'))
   Description: Wikipedia categories and lists annotated for stance (Pro/Con) towards the concepts
   Homepage: https://developer.ibm.com/exchanges/data/all/wikipedia-category-stance/
   Size: 525K
   Published date: 2019-08-01
   License: Creative Commons Attribution 3.0 Unported
   Available subdatasets: full

Use ``pardata.load_dataset()`` to load a dataset. It will first download the specified dataset with the specified version
(default is the latest version) if it's not already downloaded, and then load it in memory.

.. code-block:: python

   >>> wcs_data = pardata.load_dataset('wikipedia_category_stance')

ParData will download the `IBM Debater® Wikipedia Category Stance
<https://developer.ibm.com/exchanges/data/all/wikipedia-category-stance/>`__ dataset (latest version
``1.0.2``) if it's not already downloaded, and then load it to the variable ``wcs_data``.

``wcs_data`` is a :class:`dict` that stores the loaded content of the dataset. It has one key ``'full'``, which is the
identifier of a subdataset, i.e., a subdivision of the whole dataset. ``wikipedia_category_stance`` has only one
subdataset because it's a small dataset, hence ``wcs_data`` has only one key. Because ``wikipedia_category_stance`` is
in CSV format, ParData will automatically load the dataset to ``wcs_data['full']`` as a :class:`pandas.DataFrame` object, which is a
convenient way to manipulate CSV files in Python:

.. code-block:: python

   >>> type(wcs_data['full'])
   <class 'pandas.core.frame.DataFrame'>

We can also customize how and what type of object each file format should be loaded to in ParData. How to do so is outside
the scope of this tutorial.

By default, :func:`pardata.load_dataset` downloads to and loads from
:file:`~/.pardata/data/<dataset-name>/<dataset-version>/`. To view this information, run:

.. code-block:: python

   >>> pardata.get_config().DATADIR
   PosixPath('/home/username/.pardata/data')

To change this default data directory, use :func:`pardata.init`.

.. code-block:: python

   pardata.init(DATADIR='new/dir/to/download/load/from')
