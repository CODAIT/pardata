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

import dataclasses
import pathlib
import re
from urllib.parse import urlparse

import pytest
from pydantic import ValidationError
import requests.exceptions

from pydax import get_config, init
from pydax._config import Config
from pydax.dataset import Dataset
from pydax._schema_retrieval import retrieve_schema_file


def test_default_data_dir():
    "Test default data dir."

    pydax_data_home = pathlib.Path.home() / '.pydax' / 'data'
    assert get_config().DATADIR == pydax_data_home
    assert isinstance(get_config().DATADIR, pathlib.Path)


def test_custom_data_dir(tmp_path, wikitext103_schema):
    "Test to make sure Dataset constructor uses new global data dir if one was supplied earlier to pydax.init."

    init(DATADIR=tmp_path)
    assert get_config().DATADIR == tmp_path
    assert isinstance(get_config().DATADIR, pathlib.Path)
    wikitext = Dataset(wikitext103_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.LAZY)
    assert wikitext._data_dir == tmp_path
    assert isinstance(wikitext._data_dir, pathlib.Path)


def test_custom_relative_data_dir(chdir_tmp_path, tmp_sub_dir, tmp_relative_sub_dir):
    "Test using a custom relative data directory."

    init(DATADIR=tmp_relative_sub_dir)
    assert get_config().DATADIR == tmp_sub_dir
    assert get_config().DATADIR.is_absolute()


def test_custom_symlink_data_dir(tmp_symlink_dir):
    "Test using a custom symlink data directory. The symlink should not be resolved."

    init(DATADIR=tmp_symlink_dir)
    assert get_config().DATADIR == tmp_symlink_dir


def test_non_path_data_dir():
    "Test exception when a nonpath is passed as DATADIR."

    with pytest.raises(ValidationError) as e:
        init(DATADIR=10)

    assert re.search(r"1 validation error for Config\s+DATADIR\s+value is not a valid path \(type=type_error.path\)",
                     str(e.value))


def test_custom_configs():
    "Test custom configs."

    init(update_only=False)  # set back everything to default
    assert dataclasses.asdict(get_config()) == dataclasses.asdict(Config())

    new_urls = {
        'DATASET_SCHEMA_URL': 'some/local/file',
        'FORMAT_SCHEMA_URL': 'file://c:/some/other/local/file',
        'LICENSE_SCHEMA_URL': 'http://some/remote/file'
    }
    init(update_only=True, **new_urls)

    for url, val in new_urls.items():
        assert getattr(get_config(), url) == val
    assert get_config().DATADIR == Config.DATADIR


def test_default_schema_url_https():
    "Test the default schema URLs are https-schemed."

    assert urlparse(Config.DATASET_SCHEMA_URL).scheme == 'https'
    assert urlparse(Config.FORMAT_SCHEMA_URL).scheme == 'https'
    assert urlparse(Config.LICENSE_SCHEMA_URL).scheme == 'https'


@pytest.mark.xfail(reason="default remote might be down but it's not this library's issue",
                   raises=requests.exceptions.ConnectionError)
def test_default_schema_url_content():
    """Test the content of the remote URLs a bit. We only assert them not being None here just in case the server
    returns zero-length files."""

    init(update_only=False)

    # We only assert that we have retrieved some non-empty files in this test. This is because we want to decouple
    # the maintenance of schema files in production with the library development. These files likely would change
    # more regularly than the library. For this reason, we also verify the default schema URLs are also valid https
    # links in ``test_default_schema_url_https``.

    # This test is in `test_config.py` not in `test_schema_retrieval.py` because this test is more about the content
    # of the default schema URLs than the retrieving functionality.
    assert len(retrieve_schema_file(Config.DATASET_SCHEMA_URL)) > 0
    assert len(retrieve_schema_file(Config.FORMAT_SCHEMA_URL)) > 0
    assert len(retrieve_schema_file(Config.LICENSE_SCHEMA_URL)) > 0
