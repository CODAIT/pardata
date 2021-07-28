#
# Copyright 2020--2021 IBM Corp. All Rights Reserved.
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

"Format to loader map."


from pathlib import Path
import re
from typing import Any, Dict, Mapping, Optional, Union

from .._schema import SchemaDict
from .._typing import PathLike

from ._base import Loader
from .audio import WaveLoader
from .image import PillowLoader
from .text import PlainTextLoader
from .table import CSVPandasLoader


class FormatLoaderMap:
    """Manage a map between formats and loaders. This is usually used to determine which loader should be used for a
    given format.

    :param m: A dict that maps formats to loaders.
    """

    def __init__(self, m: Optional[Mapping[str, Loader]] = None) -> None:
        """Constructor method.
        """
        self._map: Dict[str, Loader] = {}
        if m is not None:
            for fmt, loader in m.items():
                self.register_loader(fmt, loader)

    def register_loader(self, fmt: str, loader: Loader) -> None:
        """Register a loader. If the format exists in the table, update it.

        :param fmt: The format.
        :param loader: The corresponding loader.
        :raise TypeError: ``loader`` is not a :class:`Loader` object.
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


_default_format_loader_map: FormatLoaderMap = FormatLoaderMap({
    'text/plain': PlainTextLoader(),
    'table/csv': CSVPandasLoader(),
    'image/jpeg': PillowLoader(),
    'image/png': PillowLoader(),
    'audio/wav': WaveLoader(),
})


def load_data_files(fmt: Union[str, SchemaDict], data_dir: PathLike, path: Union[str, SchemaDict], *,
                    format_loader_map: FormatLoaderMap = None) -> Any:
    """Load data files.

    :param fmt: The format.
    :param data_dir: The path to the directory that holds the data files.
    :param path: If it is a :class:`str`, it is the path to the file. If it is a :class:`dict`, it consists of two keys:
        ``type`` and ``value``. If ``type`` is ``"regex"``, ``value`` is the regular expression of the paths of the
        files.
    :param format_loader_map: The format loader map to use.
    :raises TypeError: ``fmt`` or ``path`` is neither a string nor a :class:`SchemaDict`.
    :raises ValueError: If ``path`` is a :class:`SchemaDict`, but ``path[type]`` is not ``"regex"``.
    :return: Loaded data file objects.
    """

    # We only support path as a plain path for now, but we will extend path to support regex and other types.

    if format_loader_map is None:
        format_loader_map = _default_format_loader_map

    if isinstance(fmt, str):
        fmt_id: str = fmt
        fmt_options: SchemaDict = {}
    elif isinstance(fmt, Dict):
        # In Python 3.8+, this can be done with isinstance(fmt, typing.get_args(SchemaDict))
        fmt_id = fmt['id']
        fmt_options = fmt.get('options', {})
    else:
        raise TypeError(f'Parameter "fmt" must be a string or a dict, but it is of type "{type(fmt)}".')

    if fmt_id not in format_loader_map:
        raise RuntimeError(f'The format loader map does not specify a loader for format "{fmt_id}".')

    data_dir = Path(data_dir)
    loader = format_loader_map[fmt_id]
    if isinstance(path, str):
        return loader.load(data_dir / path, fmt_options)
    elif isinstance(path, Dict):
        # In Python 3.8+, this can be done with isinstance(fmt, typing.get_args(SchemaDict))
        path_type = path['type']

        if path_type == 'regex':
            loaded_data = {}
            path_value = path['value']
            # We match under the POSIX path scheme. Be careful to not escape the regex of path_value only
            path_pattern = re.compile(re.escape(data_dir.as_posix() + '/') + path_value.replace('/', r'\/'))
            for f in data_dir.rglob('*'):
                if path_pattern.fullmatch(f.as_posix()):
                    loaded_data[f.relative_to(data_dir).as_posix()] = loader.load(data_dir / f, fmt_options)
            return loaded_data
        else:
            raise ValueError(f'Unknown type of path "{path_type}".')
    else:
        raise TypeError(f'Unsupported type of the "path" parameter: {type(path)}.')
