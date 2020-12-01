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

from pathlib import Path


def test_import_pydax_namespace():
    "Test to make sure top level public modules & subpackages are available in the global namespace."

    import pydax as test_pydax
    assert all(module.stem in dir(test_pydax) for module in Path('pydax').glob('[a-zA-Z]*'))


def test_import_pydax_loaders_namespace():
    "Test to make sure public modules are available in the loaders subpackage namespace."

    import pydax.loaders as test_pydax_loaders
    assert all(module.stem in dir(test_pydax_loaders) for module in Path('pydax/loaders').glob('[a-zA-Z]*'))
