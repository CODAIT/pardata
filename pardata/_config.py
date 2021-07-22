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

"Module for defining and modifying global configs."


import os
import pathlib
from typing import Union

from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Global read-only configurations for ParData.
    """

    # Default schema URLs
    # TODO: The types below should be typing_.PathLike. However, pydantic does not play well with os.PathLike for
    # validation. Will have to fix it in another occasion.
    DATASET_SCHEMA_FILE_URL: Union[str, pathlib.Path] = \
        'https://raw.githubusercontent.com/CODAIT/dax-schemata/master/datasets.yaml'
    FORMAT_SCHEMA_FILE_URL: Union[str, pathlib.Path] = \
        'https://raw.githubusercontent.com/CODAIT/dax-schemata/master/formats.yaml'
    LICENSE_SCHEMA_FILE_URL: Union[str, pathlib.Path] = \
        'https://raw.githubusercontent.com/CODAIT/dax-schemata/master/licenses.yaml'

    # DATADIR is the default dir where datasets files are downloaded/loaded to/from.
    DATADIR: pathlib.Path = pathlib.Path.home() / '.pardata' / 'data'

    def __post_init_post_parse__(self) -> None:
        "This is called by :meth:`.__init__()` after data type validation."
        # DATADIR should be absolute.
        # We use object.__setattr__ because we set frozen=True, same as what dataclasses does:
        # https://docs.python.org/3/library/dataclasses.html#frozen-instances
        object.__setattr__(self, 'DATADIR', pathlib.Path(os.path.abspath(self.DATADIR)))
