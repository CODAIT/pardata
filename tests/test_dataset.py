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

import tarfile

import pytest

from pydax.dataset import Dataset, list_all_datasets


def test_list_all_datasets():
    "Test to make sure test_list_all_datasets function returns available dataset names."

    datasets = list_all_datasets()
    assert all(d in ['gmb', 'wikitext103'] for d in datasets.keys())


class TestDataset:
    "Test Dataset class functionality."

    def test_mode(self, tmp_path, loaded_schemata):
        "Test if Dataset class catches an invalid mode."

        gmb_schema = loaded_schemata.schemata['dataset_schema'].export_schema('datasets', 'gmb', '1.0.2')
        with pytest.raises(ValueError) as e:
            Dataset(gmb_schema, tmp_path, mode='DOWNLOAD_ONLY')
        assert str(e.value) == 'DOWNLOAD_ONLY not a valid mode'

    def test_dataset_download(self, tmp_path, loaded_schemata):
        "Test Dataset class downloads a dataset properly."

        gmb_schema = loaded_schemata.schemata['dataset_schema'].export_schema('datasets', 'gmb', '1.0.2')
        data_dir = tmp_path / 'gmb'
        Dataset(gmb_schema, data_dir, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        assert len(list(data_dir.iterdir())) == 1
        unarchived_data_dir = data_dir / 'groningen_meaning_bank_modified'
        unarchived_data_dir_files = ['gmb_subset_full.txt', 'LICENSE.txt', 'README.txt']
        assert unarchived_data_dir.exists()
        assert len(list(unarchived_data_dir.iterdir())) == len(unarchived_data_dir_files)
        assert all(f.name in unarchived_data_dir_files for f in unarchived_data_dir.iterdir())

    def test_invalid_sha512(self, tmp_path, loaded_schemata):
        "Test if Dataset class catches an invalid hash."

        gmb_schema = loaded_schemata.schemata['dataset_schema'].export_schema('datasets', 'gmb', '1.0.2')
        gmb_schema['sha512sum'] = 'invalid hash example'

        with pytest.raises(IOError) as e:
            Dataset(gmb_schema, tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        assert 'the file may by corrupted' in str(e.value)

    def test_invalid_tarball(self, tmp_path, loaded_schemata):
        "Test if Dataset class catches an invalid tar file."

        fake_schema = loaded_schemata.schemata['dataset_schema'].export_schema('datasets', 'gmb', '1.0.2')
        fake_schema['download_url'] = 'https://dax-cdn.cdn.appdomain.cloud/dax-groningen-meaning-bank-modified/1.0.2/' \
                                      'data-preview/index.html'
        fake_schema['sha512sum'] = 'c51be3c51989bb06ef75c7f705843c790bd5a7dd099caf5b31a93cc56e21652e6952d33882eb88902' \
                                   'b0c0579795126068374764689b4526c2b02130bab694006'

        with pytest.raises(tarfile.ReadError) as e:
            Dataset(fake_schema, tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        assert 'Failed to unarchive' in str(e.value)
