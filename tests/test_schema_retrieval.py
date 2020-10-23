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

import os
from pathlib import Path

import pytest

from pydax._schema_retrieval import retrieve_schema_file
from pydax.schema_loading import DatasetSchema, FormatSchema, LicenseSchema


class TestSchemaRetrieval:
    "Test schema retrieval."

    def test_default_schema(self):
        "Test the basic functioning of retrieving default schema files."

        # We assert they are identical to the examples for now, because we don't host them on any websites. Probably
        # this will change in the future.
        assert retrieve_schema_file(DatasetSchema.DEFAULT_SCHEMA_URL) == \
            Path('examples/schema-datasets.yaml').read_text()
        assert retrieve_schema_file(FormatSchema.DEFAULT_SCHEMA_URL) == \
            Path('examples/schema-formats.yaml').read_text()
        assert retrieve_schema_file(LicenseSchema.DEFAULT_SCHEMA_URL) == \
            Path('examples/schema-licenses.yaml').read_text()

    def test_custom_schema(self):
        "Test retrieving user-specified schema files."

        # We assert they are identical to the examples for now, because we don't host them on any websites. Probably
        # this will change in the future.
        assert retrieve_schema_file('./examples/schema-datasets.yaml') == \
            Path('examples/schema-datasets.yaml').read_text()
        assert retrieve_schema_file(f'file://{os.getcwd()}/examples/schema-formats.yaml') == \
            Path('examples/schema-formats.yaml').read_text()
        assert retrieve_schema_file(LicenseSchema.DEFAULT_SCHEMA_URL.replace('https://', 'http://', 1)) == \
            Path('examples/schema-licenses.yaml').read_text()

    def test_invalid_schema(self):
        "Test retrieving user-specified invalid schema files."

        with pytest.raises(ValueError) as e:
            retrieve_schema_file(url_or_path='ftp://ftp/is/unsupported')

        assert str(e.value) == 'Unknown scheme in "ftp://ftp/is/unsupported": "ftp"'
