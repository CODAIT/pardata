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

"Schema parsing and loading functionality."


from abc import ABC
from copy import deepcopy
from typing import Any, Dict, Union

import requests
import yaml

from . import typing as typing_
from ._schema_retrieval import retrieve_schema_file


SchemaDict = Dict[str, Any]


class SchemaCollection(ABC):
    """Abstract class that provides functionality to load and export a schema collection.

    :param url_or_path: URL or path to a schema file.
    :param tls_verification: When set to ``True``, verify the remote link is https and whether the TLS certificate is
        valid. When set to a path to a file, use this file as a CA bundle file. When set to ``False``, allow http links
        and do not verify any TLS certificates. Ignored if ``url_or_path`` is a local path.
    :raises ValueError: An error occurred when parsing ``url_or_path`` as either a URL or path.
    :raises InsecureConnectionError: The connection is insecure. See ``tls_verification`` for more details.
    """

    def __init__(self, url_or_path: Union[typing_.PathLike, str], *,
                 tls_verification: Union[bool, typing_.PathLike] = True) -> None:
        """Constructor method.
        """
        self._schema_collection: SchemaDict = self._load_retrieved_schema_file(
                                                   retrieve_schema_file(url_or_path,
                                                                        tls_verification=tls_verification))

        # The URL or path from which the schema was retrieved
        self._retrieved_url_or_path: Union[typing_.PathLike, str] = url_or_path

    def _load_retrieved_schema_file(self, schema_file_content: str) -> SchemaDict:
        """Safely loads retrieved schema file.

        :param schema: Retrieved schema file content.
        :return: Nested dictionary representation of a schema.
        """
        return yaml.safe_load(schema_file_content)

    def export_schema(self, *keys: str) -> SchemaDict:
        """Returns a copy of a loaded schema collection. Should be used for debug purposes only.

        :param keys: The sequence of keys that leads to the portion of the schemata to be exported.
        :return: Copy of the schema dictionary.

        Example:

        >>> schema_collection = DatasetSchemaCollection('./tests/schemata/datasets.yaml')
        >>> schema_collection.export_schema('datasets', 'noaa_jfk', '1.1.4')
        {'name': 'NOAA Weather Data – JFK Airport'...}
        """
        schema: SchemaDict = self._schema_collection
        for k in keys:
            schema = schema[k]
        return deepcopy(schema)

    @property
    def retrieved_url_or_path(self) -> Union[typing_.PathLike, str]:
        """The URL or path from which the schema was retrieved.

        Example:

        >>> schema_collection = DatasetSchemaCollection('./tests/schemata/datasets.yaml')
        >>> schema_collection.retrieved_url_or_path
        './tests/schemata/datasets.yaml'
        """
        return self._retrieved_url_or_path


class DatasetSchemaCollection(SchemaCollection):
    """Dataset schema class that inherits functionality from :class:`SchemaCollection`.
    """

    # We have this class here because we reserve the potential to put specific dataset schema code here
    pass


class FormatSchemaCollection(SchemaCollection):
    """Format schema class that inherits functionality from :class:`SchemaCollection`.
    """

    # We have this class here because we reserve the potential to put specific format schema code here
    pass


class LicenseSchemaCollection(SchemaCollection):
    """License schema class that inherits functionality from :class:`SchemaCollection`.

    :param spdx_json_url: URL to the spdx json license file.
    """

    def __init__(self, *args: Any, spdx_json_url: str = 'https://spdx.org/licenses/licenses.json', **kwargs: Any):
        "Constructor Method."

        super().__init__(*args, **kwargs)
        self.spdx_license_json: dict = requests.get(spdx_json_url, stream=True).json()

    def get_license_name(self, identifier: str) -> str:
        """Get the name of the license from its identifier. If not found in the license schema file, turn to SPDX
        license database instead.

        :param identifier: The identifier of the license.
        :return: Name of the license.
        """

        if identifier in self._schema_collection['licenses']:
            return self._schema_collection['licenses'][identifier]['name']
        else:  # look up spdx database
            # This is not efficient, but it's OK for now -- the database is not very large
            spdx_licenses = self.spdx_license_json['licenses']
            for license in spdx_licenses:
                if license['licenseId'] == identifier:
                    return license['name']

            raise ValueError(f'Unknown license {identifier}')


class SchemaCollectionManager():
    """Stores all loaded schema collections in :attr:`schema_collections`.

    :param kwargs: Schema name and schema instance key-value pairs.

    Example:

    >>> dataset_schemata = DatasetSchemaCollection('./tests/schemata/datasets.yaml')
    >>> schema_collection_manager = SchemaCollectionManager(datasets=dataset_schemata)
    >>> license_schemata = LicenseSchemaCollection('./tests/schemata/licenses.yaml')
    >>> schema_collection_manager.add_schema_collection('licenses', license_schemata)
    >>> schema_collection_manager.schema_collections
    {'datasets':..., 'licenses':...}
    """

    def __init__(self, **kwargs: SchemaCollection) -> None:
        """Constructor method
        """
        self.schema_collections: Dict[str, SchemaCollection] = {}
        for name, val in kwargs.items():
            self.add_schema_collection(name, val)

    def add_schema_collection(self, name: str, val: SchemaCollection) -> None:
        """Store :class:`SchemaCollection` instances in a dictionary. If a schema with the same name as ``name`` is
        already stored, it is overridden.

        :param name: Schema collection name.
        :param val: :class:`SchemaCollection` instance.
        """
        if not isinstance(val, SchemaCollection):
            raise TypeError('val must be a SchemaCollection instance.')
        self.schema_collections[name] = val
