#
# Copyright 2020 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"Retrieve remote schema file."


import requests


# These two shall be made configurable in the future
SCHEMA_DATASETS_URL = ('https://raw.github.ibm.com/CODAIT/dax-api/master/examples/schema-datasets.yaml'
                       '?token=AABVD5UVIVNN5WTXWAROZJC7RYJC6')
SCHEMA_METADATA_URL = ('https://raw.github.ibm.com/CODAIT/dax-api/master/examples/schema-metadata.yaml'
                       '?token=AABVD5WRQ5YEVSGNNPTUEJ27RYI5K')


def retrieve_schema_files():
    """Retrieve the schema files.

    :return: A 2-tuple consisting of the string of the dataset schema and the string of the metadata schema.
    """

    datasets = requests.get(SCHEMA_DATASETS_URL, allow_redirects=True)
    metadata = requests.get(SCHEMA_METADATA_URL, allow_redirects=True)

    return datasets.text, metadata.text
