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
from typing import Union
from urllib.parse import urlparse
from urllib.request import urlopen

import requests

from . import _typing


# Semantically, _typing.PathLike doesn't cover strings that represent URLs
def retrieve_schema_file(url_or_path: Union[_typing.PathLike, str], encoding: str = 'utf-8') -> str:
    """Retrieve a single schema file.

    :param url_or_path: URL or path to the schema file.
    :param encoding: The encoding of the text in ``url_or_path``.
    :raises ValueError: An error occurred when parsing `url_or_path` as either a URL or path.
    :return: A string of the content.
    """
    url_or_path = str(url_or_path)
    parse_result = urlparse(url_or_path)
    scheme = parse_result.scheme

    if not all(tuple(parse_result.scheme, parse_result.netloc, parse_result.path)):
        # Not a URL, treated as a local file path
        return Path(url_or_path).read_text(encoding)
    elif scheme in ('http', 'https'):
        content = requests.get(url_or_path, allow_redirects=True).content
        # We don't use requests.Response.encoding and requests.Response.text because it is always silent when there's an
        # encoding error
        return content.decode(encoding)
    elif scheme == 'file':
        with urlopen(url_or_path) as f:  # nosec: bandit will always complain but we know the URL points to a local file
            return f.read().decode(encoding)
    else:
        raise ValueError(f'Unknown scheme in "{url_or_path}": "{scheme}"')
