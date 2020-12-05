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
from typing import Any, Dict, Optional, Union

import yaml

from ._config import get_config
from . import _typing
from ._schema_retrieval import retrieve_schema_file


SchemaDict = Dict[str, Any]


class Schema(ABC):
    """Abstract class that provides functionality to load and export schemata.

    :param url_or_path: URL or path to a schema file.
    """

    def __init__(self, url_or_path: Union[_typing.PathLike, str]) -> None:
        """Constructor method.
        """
        self._schema: SchemaDict = self._load_retrieved_schema(retrieve_schema_file(url_or_path))

        # The URL or path from which the schema was retrieved
        self._retrieved_url_or_path: Union[_typing.PathLike, str] = url_or_path

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

    @property
    def retrieved_url_or_path(self) -> Union[_typing.PathLike, str]:
        "The URL or path from which the schema was retrieved."
        return self._retrieved_url_or_path


class DatasetSchema(Schema):
    """Dataset schema class that inherits functionality from :class:`Schema`.
    """

    # We have this class here because we reserve the potential to put specific dataset schema code here
    pass


class FormatSchema(Schema):
    """Format schema class that inherits functionality from :class:`Schema`.
    """

    # We have this class here because we reserve the potential to put specific format schema code here
    pass


class LicenseSchema(Schema):
    """License schema class that inherits functionality from :class:`Schema`.
    """

    # We have this class here because we reserve the potential to put specific license schema code here
    pass


class SchemaManager():
    """Stores all loaded schemata in :attr:`schemata`.

    :param kwargs: Schema name and schema instance key-value pairs
    """

    def __init__(self, **kwargs: Schema) -> None:
        """Constructor method
        """
        self.schemata: Dict[str, Schema] = {}
        for name, val in kwargs.items():
            self.add_schema(name, val)

    def add_schema(self, name: str, val: Schema) -> None:
        """Store schema instance in a dictionary. If a schema with the same name as ``name`` is already stored, it is
        overridden.

        :param name: Schema name
        :param val: Schema instance
        """
        if not isinstance(val, Schema):
            raise TypeError('val must be a Schema instance.')
        self.schemata[name] = val


# The SchemaManager object that is managed by high-level functions
_schemata: Optional[SchemaManager] = None


def load_schemata(*, force_reload: bool = False) -> None:
    """Loads a :class:`SchemaManager` object that stores all schemata. To export the loaded :class:`SchemaManager`
    object, please use :func:`.export_schemata`.

    :param force_reload: If ``True``, force reloading even if the provided URLs by :func:`pydax.init` are the same as
         provided last time. Otherwise, only those that are different from previous given ones are reloaded.
    """
    urls = {
        'datasets': get_config().DATASET_SCHEMA_URL,
        'formats': get_config().FORMAT_SCHEMA_URL,
        'licenses': get_config().LICENSE_SCHEMA_URL
    }

    global _schemata
    if force_reload or _schemata is None:  # Force reload or clean slate, create a new SchemaManager object
        _schemata = SchemaManager(**{name: Schema(url) for name, url in urls.items()})
    else:
        for name, schema in _schemata.schemata.items():
            if schema.retrieved_url_or_path != urls[name]:
                _schemata.add_schema(name, Schema(urls[name]))


def get_schemata() -> SchemaManager:
    """Return the :class:`SchemaManager` object managed by high-level functions. If it is not created, create it. This
    function is used by high-level APIs but it should not be a high-level function itself. It should only be used
    internally because users should not have this easy access to modify the managed :class`SchemaManager` object."""

    global _schemata

    if _schemata is None:
        load_schemata()

    # The return value is guranteed to be SchemaManager instead of Optional[SchemaManager] after load_schemata
    return _schemata  # type: ignore [return-value]


def export_schemata() -> SchemaManager:
    "Return a copy of the ``SchemaManager`` object managed by high-level functions."

    return deepcopy(get_schemata())
