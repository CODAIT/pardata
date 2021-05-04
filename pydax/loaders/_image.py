#
# Copyright 2021 IBM Corp. All Rights Reserved.
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

"Image file loaders."


from typing import cast, Dict, Union

from PIL import Image  # type: ignore[import]

from .. import typing as typing_
from ..schema import SchemaDict
from ._base import Loader


class PillowLoader(Loader):
    """Image file to :class:`PIL.Image` object loader.
    """

    def load(self, path: Union[typing_.PathLike, Dict[str, str]], options: SchemaDict) -> Image:
        """The type hint says Dict, because this loader will be handling those situations in the future.

        :param path: The path to the image file.
        :param options:
               - ``encoding`` key specifies the encoding of the plain text.
        :raises TypeError: ``path`` is not a path object.
        :return: Data loaded into a :class:`PIL.Image` object.
        """

        super().load(path, options)

        # We can remove usage of cast once Dict[str, str] handling is added
        path = cast(typing_.PathLike, path)
        return Image.open(path)
