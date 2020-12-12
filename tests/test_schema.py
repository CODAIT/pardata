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

import abc
import datetime
import json

import pytest

from pydax import export_schemata, init, load_schemata
from pydax.schema import Schema, SchemaManager
from pydax._high_level import get_schemata


class TestBaseSchema:
    "Test Schema ABC."

    def test_abstract(self):
        "Test Schema is an abstract class."

        assert Schema.__bases__ == (abc.ABC,)

    def test_retrieved_url_or_path(self, schema_file_relative_dir):
        "Test whether retrieved_url_or_path gives the correct value."

        url_or_path = schema_file_relative_dir / 'datasets.yaml'
        assert Schema(url_or_path).retrieved_url_or_path == url_or_path


class TestSchema:
    "Test the functionality of the schema classes."

    def test_loading_schemata(self, loaded_schemata):
        "Test basic functioning of loading and parsing the schema files."

        assert loaded_schemata.schemata['datasets'] \
            .export_schema()['datasets']['gmb']['1.0.2']['published'] == datetime.date(2019, 12, 19)
        assert loaded_schemata.schemata['licenses'] \
            .export_schema()['licenses']['cdla_sharing']['commercial_use'] is True
        assert loaded_schemata.schemata['formats'] \
            .export_schema('formats', 'csv', 'name') == 'Comma-Separated Values'
        assert loaded_schemata.schemata['datasets'].export_schema()['datasets']['gmb']['1.0.2']['homepage'] == \
            loaded_schemata.schemata['datasets'].export_schema('datasets', 'gmb', '1.0.2', 'homepage')

    def test_load_schemata(self, loaded_schemata, schema_file_absolute_dir):
        "Test load_schemata."

        init(update_only=False,
             DATASET_SCHEMA_URL=loaded_schemata.schemata['datasets'].retrieved_url_or_path,
             FORMAT_SCHEMA_URL=loaded_schemata.schemata['formats'].retrieved_url_or_path,
             LICENSE_SCHEMA_URL=loaded_schemata.schemata['licenses'].retrieved_url_or_path)
        load_schemata(force_reload=True)
        for name in ('datasets', 'formats', 'licenses'):
            assert (get_schemata().schemata[name].retrieved_url_or_path ==
                    loaded_schemata.schemata[name].retrieved_url_or_path)

        init(update_only=True,
             # different from the previous relative path used in loaded_schemata
             DATASET_SCHEMA_URL=schema_file_absolute_dir / 'datasets.yaml')
        load_schemata(force_reload=False)
        for name in ('formats', 'licenses'):
            assert (get_schemata().schemata[name].retrieved_url_or_path ==
                    loaded_schemata.schemata[name].retrieved_url_or_path)
        assert get_schemata().schemata['datasets'].retrieved_url_or_path == schema_file_absolute_dir / 'datasets.yaml'

    def test_exporting_schemata(self):
        "Test basic functionality of exporting schemata."

        assert export_schemata() is not get_schemata()
        # The two returned schemata should equal
        assert (json.dumps(export_schemata().schemata['datasets'].export_schema(),
                           sort_keys=True, indent=2, default=str) ==
                json.dumps(get_schemata().schemata['datasets'].export_schema(), sort_keys=True, indent=2, default=str))


def test_schema_manager_value():
    "Test SchemaManager to make sure it raises an exception when it recieves a non-Schema object"

    with pytest.raises(TypeError) as e:
        SchemaManager(dataset_schema='ibm',
                      format_schema='1',
                      license_schema='3.3')

    assert str(e.value) == 'val must be a Schema instance.'
