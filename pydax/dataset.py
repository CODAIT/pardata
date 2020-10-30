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
from typing import Dict, Tuple, Union

import requests

from pydax.schema_loading import load_schemata


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

    def __init__(self, schema: Dict, data_dir: Union[os.PathLike, str], *,
                 mode: InitializationMode = InitializationMode.LAZY) -> None:
        """Constructor method.
        """

        self.schema = schema
        self.data_dir: pathlib.Path = pathlib.Path(data_dir)

        if not isinstance(mode, Dataset.InitializationMode):
            raise ValueError(f'{mode} not a valid mode')

        if mode & Dataset.InitializationMode.DOWNLOAD_ONLY:
            self.download()
        if mode & Dataset.InitializationMode.LOAD_ONLY:
            pass

    def download(self) -> None:
        """Downloads, extracts, and removes dataset archive.

        :raises IOError: The SHA256 checksum of a downloaded dataset doesn't match the expected checksum
        :raises tarfile.ReadError: The tar archive was unable to be read
        """
        download_url = self.schema['download_url']
        download_file_name = pathlib.Path(os.path.basename(download_url))
        archive_fp = self.data_dir / download_file_name

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        response = requests.get(download_url, stream=True)
        archive_fp.write_bytes(response.content)

        computed_hash = hashlib.sha512(archive_fp.read_bytes()).hexdigest()
        actual_hash = self.schema['sha512sum']
        if not actual_hash == computed_hash:
            raise IOError(f'{archive_fp} has a SHA256 checksum of: ({computed_hash}) \
                            which is different from the expected SHA256 checksum of: ({actual_hash}) \
                            the file may by corrupted.')

        # Supports tar archives only for now
        try:
            tar = tarfile.open(archive_fp)
        except tarfile.ReadError as e:
            raise tarfile.ReadError(f'Failed to unarchive "{archive_fp}"\ncaused by:\n{e}')
        with tar:
            tar.extractall(path=self.data_dir)

        os.remove(archive_fp)
