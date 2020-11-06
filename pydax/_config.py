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


from dataclasses import dataclass
import pathlib

from . import _typing


@dataclass(frozen=True)
class Config:
    """Global read-only configurations for PyDAX.
    """
    # DATADIR is the default dir where datasets files are downloaded/loaded to/from.
    DATADIR: _typing.PathLike = pathlib.Path.home() / '.pydax' / 'data'


def get_config() -> Config:
    """Function used to return global PyDAX configs.

    :return: Read-only global configs represented as a data class
    """
    return global_config  # type: ignore [name-defined]


def init(**kwargs: _typing.PathLike) -> None:
    """
    (Re-)initialize the PyDAX library. This includes updating PyDAX global configs.

    :param DATADIR: Default dataset directory to download/load to/from. Defaults to: ~/.pydax/data
    """
    global global_config
    global_config = Config(**kwargs)  # type: ignore [name-defined]


init()
