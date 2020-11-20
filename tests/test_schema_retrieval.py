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

import pytest

from pydax._schema_retrieval import retrieve_schema_file


class TestSchemaRetrieval:
    "Test schema retrieval."

    @pytest.mark.parametrize('base_schema_file_url_or_path',
                             ('schema_file_absolute_dir',
                              'schema_file_relative_dir',
                              'schema_file_file_url',
                              'schema_file_http_url'))
    def test_custom_schema(self, base_schema_file_url_or_path, schema_file_relative_dir, request):
        "Test retrieving user-specified schema files."

        # TODO: Add https tests here when we add stronger security measurements

        base = str(request.getfixturevalue(base_schema_file_url_or_path)) + os.path.sep

        assert retrieve_schema_file(base + 'datasets.yaml') == \
            (schema_file_relative_dir / 'datasets.yaml').read_text(encoding='utf-8')
        assert retrieve_schema_file(base + 'formats.yaml', encoding='ascii') == \
            (schema_file_relative_dir / 'formats.yaml').read_text(encoding='ascii')
        with pytest.raises(UnicodeDecodeError) as e:
            retrieve_schema_file(base + 'licenses.yaml', encoding='ascii')
        # We usually don't assert the position info because we don't want to rewrite this test every time the yaml
        # file changes in length.
        assert "'ascii' codec can't decode byte 0xe2" in str(e.value)
        with pytest.raises(UnicodeDecodeError) as e:
            retrieve_schema_file(base + 'formats-utf-16le-bom.yaml')
        # Test "position 0" here because it should fail at the beginning of the decoding
        assert "'utf-8' codec can't decode byte 0xff in position 0" in str(e.value)
        with pytest.raises(UnicodeDecodeError) as e:
            retrieve_schema_file(base + 'formats-utf-16be.yaml', encoding='utf-8')
        assert "'utf-8' codec can't decode byte 0x90" in str(e.value)

    def test_invalid_schema(self):
        "Test retrieving user-specified invalid schema files."

        with pytest.raises(ValueError) as e:
            retrieve_schema_file(url_or_path='ftp://ftp/is/unsupported')

        assert str(e.value) == 'Unknown scheme in "ftp://ftp/is/unsupported": "ftp"'
