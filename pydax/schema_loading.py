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

"Parse and load the retrieved schema files."


from abc import ABC
from copy import deepcopy
from typing import Any, Dict, Union

import yaml

from pydax._schema_retrieval import retrieve_schema_file


class Schema(ABC):
    """Abstract class that provides functionality to load and export schemata.

    :param url_or_path: URL or path to a schema file
    """

    def __init__(self, url_or_path: Union[str, None] = None) -> None:
        """Constructor method.
        """
        if url_or_path is None:
            url_or_path = self.DEFAULT_SCHEMA_URL  # type: ignore [attr-defined]
        self._schema = self._load_retrieved_schema(retrieve_schema_file(url_or_path))

    def _load_retrieved_schema(self, schema: str) -> Dict[str, Any]:
        """Safely loads retrieved schema file.

        :param schema: Retrieved schema object
        :return: Nested dictionary representation of a schema
        """
        return yaml.safe_load(schema)

    def export_schema(self) -> Dict[str, Any]:
        """Returns a copy of a loaded schema. Should be used for debug purposes only.

        :return: Copy of schema
        """
        return deepcopy(self._schema)


class DatasetSchema(Schema):
    """Dataset schema class that inherits functionality from :class:`Schema`.

    :param url_or_path: URL or path to a schema file
    """

    DEFAULT_SCHEMA_URL = ('https://raw.github.ibm.com/gist/hongx/d368b6c26164c74eb6a70fb7680fdb9d/raw/'
                          'f661cf761a15b50b55f30a36e00979b9a56ad3fc/schema-datasets.yaml?'
                          'token=AABVD5VCPZBEEKTJKS7I4EK7THG4C')


class FormatSchema(Schema):
    """Format schema class that inherits functionality from :class:`Schema`.

    :param url_or_path: URL or path to a schema file
    """

    DEFAULT_SCHEMA_URL = ('https://raw.github.ibm.com/gist/hongx/d368b6c26164c74eb6a70fb7680fdb9d/raw/'
                          'f661cf761a15b50b55f30a36e00979b9a56ad3fc/schema-formats.yaml?'
                          'token=AABKAR6RRJPORUU45YFSEPS7TMO4U')


class LicenseSchema(Schema):
    """License schema class that inherits functionality from :class:`Schema`.

    :param url_or_path: URL or path to a schema file
    """

    DEFAULT_SCHEMA_URL = ('https://raw.github.ibm.com/gist/hongx/d368b6c26164c74eb6a70fb7680fdb9d/raw/'
                          'f661cf761a15b50b55f30a36e00979b9a56ad3fc/schema-licenses.yaml?'
                          'token=AABKAR65PLFA3RL67ESXLRS7TMPC4')


class SchemaManager():
    """Stores all loaded schemata in :attr:`schemata`.

    :param **kwargs: Schema name and schema instance key-value pairs
    """

    def __init__(self, **kwargs: Schema) -> None:
        """Constructor method
        """
        self.schemata: Dict[str, Schema] = {}
        for name, val in kwargs.items():
            self.add_schema(name, val)

    def add_schema(self, name: str, val: Schema) -> None:
        """Store schema instance in a dictionary.

        :param name: Schema name
        :param val: Schema instance
        """
        if not isinstance(val, Schema):
            raise TypeError('val must be a Schema instance.')
        self.schemata[name] = val


def load_schemata(*,
                  dataset_url: str = DatasetSchema.DEFAULT_SCHEMA_URL,
                  format_url: str = FormatSchema.DEFAULT_SCHEMA_URL,
                  license_url: str = LicenseSchema.DEFAULT_SCHEMA_URL) -> SchemaManager:
    """Helper function to load and provide all schemata.

    :param dataset_url: Dataset schema url, defaults to DatasetSchema.DEFAULT_SCHEMA_DATASETS_URL
    :param format_url: Format schema url, defaults to FormatSchema.DEFAULT_SCHEMA_FORMATS_URL
    :param license_url: License schema url, defaults to LicenseSchema.DEFAULT_SCHEMA_LICENSES_URL
    :return: A :class:`SchemaManager` object which holds the loaded schemata in :attr:`schemata`
    """
    return SchemaManager(dataset_schema=DatasetSchema(dataset_url),
                         format_schema=FormatSchema(format_url),
                         license_schema=LicenseSchema(license_url))
