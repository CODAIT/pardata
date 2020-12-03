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


from enum import IntFlag
import hashlib
import os
import pathlib
import tarfile
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Union

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
        self._data_dir: pathlib.Path = pathlib.Path(os.path.abspath(data_dir))
        self._data: Optional[Dict[str, Any]] = None

        if not isinstance(mode, Dataset.InitializationMode):
            raise ValueError(f'{mode} not a valid mode')

        if mode & Dataset.InitializationMode.DOWNLOAD_ONLY:
            self.download()
        if mode & Dataset.InitializationMode.LOAD_ONLY:
            self.load()

    def download(self) -> None:
        """Downloads, extracts, and removes dataset archive.

        :raises FileExistsError: :attr:`Dataset._data_dir` (passed in via :meth:`.__init__()`) points to an
                                 existing file that is not a directory.
        :raises OSError: The SHA512 checksum of a downloaded dataset doesn't match the expected checksum.
        :raises tarfile.ReadError: The tar archive was unable to be read.
        """
        download_url = self._schema['download_url']
        download_file_name = pathlib.Path(os.path.basename(download_url))
        archive_fp = self._data_dir / download_file_name

        if not os.path.exists(self._data_dir):
            os.makedirs(self._data_dir)
        elif not os.path.isdir(self._data_dir):  # self._data_dir exists and is not a directory
            raise FileExistsError(f'"{self._data_dir}" exists and is not a directory.')

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
        """Check to see if dataset was downloaded.

        :return: Boolean indicating if the dataset's datadir has contents or not.
        """
        return self._data_dir.is_dir() and len(os.listdir(self._data_dir)) > 0


def handle_name_version_params(func: Callable) -> Callable:
    """Decorator for handling ``name`` and ``version`` parameters."""
    def wrapper_decorator(name: str,
                          version: Optional[str] = None,
                          *args: Union[bool, Iterable[str], None],
                          **kwargs: Union[bool, Iterable[str], None]) -> Union[None, Dict[str, Any], SchemaDict]:

        if not isinstance(name, str):
            raise TypeError('The name parameter must be supplied a str.')
        if version is not None and not isinstance(version, str):
            raise TypeError('The version parameter must be supplied a str.')
        all_datasets = list_all_datasets()
        if name not in all_datasets.keys():
            raise KeyError(f'Failed to load dataset because "{name}" is not a valid PyDAX dataset. '
                           'You can view all valid datasets and their versions by running the function '
                           'pydax.list_all_datasets().')
        if version is None:
            # Grab latest available version
            version = str(max(version_parser(v) for v in all_datasets[name]))
        elif version not in all_datasets[name]:
            raise ValueError(f'Failed to load dataset because "{version}" is not a valid PyDAX version for the dataset '
                             f'"{name}". You can view all valid datasets and their versions by running the function '
                             'pydax.list_all_datasets().')

        value = func(name=name, version=version, *args, **kwargs)
        return value
    return wrapper_decorator


@handle_name_version_params
def load_dataset(name: str, *,
                 version: Optional[str] = None,
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
    :raises TypeError: ``name`` or ``version`` are not strings.
    :return: Dictionary that holds all subdatasets.
    """

    schema = load_schemata().schemata['dataset_schema'] \
                            .export_schema('datasets', name, version)  # type: ignore [arg-type]

    data_dir = get_config().DATADIR / name / version  # type: ignore [operator]
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


@handle_name_version_params
def get_dataset_metadata(name: str, *,
                         version: Optional[str] = None,
                         human: bool = True) -> Optional[SchemaDict]:
    """Print in human-readable form a dataset's metadata or return a copy of its schema.

    :param name: Name of the dataset you want get the metadata of. You can get a list of these
        datasets by calling :func:`pydax.list_all_datasets`.
    :param version: Version of the dataset to load. Latest version is used by default. You can get a list of all
        available versions for a dataset by calling :func:`pydax.list_all_datasets`.
    :param human: Whether to print the metadata in human-readable form or to return a copy of the dataset's schema.
        Defaults to True.
    :return: A dictionary copy of the dataset's schema if ``human`` is set to False.
    """

    schema_manager = load_schemata()
    dataset_schema = schema_manager.schemata['dataset_schema'] \
                                   .export_schema('datasets', name, version)  # type: ignore [arg-type]
    license_schema = schema_manager.schemata['license_schema'].export_schema('licenses')

    if human:
        print(f'Dataset name: {dataset_schema["name"]}\n'
              f'Description: {dataset_schema["description"]}\n'
              f'Size: {dataset_schema["estimated_size"]}\n'
              f'Published date: {dataset_schema["published"]}\n'
              f'License: {license_schema[dataset_schema["license"]]["name"]}\n'
              f'Available subdatasets: {", ".join(dataset_schema["subdatasets"].keys())}'
              )
        return None

    else:
        return dataset_schema
