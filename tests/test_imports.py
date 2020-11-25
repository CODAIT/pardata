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

def test_import_pydax_namespace():
    "Test to make sure top level modules & subpackages are available in the globla namespace."

    import pydax as test_pydax
    assert all(name in dir(test_pydax) for name in ['dataset', 'loaders', 'schema'])


def test_import_pydax_loaders_namespace():
    "Test to make sure modules are available in the loaders subpackage namespace."

    import pydax.loaders as test_pydax_loaders
    assert all(name in dir(test_pydax_loaders) for name in ['table', 'text'])
