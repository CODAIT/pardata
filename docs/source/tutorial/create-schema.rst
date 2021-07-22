Example: Create a Schema for Dakota's Height Journey
----------------------------------------------------

Dakota is 17 years old. She has measured her heights every year since she was 8. She decides to contribute her height
history for scientific research. She recorded her height history in a CSV table:
::

   age,height
   8,130
   9,135
   10,141
   11,142
   12,150
   13,159
   14,164
   15,172
   16,174
   17,175

She wrote a README document: ::

   Dakota's height history. Heights are in centimeters.

   To the extent possible under law, Dakota has dedicated all copyright and related and neighboring rights to this
   dataset worldwide. You should have received a copy of the CC0 Public Domain Dedication along with this software. If
   not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

She then packed the data file and the README to a tarball ``dakota-height-history.tar.gz``:

.. code-block:: console

   $ tar tf dakota-height-history.tar.gz
   README
   height.csv

She then uploaded the tarball to a `public server
<https://pardata.readthedocs.io/en/latest/_static/dakota-height-history.tar.gz>`__. To ease the process for scientists to
work with her height history, she decides to ask for your help with creating a ParData schema file for the tarball.

To get started, create a yaml file ``dakota.yaml`` with the following header:

.. code-block:: yaml

   api_name: com.ibm.pardata.v1
   name: dakota
   last_updated: 2021-06-25
   datasets:
     heights:
       "1.0":
         <schema>

Then add some meta information about the dataset to ``<schema>``:

.. code-block:: yaml

   name: Dakota's Height History
   published: 2021-06-25
   homepage: https://example.org/dakota
   download_url: https://pardata.readthedocs.io/en/latest/_static/dakota-height-history.tar.gz
   # Obtained by running  sha512sum dakota-height-history.tar.gz
   sha512sum: b48ae99e685667d4399ea8e175c777de54ae7ae603ff08ffbaae415cebb46b96f130590019c48c46f0d440d9901d7dfee1445c4ba1a465f7facf3fe3ebb1a5a5
   # Obtained by searching https://spdx.org/licenses/
   license: CC0-1.0
   estimated_size: 10K
   description: Dakota's height history from 8 to 17. Heights are in centimeters.

Then, add some information about the dataset's content:

.. code-block:: yaml

   subdatasets:
     full:
       name: Full
       description: Full Dataset
       format:
         # This is table/csv because we are using CSV format
         id: table/csv
         options:
           columns:
             # Two columns, "age" and "height". Both are integer types.
             age: 'int'
             height: 'int'
       path: height.csv

Put it together, we have ``dakota.yaml``:

.. code-block:: yaml

   api_name: com.ibm.pardata.v1
   name: dakota
   last_updated: 2021-06-25
   datasets:
     heights:
       "1.0":
         name: Dakota's Height History
         published: 2021-06-25
         homepage: https://example.org/dakota
         download_url: https://pardata.readthedocs.io/en/latest/_static/dakota-height-history.tar.gz
         # Obtained by running  sha512sum dakota-height-history.tar.gz
         sha512sum: b48ae99e685667d4399ea8e175c777de54ae7ae603ff08ffbaae415cebb46b96f130590019c48c46f0d440d9901d7dfee1445c4ba1a465f7facf3fe3ebb1a5a5
         # Obtained by searching https://spdx.org/licenses/
         license: CC0-1.0
         estimated_size: 10K
         description: Dakota's height history from 8 to 17. Heights are in centimeters.
         subdatasets:
           full:
             name: Full
             description: Full Dataset
             format:
               # This is table/csv because we are using CSV format
               id: table/csv
               options:
                 columns:
                   # Two columns, "age" and "height". Both are integer types.
                   age: 'int'
                   height: 'int'
             path: height.csv

To use this file, switch the default dataset repository to the path of this file:

.. code-block:: python

   >>> import pardata
   >>> pardata.init(DATASET_SCHEMA_FILE_URL='/path/to/dakota.yaml')

To confirm:

.. code-block:: python

   >>> pardata.list_all_datasets()
   {'heights': ('1.0',)}

To load the dataset:

.. code-block:: python

   >>> dakota_heights = pardata.load_dataset('heights')
   >>> dakota_heights['full']
      age  height
   0    8     130
   1    9     135
   2   10     141
   3   11     142
   4   12     150
   5   13     159
   6   14     164
   7   15     172
   8   16     174
   9   17     175

``dakota_heights['full']`` is a :class:`pandas.DataFrame` object that data scientists can comfortably work with. For
example, to see heights in inches, simply do

.. code-block:: python

   >>> dakota_heights['full'].height *= 0.394
   >>> dakota_heights['full']
      age  height
   0    8  51.220
   1    9  53.190
   2   10  55.554
   3   11  55.948
   4   12  59.100
   5   13  62.646
   6   14  64.616
   7   15  67.768
   8   16  68.556
   9   17  68.950
