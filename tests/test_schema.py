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

import abc
import datetime

import pytest

from pardata.schema import SchemaCollection, SchemaCollectionManager


class TestBaseSchemaCollection:
    "Test SchemaCollection ABC."

    def test_abstract(self):
        "Test whether SchemaCollection is an abstract class."

        assert SchemaCollection.__bases__ == (abc.ABC,)

    def test_retrieved_url_or_path(self, schema_file_relative_dir):
        "Test whether retrieved_url_or_path gives the correct value."

        url_or_path = schema_file_relative_dir / 'datasets.yaml'
        assert SchemaCollection(url_or_path).retrieved_url_or_path == url_or_path


class TestSchemaCollection:
    "Test the functionality of the SchemaCollection's child classes."

    def test_loading_schema_collection(self, loaded_schema_collections):
        "Test basic functioning of loading and parsing the schema files."

        assert loaded_schema_collections.schema_collections['datasets'] \
            .export_schema()['datasets']['gmb']['1.0.2']['published'] == datetime.date(2019, 12, 19)
        assert loaded_schema_collections.schema_collections['licenses'] \
            .export_schema()['licenses']['cdla_sharing']['commercial_use'] is True
        assert loaded_schema_collections.schema_collections['formats'] \
            .export_schema('formats', 'table/csv', 'name') == 'Comma-Separated Values'
        assert loaded_schema_collections.schema_collections['datasets'] \
            .export_schema()['datasets']['gmb']['1.0.2']['homepage'] == \
            loaded_schema_collections.schema_collections['datasets'] \
            .export_schema('datasets', 'gmb', '1.0.2', 'homepage')

    def test_getting_license_name(self, loaded_schema_collections):
        "Test getting the name of a license."
        # customized
        assert (loaded_schema_collections.schema_collections['licenses'].get_license_name('cdla_sharing') ==
                'Community Data License Agreement – Sharing, Version 1.0 (CDLA-Sharing-1.0)')
        # SPDX token
        assert (loaded_schema_collections.schema_collections['licenses'].get_license_name('CDLA-Sharing-1.0') ==
                'Community Data License Agreement Sharing 1.0')
        # Unknown
        with pytest.raises(ValueError) as e:
            loaded_schema_collections.schema_collections['licenses'].get_license_name('nonsense')
        assert str(e.value) == 'Unknown license nonsense'


class TestSchemaCollectionManager:
    "Test the functionality of the SchemaCollectionManager class."

    def test_schema_collection_manager_value(self):
        """Test SchemaCollectionManager to make sure it raises an exception when it receives a non-SchemaCollection
        object.
        """

        with pytest.raises(TypeError) as e:
            SchemaCollectionManager(datasets='ibm',
                                    formats='1',
                                    licenses='3.3')
        assert str(e.value) == 'val must be a SchemaCollection instance.'
