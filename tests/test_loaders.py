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

from pydax.loaders import Loader
from pydax.loaders import FormatLoaderMap
from pydax.loaders._format_loader_map import _load_data_files
from pydax.loaders.text import PlainTextLoader


class TestBaseLoader:
    "Test loaders._base.*"

    def test_abstract(self):
        "Loader is an abstract class."

        with pytest.raises(TypeError) as e:
            Loader()
        assert 'abstract class' in str(e.value)

    def test_load(self, tmp_path):
        "Loader.load() must be overridden upon Loader being inherited."

        class MyLoader(Loader):
            pass

        # Error out in instantiating MyLoader because loader is not overridden
        with pytest.raises(TypeError) as e:
            MyLoader()
        assert "Can't instantiate abstract class MyLoader with abstract method" in str(e.value)

        class MyLoader(Loader):
            def load(self, path):
                # Calling the parent's load() method shouldn't lead to error
                super().load(path)
        MyLoader().load(tmp_path)  # This line shouldn't error out even though it calls an abstract method in its parent


class TestFormatLoaderMap:
    "Test loaders._format_loader.*"

    def test_register_non_loader(self):
        "Test when it registers a non-Loader instance."

        flm = FormatLoaderMap()

        with pytest.raises(TypeError) as e:
            flm.register_loader('some-format', 'some-string')
        assert str(e.value) == 'loader "some-string" must be a Loader instance.'

    def test_load_non_existing_format(self, tmp_path):
        "Test loading a non-existing format."

        with pytest.raises(RuntimeError) as e:
            _load_data_files('nonsense', tmp_path)

        assert str(e.value) == 'The format loader map does not specify a loader for format "nonsense".'


class TestTextLoaders:

    def test_plain_text_loader(self):
        "Test PlainTextLoader when fed in with non-path."

        integer = 1
        with pytest.raises(TypeError) as e:
            PlainTextLoader().load(integer)

        assert str(e.value) == f'Unsupported path type "{type(integer)}".'
