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
from typing import Dict, Iterable, Optional, Tuple, Union

import requests

from .schema import load_schemata, SchemaDict
from .loaders._format_loader_map import _load_data_files
from . import _typing


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
    :param data_dir: Directory to/from which the dataset should be downloaded/loaded from
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

    def __init__(self, schema: SchemaDict, data_dir: _typing.PathLike, *,
                 mode: InitializationMode = InitializationMode.LAZY) -> None:
        """Constructor method.
        """

        self._schema: SchemaDict = schema
        self._data_dir: pathlib.Path = pathlib.Path(data_dir)
        self._data: Optional[SchemaDict] = None

        if not isinstance(mode, Dataset.InitializationMode):
            raise ValueError(f'{mode} not a valid mode')

        if mode & Dataset.InitializationMode.DOWNLOAD_ONLY:
            self.download()
        if mode & Dataset.InitializationMode.LOAD_ONLY:
            self.load()

    def download(self) -> None:
        """Downloads, extracts, and removes dataset archive.

        :raises OSError: The SHA512 checksum of a downloaded dataset doesn't match the expected checksum.
        :raises tarfile.ReadError: The tar archive was unable to be read.
        """
        download_url = self._schema['download_url']
        download_file_name = pathlib.Path(os.path.basename(download_url))
        archive_fp = self._data_dir / download_file_name

        if not os.path.exists(self._data_dir):
            os.makedirs(self._data_dir)

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
    def data(self) -> SchemaDict:
        """Access loaded data objects."""
        if self._data is None:
            raise RuntimeError(f'Data has not been loaded yet. Call {self.__class__.__name__}.load() to load data.')
        # we don't copy here because it is too expensive and users may actually want to update the datasets and it
        # doesn't cause security issues as in the Schema class
        return self._data
