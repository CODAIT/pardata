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


from pathlib import Path
from typing import Dict
from urllib.parse import urlparse
from urllib.request import urlopen

import requests

# These three shall be made configurable in the future
DEFAULT_SCHEMA_DATASETS_URL = ('https://raw.github.ibm.com/gist/hongx/d368b6c26164c74eb6a70fb7680fdb9d/raw/'
                               '4d9d2dfa22c13f1bc4d8d9068638cac9c85afee1/schema-datasets.yaml?'
                               'token=AABVD5XY77RMMDELIF7TMA27SCRBY')
DEFAULT_SCHEMA_FORMATS_URL = ('https://raw.github.ibm.com/gist/hongx/d368b6c26164c74eb6a70fb7680fdb9d/raw/'
                              '4d9d2dfa22c13f1bc4d8d9068638cac9c85afee1/schema-formats.yaml?'
                              'token=AABVD5WTPC3S6DRS2MCPG2K7SCRGM')
DEFAULT_SCHEMA_LICENSES_URL = ('https://raw.github.ibm.com/gist/hongx/d368b6c26164c74eb6a70fb7680fdb9d/raw/'
                               '4d9d2dfa22c13f1bc4d8d9068638cac9c85afee1/schema-licenses.yaml?'
                               'token=AABVD5S7ATCJODC3TWIVE627SCRKE')


def retrieve_schema_file(url_or_path: str) -> str:
    """Retrieve a single schema file.

    :param url_or_path: URL or path to the schema file.
    :raises ValueError: An error occurred when parsing `url_or_path` as either a URL or path.

    :return: A string of the content.
    """

    scheme = urlparse(url_or_path).scheme

    if scheme in ('http', 'https'):
        return requests.get(url_or_path, allow_redirects=True).text
    elif scheme == 'file':
        with urlopen(url_or_path) as f:  # nosec: bandit will always complain but we know the URL points to a local file
            return f.read().decode('UTF-8')
    elif scheme == '':
        return Path(url_or_path).read_text()
    else:
        raise ValueError(f'Unknown scheme in "{url_or_path}": "{scheme}"')


def retrieve_schema_files(*,
                          datasets_url_or_path: str = DEFAULT_SCHEMA_DATASETS_URL,
                          formats_url_or_path: str = DEFAULT_SCHEMA_FORMATS_URL,
                          licenses_url_or_path: str = DEFAULT_SCHEMA_LICENSES_URL) -> Dict[str, str]:
    """Retrieve the schema files.

    :param datasets_url_or_path: URL or path to the datasets schema file.
    :param formats_url_or_path: URL or path to the formats schema file.
    :param licenses_url_or_path: URL or path to the licenses schema file.

    :return: A dict in which the kind of the schema is a key (`datasets`, `formats`, or `licenses`), and its value is
    the content of the corresponding schema file.
    """

    datasets = retrieve_schema_file(datasets_url_or_path)
    formats = retrieve_schema_file(formats_url_or_path)
    licenses = retrieve_schema_file(licenses_url_or_path)

    return {
        'datasets': datasets,
        'formats': formats,
        'licenses': licenses,
    }
