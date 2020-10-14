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

import pathlib

from pydax import _schema_retrieval


class TestSchemaRetrieval:
    "Test schema retrieval."

    def test_basic_schema_retrieval(self):
        "Test the basic functioning of retrieving schema files."

        schemata = _schema_retrieval.retrieve_schema_files()

        # We assert they are identical to the examples for now, because we don't host them on any websites. Probably
        # this will change in the future.
        assert schemata['datasets'] == pathlib.Path('examples/schema-datasets.yaml').read_text()
        assert schemata['formats'] == pathlib.Path('examples/schema-formats.yaml').read_text()
        assert schemata['licenses'] == pathlib.Path('examples/schema-licenses.yaml').read_text()
