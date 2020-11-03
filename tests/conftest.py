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

from tempfile import TemporaryDirectory

import pytest

from pydax.schema import load_schemata
from pydax.dataset import Dataset


@pytest.fixture
def loaded_schemata():
    return load_schemata(dataset_url='./tests/schemata/datasets.yaml',
                         format_url='./tests/schemata/formats.yaml',
                         license_url='./tests/schemata/licenses.yaml')


@pytest.fixture
def gmb_schema(loaded_schemata):
    return loaded_schemata.schemata['dataset_schema'].export_schema('datasets', 'gmb', '1.0.2')


@pytest.fixture
def downloaded_wikitext103_dataset(loaded_schemata):
    schema = loaded_schemata.schemata['dataset_schema'].export_schema('datasets', 'wikitext103', '1.0.1')
    with TemporaryDirectory() as tmp_data_dir:
        yield Dataset(schema, tmp_data_dir, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
