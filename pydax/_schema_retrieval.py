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
from urllib.parse import urlparse
from urllib.request import urlopen

import requests


def retrieve_schema_file(url_or_path: str) -> str:
    """Retrieve a single schema file.

    :param url_or_path: URL or path to the schema file
    :raises ValueError: An error occurred when parsing `url_or_path` as either a URL or path
    :return: A string of the content
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
