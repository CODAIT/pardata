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

"Download and load a dataset"


from enum import IntFlag
import hashlib
import json
import os
import pathlib
import shutil
import tarfile
from typing import Any, Callable, Dict, Iterable, Optional

import requests

from . import _typing
from .loaders import FormatLoaderMap
from .loaders._format_loader_map import load_data_files
from .schema import SchemaDict
from ._lock import DirectoryLock


class Dataset:
    """Models a particular dataset version along with download & load functionality.

    :param schema: Schema dict of a particular dataset version.
    :param data_dir: Directory to/from which the dataset should be downloaded/loaded from. The path can be either
        absolute or relative to the current working directory, but will be converted to the absolute path immediately
        upon initialization.
    :param mode: Mode with which to treat a dataset. Available options are:
        :attr:`Dataset.InitializationMode.LAZY`, :attr:`Dataset.InitializationMode.DOWNLOAD_ONLY`,
        :attr:`Dataset.InitializationMode.LOAD_ONLY`, and :attr:`Dataset.InitializationMode.DOWNLOAD_AND_LOAD`.
    :raises ValueError: An invalid `mode` was specified for handling the dataset.
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
        # Put directory lock under self._pydax_dir. We use self._pydax_dir_ instead of self._pydax_dir because we don't
        # want to have the directory created in lazy mode upon construction of a Dataset object.
        self._lock: DirectoryLock = DirectoryLock(self._pydax_dir_)

        if not isinstance(mode, Dataset.InitializationMode):
            raise ValueError(f'{mode} not a valid mode')

        if mode & Dataset.InitializationMode.DOWNLOAD_ONLY:
            self.download()
        if mode & Dataset.InitializationMode.LOAD_ONLY:
            self.load()

    @property
    def _data_dir(self) -> pathlib.Path:
        "Directory that stores datasets. Create it if it does not exist."
        if not self._data_dir_.exists():
            self._data_dir_.mkdir(parents=True)
        elif not self._data_dir_.is_dir():  # self._data_dir_ exists and is not a directory
            raise NotADirectoryError(f'"{self._data_dir_}" exists and is not a directory.')
        return self._data_dir_

    @property
    def _pydax_dir_(self) -> pathlib.Path:
        "Cache, metainfo, etc. directory used by this class."
        return self._data_dir_ / '.pydax.dataset'

    @property
    def _pydax_dir(self) -> pathlib.Path:
        "Same as :attr:`_pydax_dir`, but create it if it does not exist."
        if not self._pydax_dir_.exists():
            self._pydax_dir_.mkdir(parents=True)
        elif not self._pydax_dir_.is_dir():  # pydax_dir exists and is not a directory
            raise NotADirectoryError(f'"{self._pydax_dir_}" exists and is not a directory.')
        return self._pydax_dir_

    @property
    def _file_list_file(self) -> pathlib.Path:
        "Path to the file that stores the list of files in the downloaded dataset."
        return self._pydax_dir / 'files.list'

    def download(self) -> None:
        """Downloads, extracts, and removes dataset archive. It adds a directory write lock during execution.

        :raises NotADirectory: :attr:`Dataset._data_dir` (passed in via :meth:`.__init__()`) points to an
                               existing file that is not a directory.
        :raises OSError: The SHA512 checksum of a downloaded dataset doesn't match the expected checksum.
        :raises tarfile.ReadError: The tar archive was unable to be read.
        :raises exceptions.DirectoryLockAcquisitionError: Failed to acquire the directory lock.
        """
        download_url = self._schema['download_url']
        download_file_name = pathlib.Path(os.path.basename(download_url))

        with self._lock.locking_with_exception(write=True):
            archive_fp = self._pydax_dir / download_file_name
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
                with open(self._file_list_file, mode='w') as f:
                    # We do not specify 'utf-8' here to match the default encoding used by the OS, which also likely
                    # uses this encoding for accessing the filesystem.
                    json.dump(members, f, indent=2)
                tar.extractall(path=self._data_dir)

            os.remove(archive_fp)

    def load(self,
             subdatasets: Optional[Iterable[str]] = None,
             format_loader_map: Optional[FormatLoaderMap] = None) -> None:
        """Load data files to RAM. It adds a directory read lock during execution.

        :param subdatasets: The subdatasets to load. ``None`` means all subdatasets.
        :param format_loader_map: The :class:`FormatLoaderMap` object that determines which loader to use.
        :raises FileNotFoundError: The dataset files are not found on the disk. Usually this is because
            :func:`~Dataset.download` has never been called.
        :raises exceptions.DirectoryLockAcquisitionError: Failed to acquire the directory lock.
        :return: Loaded data objects.
        """
        if subdatasets is None:
            subdatasets = self._schema['subdatasets'].keys()

        with self._lock.locking_with_exception(write=False):
            self._data = {}
            for subdataset in subdatasets:
                subdataset_schema = self._schema['subdatasets'][subdataset]
                try:
                    self._data[subdataset] = load_data_files(fmt=subdataset_schema['format'],
                                                             path=self._data_dir / subdataset_schema['path'],
                                                             format_loader_map=format_loader_map)
                except FileNotFoundError as e:
                    raise FileNotFoundError(
                        f'Failed to load subdataset "{subdataset}" because some files are not found. '
                        f'Did you forget to call {self.__class__.__name__}.download()?\nCaused by:\n{e}')

        return self.data

    def delete(self, *, force: bool = False) -> None:
        """Clear the data directory. It adds a directory write lock before deletion during execution if the data
        directory exists.

        :param force: If True, delete the directory even if directory locks are present.
        :raises exceptions.DirectoryLockAcquisitionError: Failed to acquire the directory lock.
        """

        if self._data_dir_.exists():
            if force:
                lock_func: Callable = self._lock.locking
            else:
                lock_func = self._lock.locking_with_exception
            with lock_func(write=True):
                shutil.rmtree(self._data_dir_)

    @property
    def data(self) -> Dict[str, Any]:
        """Access loaded data objects.

        :raises RuntimeError: The dataset files were not downloaded and/or not loaded.
        :return: Loaded data objects.
        """
        if self._data is None:
            raise RuntimeError(f'Data has not been downloaded and/or loaded yet. Call '
                               f'{self.__class__.__name__}.download() to download data, call '
                               f'{self.__class__.__name__}.load() to load data.')
        # We don't copy here because it is too expensive and users may actually want to update the datasets and it
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
        with open(self._file_list_file, mode='r') as file_list:
            for name, info in json.load(file_list).items():
                path = self._data_dir / name
                if not path.exists():
                    # At least one file in the file list is missing
                    return False
                # We don't have pathlib type code that matches tarfile type code. We instead do an incomplete list of
                # type comparison. We don't do uncommon types such as FIFO, character device, etc. here.
                if info['type'] == int(tarfile.REGTYPE):  # Regular file
                    if not path.is_file():
                        return False
                    if path.stat().st_size != info['size']:
                        return False
                elif info['type'] == int(tarfile.DIRTYPE) and not path.is_dir():  # Directory type
                    return False
                elif info['type'] == int(tarfile.SYMTYPE) and not path.is_symlink():  # Symbolic link type
                    return False
                else:
                    # We just let go any file types that we don't understand.
                    pass
        return True
