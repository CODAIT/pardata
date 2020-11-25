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
from urllib.parse import urlparse


import requests.exceptions
import pytest

from pydax.schema import DatasetSchema, FormatSchema, LicenseSchema, Schema, SchemaManager
from pydax._schema_retrieval import retrieve_schema_file


class TestBaseSchema:
    "Test Schema ABC."

    def test_abstract(self):
        "Test Schema is an abstract class."

        assert Schema.__bases__ == (abc.ABC,)

    def test_no_DEFAULT_SCHEMA_URL(self):
        "Test when a child class of Schema doesn't override DEFAULT_SCHEMA_URL."

        class MySchema(Schema):
            def __init__(self):
                super().__init__()

        with pytest.raises(AttributeError) as e:
            MySchema()

        assert ('DEFAULT_SCHEMA_URL is not defined. '
                'Have you forgotten to define this variable when inheriting "Schema"?\n') in str(e.value)

        class MySchema(Schema):
            DEFAULT_SCHEMA_URL = 'https://ibm.box.com/shared/static/01oa3ue32lzcsd2znlbojs9ozdeftpb6.yaml'
        MySchema()  # This line shouldn't error out as long as MySchema.DEFAULT_SCHEMA_URL is valid schema


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

    def test_schema_without_url(self, loaded_schemata, schema_file_http_url):
        "Test instantiating a Schema without supplying a path or url."

        class MyDatasetSchema(Schema):
            DEFAULT_SCHEMA_URL = schema_file_http_url + '/datasets.yaml'

        assert MyDatasetSchema().export_schema() == loaded_schemata.schemata['dataset_schema'].export_schema()

    def test_default_schema_url_https(self):
        "Test the default schema URLs are https-schemed."

        assert urlparse(DatasetSchema.DEFAULT_SCHEMA_URL).scheme == 'https'
        assert urlparse(FormatSchema.DEFAULT_SCHEMA_URL).scheme == 'https'
        assert urlparse(LicenseSchema.DEFAULT_SCHEMA_URL).scheme == 'https'

    @pytest.mark.xfail(reason="default remote might be down but it's not this library's issue",
                       raises=requests.exceptions.ConnectionError)
    def test_default_schema_url_content(self):
        """Test the content of the remote URLs a bit. We only assert them not being None here just in case the server
        returns zero-length files."""

        # We only assert that we have retrieved some non-empty files in this test. This is because we want to decouple
        # the maintenance of schema files in production with the library development. These files likely would change
        # more regularly than the library. For this reason, we also verify the default schema URLs are also valid https
        # links in ``test_default_schema_url_https``.

        # This test is in `test_schema.py` not in `test_schema_retrieval.py` because this test is more about the content
        # of the default schema URLs than the retrieving functionality.
        assert retrieve_schema_file(DatasetSchema.DEFAULT_SCHEMA_URL) is not None
        assert retrieve_schema_file(FormatSchema.DEFAULT_SCHEMA_URL) is not None
        assert retrieve_schema_file(LicenseSchema.DEFAULT_SCHEMA_URL) is not None


def test_schema_manager_value():
    "Test SchemaManager to make sure it raises an exception when it recieves a non-Schema object"

    with pytest.raises(TypeError) as e:
        SchemaManager(dataset_schema='ibm',
                      format_schema='1',
                      license_schema='3.3')

    assert str(e.value) == 'val must be a Schema instance.'
