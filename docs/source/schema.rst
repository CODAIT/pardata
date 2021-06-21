Schema File Format References
=============================

Top-Level Keys
--------------

A schema file is a yaml file that gathers multiple schemata. It can be seen as representing a dataset repository. These
schemata may be gathered together because they are within the same community, share the same ownership, or for any other
reasons. It is typically structured as:

.. code-block:: yaml

   api_name: com.ibm.pydax.v1
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

   Should always be ``com.ibm.pydax.v1``.

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
       <Dictionary that describes the subdataset>
     <subdataset2_id>:
       <Dictionary that describes the subdataset>
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
