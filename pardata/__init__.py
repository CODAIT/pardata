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

"ParData package and high level functions."


from . import dataset, exceptions, loaders, schema
from ._high_level import (describe_dataset,
                          export_schema_collections,
                          get_config,
                          get_dataset_metadata,
                          init,
                          list_all_datasets,
                          load_dataset,
                          load_dataset_from_location,
                          load_schema_collections)
from ._version import version as __version__
