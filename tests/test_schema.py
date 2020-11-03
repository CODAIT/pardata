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

import datetime

import pytest

from pydax.schema import DatasetSchema, SchemaManager


class TestSchema:
    "Test the functionality of the schema classes."

    def test_loading_schemata(self, loaded_schemata):
        "Test basic functioning of loading and parsing the schema files."

        assert loaded_schemata.schemata['dataset_schema'] \
            .export_schema()['datasets']['gmb']['1.0.2']['published'] == datetime.date(2019, 12, 19)
        assert loaded_schemata.schemata['license_schema'] \
            .export_schema()['licenses']['cdla_sharing']['commercial_use'] is True
        assert loaded_schemata.schemata['format_schema'] \
            .export_schema('formats', 'csv', 'name') == 'Comma-Separated Values'
        assert loaded_schemata.schemata['dataset_schema'].export_schema()['datasets']['gmb']['1.0.2']['homepage'] == \
            loaded_schemata.schemata['dataset_schema'].export_schema('datasets', 'gmb', '1.0.2', 'homepage')

    def test_schema_without_url(self, loaded_schemata):
        "Test instantiating a Schema without supplying a path or url."

        assert DatasetSchema().export_schema() == loaded_schemata.schemata['dataset_schema'].export_schema()


def test_schema_manager_value():
    "Test SchemaManager to make sure it raises an exception when it recieves a non-Schema object"

    with pytest.raises(TypeError) as e:
        SchemaManager(dataset_schema='ibm',
                      format_schema='1',
                      license_schema='3.3')

    assert str(e.value) == 'val must be a Schema instance.'
