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

from pydax import get_config, init
from pydax.dataset import Dataset


def test_default_data_dir(wikitext103_schema):
    "Test default data dir."

    pydax_data_home = pathlib.Path.home() / '.pydax' / 'data'
    assert get_config().DATADIR == pydax_data_home


def test_custom_data_dir(tmp_path, wikitext103_schema):
    "Test to make sure Dataset constructor uses new global data dir if one was supplied earlier to pydax.init."

    init(DATADIR=tmp_path)
    assert get_config().DATADIR == tmp_path
    wikitext = Dataset(wikitext103_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.LAZY)
    assert wikitext._data_dir == tmp_path
