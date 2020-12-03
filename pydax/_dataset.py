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

"Download and load a dataset"


from contextlib import contextmanager
from enum import IntFlag
import functools
import hashlib
import json
import os
import pathlib
import tarfile
from typing import Any, Callable, Dict, IO, Iterable, Iterator, Optional, Tuple, Union, no_type_check

from packaging.version import parse as version_parser
import requests

from . import _typing
from ._config import get_config
from ._schema import load_schemata
from .schema import SchemaDict
from .loaders._format_loader_map import _load_data_files


def list_all_datasets() -> Dict[str, Tuple]:
    """Show all available pydax datasets and their versions.

    :return: Mapping of available datasets and their versions
    """

    dataset_schema = load_schemata().schemata['dataset_schema'].export_schema('datasets')
    return {
        outer_k: tuple(inner_k for inner_k, inner_v in outer_v.items())
        for outer_k, outer_v in dataset_schema.items()
    }


class Dataset:
    """Models a particular dataset version along with download & load functionality.

    :param schema: Schema dict of a particular dataset version
    :param data_dir: Directory to/from which the dataset should be downloaded/loaded from. The path can be either
        absolute or relative to the current working directory, but will be converted to the absolute path immediately
        upon initialization.
    :param mode: Mode with which to treat a dataset. Available options are:
        :attr:`Dataset.InitializationMode.LAZY`, :attr:`Dataset.InitializationMode.DOWNLOAD_ONLY`,
        :attr:`Dataset.InitializationMode.LOAD_ONLY`, and :attr:`Dataset.InitializationMode.DOWNLOAD_AND_LOAD`
    :raises ValueError: An invalid `mode` was specified for handling the dataset
    """

    class InitializationMode(IntFlag):
        """Enum class that acts as `mode` for :class:`Dataset`.
        """
        LAZY = 0
        DOWNLOAD_ONLY = 1
        LOAD_ONLY = 2
        DOWNLOAD_AND_LOAD = 3

    def __init__(self, schema: SchemaDict,
                 data_dir: _typing.PathLike,  *,
                 mode: InitializationMode = InitializationMode.LAZY) -> None:
        """Constructor method.
        """

        self._schema: SchemaDict = schema
        self._data_dir_: pathlib.Path = pathlib.Path(os.path.abspath(data_dir))
        self._data: Optional[Dict[str, Any]] = None

        if not isinstance(mode, Dataset.InitializationMode):
            raise ValueError(f'{mode} not a valid mode')

        if mode & Dataset.InitializationMode.DOWNLOAD_ONLY:
            self.download()
        if mode & Dataset.InitializationMode.LOAD_ONLY:
            self.load()

    @property
    def _data_dir(self) -> pathlib.Path:
        "Directory that stores datasets. Create it if not existing."
        if not self._data_dir_.exists():
            self._data_dir_.mkdir(parents=True)
        elif not self._data_dir_.is_dir():  # self._data_dir_ exists and is not a directory
            raise FileExistsError(f'"{self._data_dir_}" exists and is not a directory.')
        return self._data_dir_

    @property
    def _cache_dir(self) -> pathlib.Path:
        "Cache and metainfo directory used by this class. Create it if not existing."
        cache_dir = self._data_dir / '.pydax'
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True)
        elif not cache_dir.is_dir():  # cache_dir exists and is not a directory
            raise FileExistsError(f'"{cache_dir}" exists and is not a directory.')
        return cache_dir

    @property
    def _file_list_file(self) -> pathlib.Path:
        "Path to the file that stores the list of files in the downloaded dataset."
        return self._cache_dir / 'files.list'

    @contextmanager
    def _open_and_lock_file_list_file(self, **kwargs: Any) -> Iterator[IO]:
        """Open and lock the file that stores the list of files in the downloaded dataset.
        :param mode: Same as in :func:`open`.
        :return: A file object that points to the file that stores the list of files in the downloaded dataset.
        """
        # TODO: The lock part is to prevent the file being messed if someone runs multiple processes that use pydax
        # (e.g., some data scientist opens two notebooks.) This is to be implemented.
        with open(self._file_list_file, **kwargs) as f:
            yield f

    def download(self) -> None:
        """Downloads, extracts, and removes dataset archive.

        :raises FileExistsError: :attr:`Dataset._data_dir` (passed in via :meth:`.__init__()`) points to an
                                 existing file that is not a directory.
        :raises OSError: The SHA512 checksum of a downloaded dataset doesn't match the expected checksum.
        :raises tarfile.ReadError: The tar archive was unable to be read.
        """
        download_url = self._schema['download_url']
        download_file_name = pathlib.Path(os.path.basename(download_url))
        archive_fp = self._cache_dir / download_file_name

        response = requests.get(download_url, stream=True)
        archive_fp.write_bytes(response.content)

        computed_hash = hashlib.sha512(archive_fp.read_bytes()).hexdigest()
        actual_hash = self._schema['sha512sum']
        if not actual_hash == computed_hash:
            raise OSError(f'{archive_fp} has a SHA512 checksum of: ({computed_hash}) \
                            which is different from the expected SHA512 checksum of: ({actual_hash}) \
                            the file may by corrupted.')

        # Supports tar archives only for now
        try:
            tar = tarfile.open(archive_fp)
        except tarfile.ReadError as e:
            raise tarfile.ReadError(f'Failed to unarchive "{archive_fp}"\ncaused by:\n{e}')
        with tar:
            members = {}
            for member in tar.getmembers():
                members[member.name] = {'type': int(member.type)}
                if member.isreg():  # For regular files, we also save its size
                    members[member.name]['size'] = member.size
            with self._open_and_lock_file_list_file(mode='w') as f:
                # We do not specify 'utf-8' here to match the default encoding used by the OS, which also likely uses
                # this encoding for accessing the filesystem.
                json.dump(members, f, indent=2)
            tar.extractall(path=self._data_dir)

        os.remove(archive_fp)

    def load(self, subdatasets: Union[Iterable[str], None] = None) -> None:
        """Load data files to RAM. The loaded data objects can be retrieved via :attr:`data`.

        :param subdatasets: The subdatasets to load. None means all subdatasets.
        :raises FileNotFoundError: The dataset files are not found on the disk. Usually this is because
            :func:`~Dataset.download` has never been called.
        """
        if subdatasets is None:
            subdatasets = self._schema['subdatasets'].keys()

        self._data = {}
        for subdataset in subdatasets:
            subdataset_schema = self._schema['subdatasets'][subdataset]
            try:
                self._data[subdataset] = _load_data_files(fmt=subdataset_schema['format'],
                                                          path=self._data_dir / subdataset_schema['path'])
            except FileNotFoundError as e:
                raise FileNotFoundError(f'Failed to load subdataset "{subdataset}" because some files are not found. '
                                        f'Did you forget to call {self.__class__.__name__}.download()?\nCaused by:\n'
                                        f'{e}')

    @property
    def data(self) -> Dict[str, Any]:
        """Access loaded data objects."""
        if self._data is None:
            raise RuntimeError(f'Data has not been loaded yet. Call {self.__class__.__name__}.load() to load data.')
        # we don't copy here because it is too expensive and users may actually want to update the datasets and it
        # doesn't cause security issues as in the Schema class
        return self._data

    def is_downloaded(self) -> bool:
        """Check to see if dataset was downloaded. We determine this by comparing the extracted file tree with the file
        list :meth:`._file_list_file` (their existence, types, and sizes). In this way, if the extraction of the archive
        failed, this should return False and the user would not be misled. For performance reasons, we do not examine
        the content of the extracted files.

        :return: ``True`` if the dataset has been downloaded and ``False`` otherwise.
        """

        # The method to detect whether the dataset has been downloaded can certainly be improved by balancing how much
        # to examine and how much time it takes to do so, considering some heuristics such as the dataset size, the
        # number of files, etc. The method used here should be able to strike a good balance for most cases and should
        # be good enough for the first release.

        if not self._file_list_file.exists():
            # File not found, may not have finished downloading at all and we treat it as so. We can't control users'
            # own tweaking with the directory.
            return False
        with self._open_and_lock_file_list_file(mode='r') as file_list:
            for name, info in json.load(file_list).items():
                path = self._data_dir / name
                if not path.exists():
                    # At least one file in the file list is missing
                    return False
                if info['type'] == int(tarfile.REGTYPE):  # Regular file
                    if not path.is_file():
                        return False
                    if path.stat().st_size != info['size']:
                        return False
                elif info['type'] == int(tarfile.DIRTYPE):  # Directory type
                    if not path.is_dir():
                        return False
                elif info['type'] == int(tarfile.SYMTYPE):  # Symbolic link type
                    if not path.is_symlink():
                        return False
                else:
                    # We just let go any file types that we don't understand.
                    pass
        return True


@no_type_check
def _handle_name_param(func: Callable) -> Callable:
    """Decorator for handling ``name`` parameter.

    :raises TypeError: ``name`` is not a string.
    :raises KeyError: ``name`` is not a valid PyDAX dataset name.
    :return: Wrapped function that handles ``name`` parameter properly.
    """
    @functools.wraps(func)
    def name_wrapper(name: str, *args, **kwargs):

        if not isinstance(name, str):
            raise TypeError('The name parameter must be supplied a str.')
        all_datasets = list_all_datasets()
        if name not in all_datasets.keys():
            raise KeyError(f'"{name}" is not a valid PyDAX dataset. You can view all valid datasets and their versions '
                           'by running the function pydax.list_all_datasets().')
        return func(name, *args, **kwargs)
    return name_wrapper


@no_type_check
def _handle_version_param(func: Callable) -> Callable:
    """Decorator for handling ``version`` parameter. Must still be supplied a dataset ``name``.

    :raises TypeError: ``version`` is not a string.
    :raises KeyError: ``version`` is not a valid PyDAX version of ``name``.
    :return: Wrapped function that handles ``version`` parameter properly.
    """
    @functools.wraps(func)
    def version_wrapper(name: str, version: str = 'latest', *args, **kwargs):

        if not isinstance(version, str):
            raise TypeError('The version parameter must be supplied a str.')
        all_datasets = list_all_datasets()
        if version == 'latest':
            # Grab latest available version
            version = str(max(version_parser(v) for v in all_datasets[name]))
        elif version not in all_datasets[name]:
            raise KeyError(f'"{version}" is not a valid PyDAX version for the dataset "{name}". You can view all '
                           'valid datasets and their versions by running the function pydax.list_all_datasets().')
        return func(name=name, version=version, *args, **kwargs)
    return version_wrapper


@_handle_name_param
@_handle_version_param
def load_dataset(name: str, *,
                 version: str = 'latest',
                 download: bool = True,
                 subdatasets: Union[Iterable[str], None] = None) -> Dict[str, Any]:
    """High level function that wraps :class:`Dataset` class's load and download functionality. Downloads to and loads
    from directory: `DATADIR/name/version` where ``DATADIR`` is in ``pydax.get_config().DATADIR``. ``DATADIR`` can
    be changed by calling :func:`pydax.init()`.

    :param name: Name of the dataset you want to load from PyDAX's available datasets. You can get a list of these
        datasets by calling :func:`pydax.list_all_datasets`.
    :param version: Version of the dataset to load. Latest version is used by default. You can get a list of all
        available versions for a dataset by calling :func:`pydax.list_all_datasets`.
    :param download: Whether or not the dataset should be downloaded before loading.
    :param subdatasets: An iterable containing the subdatasets to load. ``None`` means all subdatasets.
    :raises FileNotFoundError: The dataset files were not previously downloaded or can't be found, and ``download`` is
        False.
    :return: Dictionary that holds all subdatasets.
    """

    schema = load_schemata().schemata['dataset_schema'].export_schema('datasets', name, version)

    data_dir = get_config().DATADIR / name / version
    dataset = Dataset(schema=schema, data_dir=data_dir, mode=Dataset.InitializationMode.LAZY)
    if download and not dataset.is_downloaded():
        dataset.download()
    try:
        dataset.load(subdatasets=subdatasets)
    except FileNotFoundError as e:
        raise FileNotFoundError('Failed to load the dataset because some files are not found. '
                                'Did you forget to download the dataset (by specifying `download=True`)?'
                                f'\nCaused by:\n{e}')

    return dataset.data


@_handle_name_param
@_handle_version_param
def get_dataset_metadata(name: str, *,
                         version: str = 'latest',
                         human: bool = True) -> Union[str, SchemaDict]:
    """Return a dataset's metadata either in human-readable form or as a copy of its schema.

    :param name: Name of the dataset you want get the metadata of. You can get a list of these
        datasets by calling :func:`pydax.list_all_datasets`.
    :param version: Version of the dataset to load. Latest version is used by default. You can get a list of all
        available versions for a dataset by calling :func:`pydax.list_all_datasets`.
    :param human: Whether to return the metadata as a string in human-readable form or to return a copy of the
        dataset's schema. Defaults to True.
    :return: Return a dataset's metadata either as a string or as a schema dictionary.
    """

    schema_manager = load_schemata()
    dataset_schema = schema_manager.schemata['dataset_schema'].export_schema('datasets', name, version)
    license_schema = schema_manager.schemata['license_schema'].export_schema('licenses')
    if human:
        return (f'Dataset name: {dataset_schema["name"]}\n'
                f'Description: {dataset_schema["description"]}\n'
                f'Size: {dataset_schema["estimated_size"]}\n'
                f'Published date: {dataset_schema["published"]}\n'
                f'License: {license_schema[dataset_schema["license"]]["name"]}\n'
                f'Available subdatasets: {", ".join(dataset_schema["subdatasets"].keys())}')
    else:
        return dataset_schema
