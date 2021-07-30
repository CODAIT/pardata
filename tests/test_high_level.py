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

import dataclasses
import json
import pathlib
import re

from packaging.version import parse as version_parser
import pytest
from pydantic import ValidationError

from pardata import (describe_dataset, export_schema_collections, get_config, get_dataset_metadata, init,
                     list_all_datasets, load_dataset, load_dataset_from_location, load_schema_collections)
from pardata.dataset import Dataset
from pardata._config import Config
from pardata._high_level import _get_schema_collections

# Global configurations --------------------------------------------------


class TestGetConfig:
    "Test high-level get_config function."

    def test_default_data_dir(self):
        "Test default data dir."

        pardata_data_home = pathlib.Path.home() / '.pardata' / 'data'
        assert get_config().DATADIR == pardata_data_home
        assert isinstance(get_config().DATADIR, pathlib.Path)


class TestInit:
    "Test high-level init function."

    def test_custom_data_dir(self, tmp_path, wikitext103_schema):
        "Test to make sure Dataset constructor uses new global data dir if one was supplied earlier to pardata.init."

        init(DATADIR=tmp_path)
        assert get_config().DATADIR == tmp_path
        assert isinstance(get_config().DATADIR, pathlib.Path)
        wikitext = Dataset(wikitext103_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.LAZY)
        assert wikitext._data_dir == tmp_path
        assert isinstance(wikitext._data_dir, pathlib.Path)

    def test_custom_relative_data_dir(self, chdir_tmp_path, tmp_sub_dir, tmp_relative_sub_dir):
        "Test using a custom relative data directory."

        init(DATADIR=tmp_relative_sub_dir)
        assert get_config().DATADIR == tmp_sub_dir
        assert get_config().DATADIR.is_absolute()

    def test_custom_symlink_data_dir(self, tmp_symlink_dir):
        "Test using a custom symlink data directory. The symlink should not be resolved."

        init(DATADIR=tmp_symlink_dir)
        assert get_config().DATADIR == tmp_symlink_dir

    def test_non_path_data_dir(self):
        "Test exception when a nonpath is passed as DATADIR."

        with pytest.raises(ValidationError) as e:
            init(DATADIR=10)

        assert re.search((r'1 validation error for Config\s+DATADIR\s+value'
                          r' is not a valid path \(type=type_error.path\)'), str(e.value))

    def test_custom_configs(self):
        "Test custom configs."

        init(update_only=False)  # set back everything to default
        assert dataclasses.asdict(get_config()) == dataclasses.asdict(Config())

        new_urls = {
            'DATASET_SCHEMA_FILE_URL': 'some/local/file',
            'FORMAT_SCHEMA_FILE_URL': 'file://c:/some/other/local/file',
            'LICENSE_SCHEMA_FILE_URL': 'http://some/remote/file'
        }
        init(update_only=True, **new_urls)

        for url, val in new_urls.items():
            assert getattr(get_config(), url) == val
        assert get_config().DATADIR == Config.DATADIR

# Dataset --------------------------------------------------


class TestListAllDatasets:
    "Test high-level list_all_datasets function."

    def test_list_all_datasets(self):
        "Test to make sure test_list_all_datasets function returns available dataset names."

        datasets = list_all_datasets()
        assert frozenset(datasets.keys()) == frozenset(['gmb', 'noaa_jfk', 'tensorflow_speech_commands', 'wikitext103'])


class TestLoadDataset:
    "Test high-level load_dataset function."

    def test_name_param(self, tmp_path):
        "Test to see the name parameter is being handled properly."

        init(DATADIR=tmp_path)

        with pytest.raises(TypeError) as e:
            load_dataset(123)
        assert str(e.value) == 'The name parameter must be supplied a str.'

        name = 'fake_dataset'
        with pytest.raises(KeyError) as e:
            load_dataset(name)
        assert str(e.value) == (f'\'"{name}" is not a valid ParData dataset. You can view all valid datasets and their '
                                'versions by running the function pardata.list_all_datasets().\'')

    def test_version_param(self, tmp_path):
        "Test to see the version parameter is being handled properly."

        init(DATADIR=tmp_path)

        with pytest.raises(TypeError) as e:
            load_dataset('gmb', version=1.0)
        assert str(e.value) == 'The version parameter must be supplied a str.'

        name, version = 'gmb', ''
        with pytest.raises(KeyError) as e:
            load_dataset('gmb', version=version)
        assert str(e.value) == (f'\'"{version}" is not a valid ParData version for the dataset "{name}". '
                                'You can view all valid datasets and their versions by running the function '
                                'pardata.list_all_datasets().\'')

        name, version = 'gmb', 'fake_version'
        with pytest.raises(KeyError) as e:
            load_dataset('gmb', version=version)
        assert str(e.value) == (f'\'"{version}" is not a valid ParData version for the dataset "{name}". '
                                'You can view all valid datasets and their versions by running the function '
                                'pardata.list_all_datasets().\'')

        # If no version specified, make sure latest version grabbed
        all_datasets = list_all_datasets()
        latest_version = str(sorted(version_parser(v) for v in all_datasets[name])[-1])
        assert load_dataset('gmb') == load_dataset('gmb', version=latest_version)

    def test_subdatasets_param(self, tmp_path):
        "Test to see subdatasets parameter is being handled properly."

        init(DATADIR=tmp_path)

        with pytest.raises(TypeError) as e:
            load_dataset('wikitext103', version='1.0.1', download=True, subdatasets=123)
        assert str(e.value) == '\'int\' object is not iterable'

        subdatasets = ['train']
        wikitext103_data = load_dataset('wikitext103', version='1.0.1', download=True, subdatasets=subdatasets)
        assert list(wikitext103_data.keys()) == subdatasets

    def test_default_dataset_schema_name(self, tmp_path, gmb_schema):
        "Test the default schemata name."

        init(DATADIR=tmp_path)
        data_dir = tmp_path / 'default' / 'gmb' / '1.0.2'
        gmb = Dataset(gmb_schema, data_dir=data_dir, mode=Dataset.InitializationMode.DOWNLOAD_AND_LOAD)
        _get_schema_collections().schema_collections['datasets']._schema_collection.pop('name')  # Remove the "name" key
        gmb_data = load_dataset('gmb', version='1.0.2', download=False)
        assert gmb.data == gmb_data

    def test_download_false(self, tmp_path, gmb_schema):
        "Test to see the function loads properly when download=False and dataset was previously downloaded."

        init(DATADIR=tmp_path)
        data_dir = tmp_path / 'dax' / 'gmb' / '1.0.2'
        gmb = Dataset(gmb_schema, data_dir=data_dir, mode=Dataset.InitializationMode.DOWNLOAD_AND_LOAD)
        gmb_data = load_dataset('gmb', version='1.0.2', download=False)
        assert gmb.data == gmb_data

    def test_download_true(self, tmp_path, downloaded_gmb_dataset):
        "Test to see the function downloads and loads properly when download=True."

        init(DATADIR=tmp_path)
        downloaded_gmb_dataset_data = downloaded_gmb_dataset.load()
        gmb_data = load_dataset('gmb', version='1.0.2', download=True)
        assert downloaded_gmb_dataset_data == gmb_data

    def test_loading_undownloaded(self, tmp_path):
        "Test loading before ``Dataset.download()`` has been called."

        init(DATADIR=tmp_path)
        with pytest.raises(RuntimeError) as e:
            load_dataset('wikitext103', version='1.0.1', download=False)
        assert ('Did you forget to download the dataset '
                '(by calling this function with `download=True` for at least once)?') in str(e.value)


class TestLoadDatasetFromLocation:
    "Test ``load_dataset_from_location."

    def test_loading_dataset_from_path(self, downloaded_gmb_dataset, dataset_dir):
        for force_redownload in ('False', 'False', 'True'):
            data = load_dataset_from_location(dataset_dir / 'gmb-1.0.2.zip', force_redownload=force_redownload)
            assert frozenset(data.keys()) == frozenset(('text/plain',))
            assert frozenset(data['text/plain'].keys()) == frozenset((
                'groningen_meaning_bank_modified/gmb_subset_full.txt',
                'groningen_meaning_bank_modified/LICENSE.txt',
                'groningen_meaning_bank_modified/README.txt'
            ))

    def test_loading_dataset_from_url(self, gmb_schema):
        for force_redownload in ('False', 'False', 'True'):
            data = load_dataset_from_location(gmb_schema['download_url'], force_redownload=force_redownload)
            assert frozenset(data.keys()) == frozenset(('text/plain',))
            assert frozenset(data['text/plain'].keys()) == frozenset((
                'groningen_meaning_bank_modified/gmb_subset_full.txt',
                'groningen_meaning_bank_modified/LICENSE.txt',
                'groningen_meaning_bank_modified/README.txt'
            ))

    def test_custom_schema(self, gmb_schema):
        data = load_dataset_from_location(gmb_schema['download_url'], schema=gmb_schema)
        assert frozenset(data.keys()) == frozenset(('gmb_subset_full',))
        assert data['gmb_subset_full'].startswith('Masked VBN O\n')
        assert data['gmb_subset_full'].endswith('. . O\n\n')


def test_get_dataset_metadata():
    "Test ``get_dataset_metadata``."

    name, version = 'gmb', '1.0.2'

    gmb_schema = get_dataset_metadata(name, version=version)
    assert (gmb_schema ==
            export_schema_collections().schema_collections['datasets'].export_schema('datasets', name, version))


def test_describe_dataset():
    "Test ``describe_dataset``."

    name, version = 'gmb', '1.0.2'

    gmb_description = describe_dataset(name, version=version)
    dataset_schema = export_schema_collections().schema_collections['datasets'].export_schema('datasets', name, version)
    license_schema = export_schema_collections().schema_collections['licenses'].export_schema('licenses')

    # Check a couple of spots
    assert dataset_schema['name'] in gmb_description
    assert dataset_schema['estimated_size'] in gmb_description
    assert license_schema[dataset_schema["license"]]["name"] in gmb_description

    # Instead of copying over the string for testing, we test a couple of important characteristics here
    gmb_lines = gmb_description.splitlines()
    assert len(gmb_lines) == 7  # number of lines
    assert all(line.strip() != '' for line in gmb_lines)  # no blank line
    assert all(line.strip() == line for line in gmb_lines)  # no trailing or leading whitespace
    assert all(':' in line for line in gmb_lines)  # no missing colons

# Schemata --------------------------------------------------


class TestSchemataFunctions:
    "Test the high-level schemata functions."

    def test_load_schema_collections(self, loaded_schema_collections, schema_file_absolute_dir):
        "Test high-level load_schema_collections function."

        init(update_only=False,
             DATASET_SCHEMA_FILE_URL=loaded_schema_collections.schema_collections['datasets'].retrieved_url_or_path,
             FORMAT_SCHEMA_FILE_URL=loaded_schema_collections.schema_collections['formats'].retrieved_url_or_path,
             LICENSE_SCHEMA_FILE_URL=loaded_schema_collections.schema_collections['licenses'].retrieved_url_or_path)
        load_schema_collections(force_reload=True)
        for name in ('datasets', 'formats', 'licenses'):
            assert (_get_schema_collections().schema_collections[name].retrieved_url_or_path ==
                    loaded_schema_collections.schema_collections[name].retrieved_url_or_path)

        init(update_only=True,
             # Different from the previous relative path used in loaded_schemata
             DATASET_SCHEMA_FILE_URL=schema_file_absolute_dir / 'datasets.yaml')
        load_schema_collections(force_reload=False)
        for name in ('formats', 'licenses'):
            assert (_get_schema_collections().schema_collections[name].retrieved_url_or_path ==
                    loaded_schema_collections.schema_collections[name].retrieved_url_or_path)
        assert (_get_schema_collections().schema_collections['datasets'].retrieved_url_or_path ==
                schema_file_absolute_dir / 'datasets.yaml')

    def test_export_schema_collections(self, schema_file_absolute_dir, schema_file_https_url):
        "Test high-level export_schema_collections function."

        assert export_schema_collections() is not _get_schema_collections()
        # The two returned schemata should equal
        assert (json.dumps(export_schema_collections().schema_collections['datasets'].export_schema(),
                           sort_keys=True, indent=2, default=str) ==
                json.dumps(_get_schema_collections().schema_collections['datasets'].export_schema(),
                           sort_keys=True, indent=2, default=str))

        # Different from https url used by pardata_initialization autouse fixture
        new_urls = {
            'DATASET_SCHEMA_FILE_URL': schema_file_absolute_dir / 'datasets.yaml',
            'LICENSE_SCHEMA_FILE_URL': schema_file_absolute_dir / 'licenses.yaml'
        }
        init(update_only=True, **new_urls)
        assert (export_schema_collections().schema_collections['formats'].retrieved_url_or_path ==
                f'{schema_file_https_url}/formats.yaml')
        assert (export_schema_collections().schema_collections['datasets'].retrieved_url_or_path ==
                new_urls['DATASET_SCHEMA_FILE_URL'])
        assert (export_schema_collections().schema_collections['licenses'].retrieved_url_or_path ==
                new_urls['LICENSE_SCHEMA_FILE_URL'])
