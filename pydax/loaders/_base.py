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

from abc import ABC, abstractmethod

from typing import Any, Dict, Union

from .. import _typing


class Loader(ABC):
    "Base class of all loaders."

    @abstractmethod
    def load(self, path: Union[_typing.PathLike, Dict[str, str]]) -> Any:
        """Loads from a give path or a dict of path configurations. This should must overridden when inherited.

        :param path: The path or path configurations of the files to be loaded.
        :return: The object representing the loaded file.
        """
        pass
