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

from typing import Any, Dict, Optional, Union


from ._base import Loader
from .text import PlainTextLoader


class FormatLoaderMap:
    """Manage a map between formats and loaders. This is usually used to determine which loader should be used for a
    given format.

    :param m: A dict that maps formats to loaders.

    """

    def __init__(self, m: Optional[Dict[str, Loader]] = None) -> None:
        "Constructor method."
        self._map: Dict[str, Loader] = {}
        if m is not None:
            for fmt, loader in m.items():
                self.register_loader(fmt, loader)

    def register_loader(self, fmt: str, loader: Loader) -> None:
        """Register a loader. If the format exists in the table, update it.

        :param fmt: The format.
        :param loader: The corresponding loader.
        """
        if not isinstance(loader, Loader):
            raise TypeError(f'loader "{loader}" must be a Loader instance.')
        # We may support an overriding check in the future
        self._map[fmt] = loader

    def __getitem__(self, fmt: str) -> Loader:
        """Get the loader of a given format.

        :param fmt: The format.
        """
        return self._map[fmt]

    def __contains__(self, fmt: str) -> bool:
        """Whether a format is covered by this format loader map.

        :param fmt: Name of the format.
        """
        return fmt in self._map


_default_format_loader_map: FormatLoaderMap = FormatLoaderMap({'txt': PlainTextLoader()})


def _load_data_files(fmt: str, path: Union[str, Dict[str, str]], *, format_loader_map: FormatLoaderMap = None) -> Any:
    """Load data files.

    :param fmt: The format.
    :param path: Path to the file(s).
    :param format_loader_map: The format loader map to use.
    :return: Loaded data file objects.
    """

    # We only support path as a plain path for now, but we will extend path to support regex and other types.

    if format_loader_map is None:
        format_loader_map = _default_format_loader_map

    if fmt not in format_loader_map:
        raise RuntimeError(f'The format loader map does not specify a loader for format "{fmt}".')

    return format_loader_map[fmt].load(path)
