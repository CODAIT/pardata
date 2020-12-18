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

import pytest

from pydax.exceptions import InsecureConnectionError
from pydax._schema_retrieval import retrieve_schema_file


class TestSchemaRetrieval:
    "Test schema retrieval."

    # We set tls_verification to False in this test. We don't test raising this warning because it is not within the
    # project's scope to guarantee that this warning will raise, and this warning raises only once, which means that
    # whether the warning will be raised depends on the order in which the tests are being executed.
    @pytest.mark.filterwarnings('ignore:Unverified HTTPS request .*:urllib3.exceptions.InsecureRequestWarning')
    @pytest.mark.parametrize('location_type',
                             ('absolute_dir',
                              'relative_dir',
                              'file_url',
                              'http_url',
                              'https_url'))
    def test_custom_schema_insecure(self, location_type, schema_file_relative_dir, request):
        "Test retrieving user-specified schema files, with insecure connections allowed."

        # We use '/' instead of os.path.sep because URLs only accept / not \ as separators, but Windows path accepts
        # both. This is not an issue for the purpose of this test.
        base = str(request.getfixturevalue('schema_file_' + location_type)) + '/'

        assert retrieve_schema_file(base + 'datasets.yaml', tls_verification=False) == \
            (schema_file_relative_dir / 'datasets.yaml').read_text(encoding='utf-8')
        assert retrieve_schema_file(base + 'formats.yaml', encoding='ascii', tls_verification=False) == \
            (schema_file_relative_dir / 'formats.yaml').read_text(encoding='ascii')
        with pytest.raises(UnicodeDecodeError) as e:
            retrieve_schema_file(base + 'licenses.yaml', encoding='ascii', tls_verification=False)
        # We usually don't assert the position info because we don't want to rewrite this test every time the yaml
        # file changes in length.
        assert "'ascii' codec can't decode byte 0xe2" in str(e.value)
        with pytest.raises(UnicodeDecodeError) as e:
            retrieve_schema_file(base + 'formats-utf-16le-bom.yaml', tls_verification=False)
        # Test "position 0" here because it should fail at the beginning of the decoding
        assert "'utf-8' codec can't decode byte 0xff in position 0" in str(e.value)
        with pytest.raises(UnicodeDecodeError) as e:
            retrieve_schema_file(base + 'formats-utf-16be.yaml', encoding='utf-8', tls_verification=False)
        assert "'utf-8' codec can't decode byte 0x90" in str(e.value)

    def test_invalid_schema(self):
        "Test retrieving user-specified invalid schema files."

        with pytest.raises(ValueError) as e:
            retrieve_schema_file(url_or_path='ftp://ftp/is/unsupported')

        assert str(e.value) == 'Unknown scheme in "ftp://ftp/is/unsupported": "ftp"'

    @pytest.mark.parametrize('location_type', ('http_url', 'https_url'))
    def test_insecure_connections_fail(self, location_type, untrust_self_signed_cert, request):
        "Test insecure connections that should fail."
        url = str(request.getfixturevalue('schema_file_' + location_type)) + '/datasets.yaml'
        with pytest.raises(InsecureConnectionError) as e:
            retrieve_schema_file(url, tls_verification=True)
        assert url in str(e.value)
        assert retrieve_schema_file.__kwdefaults__['tls_verification'] is True

    @pytest.mark.parametrize('location_type',
                             ('absolute_dir',
                              'relative_dir',
                              'file_url',
                              'https_url'))
    def test_insecure_connections_succeed(self, location_type, schema_file_relative_dir, request):
        "Test secure connections that should succeed."
        # We use '/' instead of os.path.sep because URLs only accept / not \ as separators, but Windows path accepts
        # both. This is not an issue for the purpose of this test.
        path_or_url = str(request.getfixturevalue('schema_file_' + location_type)) + '/datasets.yaml'
        assert retrieve_schema_file(path_or_url, tls_verification=True) == \
            (schema_file_relative_dir / 'datasets.yaml').read_text(encoding='utf-8')
