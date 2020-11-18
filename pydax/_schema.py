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


SchemaDict = Dict[str, Any]


class Schema(ABC):
    """Abstract class that provides functionality to load and export schemata.

    :param url_or_path: URL or path to a schema file.
    :raise AttributeError: DEFAULT_SCHEMA_URL is not overridden.
    """

    def __init__(self, url_or_path: Union[str, None] = None) -> None:
        """Constructor method.
        """
        if url_or_path is None:
            try:
                url_or_path = self.__class__.DEFAULT_SCHEMA_URL  # type: ignore [attr-defined]
            except AttributeError as e:
                raise AttributeError("DEFAULT_SCHEMA_URL is not defined. "
                                     'Have you forgotten to define this variable when inheriting "Schema"?\n'
                                     f"Caused by:\n{e}")
        self._schema: SchemaDict = self._load_retrieved_schema(retrieve_schema_file(url_or_path))

    def _load_retrieved_schema(self, schema: str) -> SchemaDict:
        """Safely loads retrieved schema file.

        :param schema: Retrieved schema object
        :return: Nested dictionary representation of a schema
        """
        return yaml.safe_load(schema)

    def export_schema(self, *keys: str) -> SchemaDict:
        """Returns a copy of a loaded schema. Should be used for debug purposes only.

        :param keys: The sequence of keys that leads to the portion of the schema to be exported.
        :return: Copy of the schema dictionary
        """
        schema: SchemaDict = self._schema
        for k in keys:
            schema = schema[k]
        return deepcopy(schema)


class DatasetSchema(Schema):
    """Dataset schema class that inherits functionality from :class:`Schema`.

    :param url_or_path: URL or path to a schema file
    """

    DEFAULT_SCHEMA_URL = 'https://ibm.box.com/shared/static/01oa3ue32lzcsd2znlbojs9ozdeftpb6.yaml'


class FormatSchema(Schema):
    """Format schema class that inherits functionality from :class:`Schema`.

    :param url_or_path: URL or path to a schema file
    """

    DEFAULT_SCHEMA_URL = 'https://ibm.box.com/shared/static/sv9hyf9vjdiareodbgo6kz5o8prxfm51.yaml'


class LicenseSchema(Schema):
    """License schema class that inherits functionality from :class:`Schema`.

    :param url_or_path: URL or path to a schema file
    """

    DEFAULT_SCHEMA_URL = ('https://ibm.box.com/shared/static/iy5xq7vk53dss5pgs0xvrfol9tfyd7ya.yaml')


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
