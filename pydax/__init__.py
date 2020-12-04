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

"PyDAX package"


from . import dataset, loaders, schema
from ._config import get_config, init
from ._dataset import get_dataset_metadata, list_all_datasets, load_dataset
from ._schema import load_schemata
from ._version import version as __version__

__all__ = (
           # modules & subpackages
           'dataset',
           'loaders',
           'schema',
           # _config
           'get_config',
           'init',
           # _dataset
           'get_dataset_metadata',
           'list_all_datasets',
           'load_dataset',
           # _schema
           'load_schemata',
           # _version
           '__version__'
)
