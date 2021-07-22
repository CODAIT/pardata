Schema File Format
==================

A schema is a tree-like data structure that describes a dataset or a format, or a license. It contains information such
as the download URL, license, format descriptions of a dataset. We usually represent them in the yaml format, or as a
Python ``dict`` in a Python program.

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

Below is an example schema that describes the
`IBM Debater® Thematic Clustering of Sentences <https://developer.ibm.com/exchanges/data/all/thematic-clustering-of-sentences/>`_
dataset:

.. code-block:: yaml

   name: IBM Debater® Thematic Clustering of Sentences
   published: 2019-08-01
   homepage: https://developer.ibm.com/exchanges/data/all/thematic-clustering-of-sentences/
   download_url: https://dax-cdn.cdn.appdomain.cloud/dax-thematic-clustering-of-sentences/1.0.2/thematic-clustering-of-sentences.tar.gz
   sha512sum: 08a3f1a9dc06083eb51874e90d7241f67b676af2cbc28fe6a312694051f53391fc95de70fdcdce404de3578fa389558220ea38d34f70265ed88220d0b14f1aba
   license: cc_by_sa_30
   estimated_size: 10.6M
   description: "A benchmark of sentence-clustering based on the partition of Wikipedia articles into sections."
   subdatasets:
     full:
       name: IBM Debater® Thematic Clustering of Sentences
       description: IBM Debater® Thematic Clustering of Sentences complete dataset
       format:
         id: table/csv
         options:
           columns:
             article_title: 'string'
             sentence: 'string'
             cluster_title: 'string'
             article_link: 'string'
       path: dataset.csv

A schema file is a yaml file that gathers multiple schemata. It can be seen as representing a dataset repository. These
schemata may be gathered together because they are within the same community, share the same ownership, or for any other
reasons. It is typically structured as

.. code-block:: yaml

   api_name: com.ibm.pardata.v1
   name: <Identifier of the schema file>
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

Check out :doc:`../schema` for a complete reference and `default ParData repository
<https://github.com/CODAIT/dax-schemata/blob/master/datasets.yaml>`__ for a live example.

For further details, check out :doc:`../schema`.
