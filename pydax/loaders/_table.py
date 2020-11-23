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

"Tabular data loaders."

import os

from typing import Dict, Optional, Union

import pandas as pd  # type: ignore

from .. import _typing
from ..schema import SchemaDict

from ._base import Loader


class CSVPandasLoader(Loader):

    def load(self, path: Union[_typing.PathLike, Dict[str, str]], options: Optional[SchemaDict]) -> str:
        """The type hint says Dict, because this loader will be handling those situations in the future, perhaps via a
        ``IteratingLoader`` class.

        :param path: The path to the CSV file.
        :param options:
               - ``columns`` key specifies the datatype of each column. If unspecified, then it is default.
               - ``encoding`` key specifies the encoding of the CSV file. Defaults to UTF-8.
        :raises TypeError: ``path`` is not a path object.
        """

        if not isinstance(path, (str, os.PathLike)):
            # In Python 3.8, this can be done with isinstance(path, typing.get_args(_typing.PathLike))
            raise TypeError(f'Unsupported path type "{type(path)}".')

        if options is None:
            options = {}

        parse_dates = []
        for column, type_ in options.get('columns', {}).items():
            # TODO: This is very simple right now. Need consider more situations
            if type_ == 'date':
                # pandas has this unusual handling of date datatype. Instead of specifying as a data type of a column,
                # we have to pass in `parse_dates`.
                parse_dates.append(column)

        return pd.read_csv(path, parse_dates=parse_dates, encoding=options.get('encoding', 'utf-8'))
