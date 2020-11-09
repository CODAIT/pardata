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
import tarfile

import pytest

from pydax.dataset import Dataset, list_all_datasets


def test_list_all_datasets():
    "Test to make sure test_list_all_datasets function returns available dataset names."

    datasets = list_all_datasets()
    assert all(d in ['gmb', 'wikitext103'] for d in datasets.keys())


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

    def test_invalid_tarball(self, tmp_path, gmb_schema):
        "Test if Dataset class catches an invalid tar file."

        fake_schema = gmb_schema
        fake_schema['download_url'] = 'https://dax-cdn.cdn.appdomain.cloud/dax-groningen-meaning-bank-modified/1.0.2/' \
                                      'data-preview/index.html'
        fake_schema['sha512sum'] = 'c51be3c51989bb06ef75c7f705843c790bd5a7dd099caf5b31a93cc56e21652e6952d33882eb88902' \
                                   'b0c0579795126068374764689b4526c2b02130bab694006'

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
        assert str(e.value) == '"setup.py" exists and is not a directory.'
