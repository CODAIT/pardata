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

"Loader base class."


from abc import ABC, abstractmethod
import os
from typing import Any, Dict, Union

from .. import typing as typing_
from .._schema import SchemaDict


class Loader(ABC):
    """Base class of all loaders.
    """

    @abstractmethod
    def load(self, path: Union[typing_.PathLike, Dict[str, str]], options: SchemaDict) -> Any:
        """Loads from a given path or a dict of path configurations. This must be overridden when inherited.

        :param path: The path or path configurations of the files to be loaded.
        :param options: Options passed to the loader.
        :return: The object representing the loaded file.
        """
        self.check_path(path)

    def check_path(self, path: Union[typing_.PathLike, Dict[str, str]]) -> None:
        """Check if the given path is a valid path to the file to be loaded. Raise an error if it is not.

        :param path: The path of the file to be loaded.
        :raises TypeError: ``path`` is not a path object.
        :return: No return unless the ``path`` is invalid, in which case see :class:`TypeError`.
        """
        if not isinstance(path, (str, os.PathLike)):
            # In Python 3.8, this can be done with isinstance(path, typing.get_args(typing_.PathLike))
            raise TypeError(f'Unsupported path type "{type(path)}".')
