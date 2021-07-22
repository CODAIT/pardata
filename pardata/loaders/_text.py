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

"Text file loaders."


import pathlib
from typing import cast, Dict, Union

from .. import typing as typing_
from ..schema import SchemaDict
from ._base import Loader


class PlainTextLoader(Loader):
    """Plain text to string loader.
    """

    def load(self, path: Union[typing_.PathLike, Dict[str, str]], options: SchemaDict) -> str:
        """The type hint says Dict, because this loader will be handling those situations in the future.

        :param path: The path to the plain text file.
        :param options:
               - ``encoding`` key specifies the encoding of the plain text.
        :raises TypeError: ``path`` is not a path object.
        :return: Data loaded into a ``str``.
        """

        super().load(path, options)

        encoding = options.get('encoding', 'utf-8')
        # We can remove usage of cast once Dict[str, str] handling is added
        path = cast(typing_.PathLike, path)
        return pathlib.Path(path).read_text(encoding=encoding)
