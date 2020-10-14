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


from typing import Dict

import requests

# These three shall be made configurable in the future
SCHEMA_DATASETS_URL = ('https://raw.github.ibm.com/gist/hongx/d368b6c26164c74eb6a70fb7680fdb9d/raw/'
                       '4d9d2dfa22c13f1bc4d8d9068638cac9c85afee1/schema-datasets.yaml?'
                       'token=AABVD5XY77RMMDELIF7TMA27SCRBY')
SCHEMA_FORMATS_URL = ('https://raw.github.ibm.com/gist/hongx/d368b6c26164c74eb6a70fb7680fdb9d/raw/'
                      '4d9d2dfa22c13f1bc4d8d9068638cac9c85afee1/schema-formats.yaml?'
                      'token=AABVD5WTPC3S6DRS2MCPG2K7SCRGM')
SCHEMA_LICENSES_URL = ('https://raw.github.ibm.com/gist/hongx/d368b6c26164c74eb6a70fb7680fdb9d/raw/'
                       '4d9d2dfa22c13f1bc4d8d9068638cac9c85afee1/schema-licenses.yaml?'
                       'token=AABVD5S7ATCJODC3TWIVE627SCRKE')


def retrieve_schema_files() -> Dict[str, str]:
    """Retrieve the schema files.

    :return: A dict in which the kind of the schema is a key (`datasets`, `formats`, or `licenses`), and its value is
    the content of the corresponding schema file.

    """

    datasets = requests.get(SCHEMA_DATASETS_URL, allow_redirects=True)
    formats = requests.get(SCHEMA_FORMATS_URL, allow_redirects=True)
    licenses = requests.get(SCHEMA_LICENSES_URL, allow_redirects=True)

    return {
        'datasets': datasets.text,
        'formats': formats.text,
        'licenses': licenses.text,
    }
