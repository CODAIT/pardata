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


class TestSchemaRetrieval:
    "Test schema retrieval."

    def test_custom_schema_local(self):
        "Test retrieving user-specified local schema files."

        # We assert they are identical to the test schema files for now, because we don't host them on any websites.
        # Probably this will change in the future.
        assert retrieve_schema_file('./tests/schemata/datasets.yaml') == \
            Path('tests/schemata/datasets.yaml').read_text()
        assert retrieve_schema_file(f'file://{os.getcwd()}/tests/schemata/formats.yaml') == \
            Path('tests/schemata/formats.yaml').read_text()

    def test_custom_schema_remote(self, http_schema_file_url):
        "Test retrieving user-specified remote schema files."

        assert retrieve_schema_file(http_schema_file_url + 'licenses.yaml') == \
            Path('tests/schemata/licenses.yaml').read_text()
        # TODO: Add https tests here when we add stronger security measurements

    def test_invalid_schema(self):
        "Test retrieving user-specified invalid schema files."

        with pytest.raises(ValueError) as e:
            retrieve_schema_file(url_or_path='ftp://ftp/is/unsupported')

        assert str(e.value) == 'Unknown scheme in "ftp://ftp/is/unsupported": "ftp"'
