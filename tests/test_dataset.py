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

import hashlib
import pathlib
import tarfile

import pytest
from packaging.version import parse as version_parser

from pydax import init, list_all_datasets, load_dataset
from pydax.dataset import Dataset


def test_list_all_datasets(spoofed_default_url):
    "Test to make sure test_list_all_datasets function returns available dataset names."

    datasets = list_all_datasets()
    assert frozenset(datasets.keys()) == frozenset(['gmb', 'noaa_jfk', 'wikitext103'])


class TestDataset:
    "Test Dataset class functionality."

    def test_mode(self, tmp_path, gmb_schema):
        "Test if Dataset class catches an invalid mode."

        with pytest.raises(ValueError) as e:
            Dataset(gmb_schema, data_dir=tmp_path, mode='DOWNLOAD_ONLY')
        assert str(e.value) == 'DOWNLOAD_ONLY not a valid mode'

    def test_dataset_download(self, tmp_path, gmb_schema):
        "Test Dataset class downloads a dataset properly."

        data_dir = tmp_path / 'gmb'
        Dataset(gmb_schema, data_dir=data_dir, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        assert len(list(data_dir.iterdir())) == 1
        unarchived_data_dir = data_dir / 'groningen_meaning_bank_modified'
        unarchived_data_dir_files = ['gmb_subset_full.txt', 'LICENSE.txt', 'README.txt']
        assert unarchived_data_dir.is_dir()
        assert len(list(unarchived_data_dir.iterdir())) == len(unarchived_data_dir_files)
        assert all(f.name in unarchived_data_dir_files for f in unarchived_data_dir.iterdir())

    def test_invalid_sha512(self, tmp_path, gmb_schema):
        "Test if Dataset class catches an invalid hash."

        gmb_schema['sha512sum'] = 'invalid hash example'

        with pytest.raises(IOError) as e:
            Dataset(gmb_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        assert 'the file may by corrupted' in str(e.value)

    def test_invalid_tarball(self, tmp_path, gmb_schema, schema_file_http_url, schema_file_relative_dir):
        "Test if Dataset class catches an invalid tar file."

        fake_schema = gmb_schema
        fake_schema['download_url'] = schema_file_http_url + '/datasets.yaml'
        fake_schema['sha512sum'] = hashlib.sha512((schema_file_relative_dir / 'datasets.yaml').read_bytes()).hexdigest()

        with pytest.raises(tarfile.ReadError) as e:
            Dataset(fake_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        assert 'Failed to unarchive' in str(e.value)

    def test_load(self, downloaded_wikitext103_dataset):
        "Test basic loading functionality."

        downloaded_wikitext103_dataset.load()

        assert (hashlib.sha512(downloaded_wikitext103_dataset.data['train'].encode()).hexdigest() ==
                ('df7615f77cb9dd19975881f271e3e3525bee38c08a67fea36a51c96be69a3ecabc9e05c02cbaf'
                 '6fc63a0082efb44156f61c81061d3b0272bbccd7657c682e791'))

        assert (hashlib.sha512(downloaded_wikitext103_dataset.data['valid'].encode()).hexdigest() ==
                ('e4834d365d5f8313503895fd8304d29a566ff4a2df77efb32457fdc353304fb61460511f89bb9'
                 '0f14a47132c1539aaa324d3e71f5f56045a61a7292ad25a3c02'))

        assert (hashlib.sha512(downloaded_wikitext103_dataset.data['test'].encode()).hexdigest() ==
                ('6fe665d33c0f788eba76da50539f0ca02432c70c94b788a493da491215e86043fc732dbeef9bb'
                 '49a72341c7283ea55f59d10941ac41f7ac58aea3bdcd72f5cd8'))

    def test_constructor_download_and_load(self, tmp_path, wikitext103_schema):
        "Test the full power of Dataset.__init__() (mode being ``InitializationMode.DOWNLOAD_AND_LOAD``)."

        dataset = Dataset(wikitext103_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_AND_LOAD)

        assert (hashlib.sha512(dataset.data['train'].encode()).hexdigest() ==
                ('df7615f77cb9dd19975881f271e3e3525bee38c08a67fea36a51c96be69a3ecabc9e05c02cbaf'
                 '6fc63a0082efb44156f61c81061d3b0272bbccd7657c682e791'))

        assert (hashlib.sha512(dataset.data['valid'].encode()).hexdigest() ==
                ('e4834d365d5f8313503895fd8304d29a566ff4a2df77efb32457fdc353304fb61460511f89bb9'
                 '0f14a47132c1539aaa324d3e71f5f56045a61a7292ad25a3c02'))

        assert (hashlib.sha512(dataset.data['test'].encode()).hexdigest() ==
                ('6fe665d33c0f788eba76da50539f0ca02432c70c94b788a493da491215e86043fc732dbeef9bb'
                 '49a72341c7283ea55f59d10941ac41f7ac58aea3bdcd72f5cd8'))

    def test_loading_undownloaded(self, tmp_path, gmb_schema):
        "Test loading before ``Dataset.download()`` has been called."

        dataset = Dataset(gmb_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.LAZY)

        with pytest.raises(FileNotFoundError) as e:
            dataset.load()
        assert ('Failed to load subdataset "gmb_subset_full" because some files are not found. '
                'Did you forget to call Dataset.download()?\nCaused by:\n') in str(e.value)

    def test_unloaded_access_to_data(self, tmp_path, gmb_schema):
        "Test access to `Dataset.data` when no data has been loaded."

        dataset = Dataset(gmb_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.LAZY)
        with pytest.raises(RuntimeError) as e:
            dataset.data
        assert 'Data has not been loaded yet. Call Dataset.load() to load data.' == str(e.value)

        # Same after downloading
        dataset.download()
        with pytest.raises(RuntimeError) as e:
            dataset.data
        assert str(e.value) == 'Data has not been loaded yet. Call Dataset.load() to load data.'

    def test_data_dir_is_not_a_dir(self, gmb_schema):
        "Test when ``data_dir`` exists and is not a dir."

        with pytest.raises(FileExistsError) as e:
            Dataset(gmb_schema, data_dir='./setup.py', mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        assert str(e.value) == f'"{pathlib.Path.cwd()/"setup.py"}" exists and is not a directory.'

    def test_relative_data_dir(self, gmb_schema, chdir_tmp_path, tmp_sub_dir, tmp_relative_sub_dir):
        "Test when ``data_dir`` is relative."

        dataset = Dataset(gmb_schema, data_dir=tmp_relative_sub_dir, mode=Dataset.InitializationMode.LAZY)
        assert dataset._data_dir == tmp_sub_dir
        assert dataset._data_dir.is_absolute()

    def test_symlink_data_dir(self, tmp_symlink_dir, gmb_schema):
        "Test when ``data_dir`` is a symlink. The symlink should not be resolved."

        dataset = Dataset(gmb_schema, data_dir=tmp_symlink_dir, mode=Dataset.InitializationMode.LAZY)
        assert dataset._data_dir == tmp_symlink_dir

    def test_is_downloaded(self, tmp_path, gmb_schema):
        "Test is_downloaded method."

        data_dir = tmp_path / 'gmb' / '1.0.2'
        gmb = Dataset(gmb_schema, data_dir=data_dir, mode=Dataset.InitializationMode.LAZY)
        assert gmb.is_downloaded() is False

        gmb.download()
        assert gmb.is_downloaded() is True


class TestLoadDataset:
    "Test load_dataset function."

    def test_name_param(self, tmp_path):
        "Test to see the name parameter is being handled properly."

        init(DATADIR=tmp_path)

        with pytest.raises(TypeError) as e:
            load_dataset(123)
        assert str(e.value) == 'The name parameter must be supplied a str.'

        name = 'fake_dataset'
        with pytest.raises(KeyError) as e:
            load_dataset(name)
        assert str(e.value) == (f'\'Failed to load dataset because "{name}" is not a valid PyDAX dataset. '
                                'You can view all valid datasets and their versions by running the function '
                                'pydax.list_all_datasets().\'')

    def test_version_param(self, tmp_path):
        "Test to see the version parameter is being handled properly."

        init(DATADIR=tmp_path)

        with pytest.raises(TypeError) as e:
            load_dataset('gmb', version=1.0)
        assert str(e.value) == 'The version parameter must be supplied a str.'

        name, version = 'gmb', ''
        with pytest.raises(ValueError) as e:
            load_dataset('gmb', version=version)
        assert str(e.value) == (f'Failed to load dataset because "{version}" is not a valid PyDAX version for the '
                                f'dataset "{name}". You can view all valid datasets and their versions by running the '
                                'function pydax.list_all_datasets().')

        name, version = 'gmb', 'fake_version'
        with pytest.raises(ValueError) as e:
            load_dataset('gmb', version=version)
        assert str(e.value) == (f'Failed to load dataset because "{version}" is not a valid PyDAX version for the '
                                f'dataset "{name}". You can view all valid datasets and their versions by running the '
                                'function pydax.list_all_datasets().')

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

    def test_download_false(self, tmp_path, gmb_schema):
        "Test to see the function loads properly when download=False and dataset was previously downloaded."

        init(DATADIR=tmp_path)
        data_dir = tmp_path / 'gmb' / '1.0.2'
        gmb = Dataset(gmb_schema, data_dir=data_dir, mode=Dataset.InitializationMode.DOWNLOAD_AND_LOAD)
        gmb_data = load_dataset('gmb', version='1.0.2', download=False)
        assert gmb.data == gmb_data

    def test_download_true(self, tmp_path, downloaded_gmb_dataset):
        "Test to see the function downloads and loads properly when download=True."

        init(DATADIR=tmp_path)
        downloaded_gmb_dataset.load()
        gmb_data = load_dataset('gmb', version='1.0.2', download=True)
        assert downloaded_gmb_dataset.data == gmb_data

    def test_loading_undownloaded(self, tmp_path):
        "Test loading before ``Dataset.download()`` has been called."

        init(DATADIR=tmp_path)
        with pytest.raises(FileNotFoundError) as e:
            load_dataset('wikitext103', version='1.0.1', download=False)
        assert 'Failed to load the dataset because some files are not found.' in str(e.value)
