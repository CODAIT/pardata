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

"Module for defining and modifying global configs"


import dataclasses
import os
import pathlib
from typing import Any

from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Global read-only configurations for PyDAX.
    """

    # Default schema URLs
    DEFAULT_DATASET_SCHEMA_URL: str = 'https://raw.githubusercontent.com/CODAIT/dax-schemata/master/datasets.yaml'
    DEFAULT_FORMAT_SCHEMA_URL: str = 'https://raw.githubusercontent.com/CODAIT/dax-schemata/master/formats.yaml'
    DEFAULT_LICENSE_SCHEMA_URL: str = 'https://raw.githubusercontent.com/CODAIT/dax-schemata/master/licenses.yaml'

    # DATADIR is the default dir where datasets files are downloaded/loaded to/from.
    DATADIR: pathlib.Path = pathlib.Path.home() / '.pydax' / 'data'

    def __post_init_post_parse__(self) -> None:
        "This is called by :meth:`.__init__()` after data type validation."
        # DATADIR should be absolute.
        # We use object.__setattr__ because we set frozen=True, same as what dataclasses does:
        # https://docs.python.org/3/library/dataclasses.html#frozen-instances
        object.__setattr__(self, 'DATADIR', pathlib.Path(os.path.abspath(self.DATADIR)))


def get_config() -> Config:
    """Function used to return global PyDAX configs.

    :return: Read-only global configs represented as a data class
    """
    return global_config  # type: ignore [name-defined]


def init(update_only: bool = True, **kwargs: Any) -> None:
    """
    (Re-)initialize the PyDAX library. This includes updating PyDAX global configs.

    :param update_only: If ``True``, only update in the global configs what config is specified. Otherwise, reset
        everything to default in global configs except those specified as keyword arguments.
    :param DEFAULT_DATASET_SCHEMA_URL: The default dataset schema file URL.
    :param DEFAULT_FORMAT_SCHEMA_URL: The default format schema file URL.
    :param DEFAULT_LICENSE_SCHEMA_URL: The default license schema file URL.
    :param DATADIR: Default dataset directory to download/load to/from. The path can be either absolute or relative to
        the current working directory, but will be converted to the absolute path immediately in this function.
        Defaults to: ~/.pydax/data
    """
    global global_config

    if update_only:
        # We don't use dataclasses.replace here because it is uncertain whether it would work well with
        # pydantic.dataclasses.
        prev = dataclasses.asdict(global_config)  # type: ignore [name-defined]
        prev.update(kwargs)
        global_config = Config(**prev)  # type: ignore [name-defined]
    else:
        global_config = Config(**kwargs)  # type: ignore [name-defined]


init(update_only=False)
