Schema File Format References
=============================

For an introduction of the schema file format, check out :doc:`tutorial/schema`.

Top-Level Keys
--------------

A schema file is a yaml file that gathers multiple schemata. It can be seen as representing a dataset repository. These
schemata may be gathered together because they are within the same community, share the same ownership, or for any other
reasons. It is typically structured as:

.. code-block:: yaml

   api_name: com.ibm.pardata.v1
   last_updated: <ISO date string of last update>
   datasets:
     <dataset1_id>:
       <version1>:
         <the schema of dataset1_id version1>
       <version2>:
         <the schema of dataset1_id version2>
       ...
     <dataset2_id>:
       <version1>:
         <the schema of dataset2_id version1>
       <version2>:
         <the schema of dataset2_id version2>
       ...

.. object:: api_name

   Should always be ``com.ibm.pardata.v1``.

.. object:: last_updated

   The date in which the file was last updated. This should be in ISO format, such as ``2021-06-20``.

.. object:: datasets

   A dictionary of datasets. The key of each item is a dataset identifier, and the value of each item is another
   dictionary. In this dictionary, each key is a version string (e.g., ``"1.2.3"``) representing a particular version of
   a dataset in the dataset series; each value is a schema for the dataset.

   .. code-block:: yaml

     <dataset1_id>:
       <version1>:
         <the schema of dataset1_id version1>
       <version2>:
         <the schema of dataset1_id version2>
       ...


Schema
------

A schema is a tree-like data structure that describes a dataset or a format, or a license. It contains information such
as the download URL, license, format descriptions of a dataset. We usually represent them in the yaml format, or as a
Python ``dict`` in a Python program.

Each schema follows the following structure:

.. code-block:: yaml

   name: <dataset name>
   published: <published date>
   homepage: <homepage URL>
   download_url: <download URL>
   sha512sum: <sha512sum of the dataset file>
   license: <SPDX license token or custom license symbol>
   estimated_size: <estimated size>
   description: <description>
   subdatasets:
     <subdataset1_id>:
       <Subdataset Dict: Dictionary that describes subdataset1_id>
     <subdataset2_id>:
       <Subdataset Dict: Dictionary that describes subdataset2_id>
     ...

.. object:: name

   Human-readable name of the dataset.

.. object:: published

   Published date in ISO format.

.. object:: homepage

   Homepage URL.

.. object:: download_url

   Download URL.

.. object:: sha512sum

   sha512sum of the dataset file. It can be generated using ``sha512sum data-file.tar.gz``)

.. object:: license

   SPDX license token or custom license symbol.

.. object:: estimated_size

   Estimated size of the dataset.

.. object:: description

   Description of the dataset.

.. object:: subdatasets

   A dictionary that divides the datasets into multiple subdatasets and describes them. The keys of the dictionary
   are subdataset identifiers and values are dictionaries that describe the subdataset.

Subdataset Dict
---------------

A subdataset dict describes a subdataset, which is a logical subdivision of the dataset.

.. object:: name

   Name of the subdataset.

.. object:: description

   Description of the subdataset.

.. object:: format

   A dictionary that describes the format of the subdataset.

   .. object:: id

      Identifier of the format specified in ``FORMAT_SCHEMA_FILE_URL``.

   .. object:: path

      Path to the file of this subdataset. It can also be a dictionary to specify a regular expression. For example,
      ::

          path:
            type: regex
            value: "TensorFlow-Speech-Commands/house/.*\\.wav"

   .. object:: options

      A dictionary that specifies the options for a particular format. The specification varies by format.

      - ``audio/wav``: No options.
      - ``image/jpeg``: No options.
      - ``image/png``: No options.
      - ``table/csv``

        + ``columns``: A dictionary in which keys are the names of the columns and values are the type of the entries in
          the columns. If it is not specified, then pandas defaults are used.
        + ``delimiter``: The delimiter of the CSV files. Default: ``,``
        + ``encoding``: Encoding of the CSV files. Default: ``UTF-8``

      - ``text/plain``
        + ``encoding``: Encoding of the text files. Default: ``UTF-8``
