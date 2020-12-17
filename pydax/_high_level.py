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

"""High-level functions. They are tailored for new users to quickly get started with PyDAX for common tasks."""

# We don't use __all__ in this file because having every exposed function shown in __init__.py is more clear.

from copy import deepcopy
import dataclasses
import functools
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Union, no_type_check
from packaging.version import parse as version_parser

from ._config import Config
from ._dataset import Dataset
from ._schema import Schema, SchemaDict, SchemaManager


def get_config() -> Config:
    """Returns global PyDAX configs.

    :return: Read-only global configs represented as a data class

    Example get_config:

    >>> config = get_config()
    >>> config.DATASET_SCHEMA_URL
    'https://raw.githubusercontent.com/CODAIT/dax-schemata/master/datasets.yaml'
    >>> config.FORMAT_SCHEMA_URL
    'https://raw.githubusercontent.com/CODAIT/dax-schemata/master/formats.yaml'
    >>> config.LICENSE_SCHEMA_URL
    'https://raw.githubusercontent.com/CODAIT/dax-schemata/master/licenses.yaml'

    """
    return _global_config  # type: ignore [name-defined]


# The SchemaManager object that is managed by high-level functions
_schemata: Optional[SchemaManager] = None


def init(update_only: bool = True, **kwargs: Any) -> None:
    """
    (Re-)initialize the PyDAX library. This includes updating PyDAX global configs.

    :param update_only: If ``True``, only update in the global configs what config is specified; reuse schemata loaded
        by high-level functions if URLs do not change. Otherwise, reset everything to default in global configs except
        those specified as keyword arguments; clear all schemata loaded by high-level functions.
    :param DATASET_SCHEMA_URL: The default dataset schema file URL.
    :param FORMAT_SCHEMA_URL: The default format schema file URL.
    :param LICENSE_SCHEMA_URL: The default license schema file URL.
    :param DATADIR: Default dataset directory to download/load to/from. The path can be either absolute or relative to
        the current working directory, but will be converted to the absolute path immediately in this function.
        Defaults to: ~/.pydax/data
    """
    global _global_config, _schemata

    if update_only:
        # We don't use dataclasses.replace here because it is uncertain whether it would work well with
        # pydantic.dataclasses.
        prev = dataclasses.asdict(_global_config)  # type: ignore [name-defined]
        prev.update(kwargs)
        _global_config = Config(**prev)  # type: ignore [name-defined]
    else:
        _global_config = Config(**kwargs)  # type: ignore [name-defined]
        _schemata = None


init(update_only=False)


def list_all_datasets() -> Dict[str, Tuple]:
    """Show all available pydax datasets and their versions.

    :return: Mapping of available datasets and their versions

    Example list_all_datasets()

    >>> import pprint
    >>> datasets = list_all_datasets()
    >>> pprint.pprint(datasets)
    {'claim_sentences_search': ('1.0.2',),
     'expert-in-the-loop-ai-polymer-discovery': ('1.0.0',),
     'gmb': ('1.0.2',),
     'noaa_jfk': ('1.1.4',),
     'wikitext103': ('1.0.1',)}
    """

    dataset_schema = export_schemata().schemata['datasets'].export_schema('datasets')
    return {
        outer_k: tuple(inner_k for inner_k, inner_v in outer_v.items())
        for outer_k, outer_v in dataset_schema.items()
    }


@no_type_check
def _handle_name_param(func: Callable) -> Callable:
    """Decorator for handling ``name`` parameter.

    :raises TypeError: ``name`` is not a string.
    :raises KeyError: ``name`` is not a valid PyDAX dataset name.
    :return: Wrapped function that handles ``name`` parameter properly.
    """
    @functools.wraps(func)
    def name_wrapper(name: str, *args, **kwargs):

        if not isinstance(name, str):
            raise TypeError('The name parameter must be supplied a str.')
        all_datasets = list_all_datasets()
        if name not in all_datasets.keys():
            raise KeyError(f'"{name}" is not a valid PyDAX dataset. You can view all valid datasets and their versions '
                           'by running the function pydax.list_all_datasets().')
        return func(name, *args, **kwargs)
    return name_wrapper


@no_type_check
def _handle_version_param(func: Callable) -> Callable:
    """Decorator for handling ``version`` parameter. Must still be supplied a dataset ``name``.

    :raises TypeError: ``version`` is not a string.
    :raises KeyError: ``version`` is not a valid PyDAX version of ``name``.
    :return: Wrapped function that handles ``version`` parameter properly.
    """
    @functools.wraps(func)
    def version_wrapper(name: str, version: str = 'latest', *args, **kwargs):

        if not isinstance(version, str):
            raise TypeError('The version parameter must be supplied a str.')
        all_datasets = list_all_datasets()
        if version == 'latest':
            # Grab latest available version
            version = str(max(version_parser(v) for v in all_datasets[name]))
        elif version not in all_datasets[name]:
            raise KeyError(f'"{version}" is not a valid PyDAX version for the dataset "{name}". You can view all '
                           'valid datasets and their versions by running the function pydax.list_all_datasets().')
        return func(name=name, version=version, *args, **kwargs)
    return version_wrapper


@_handle_name_param
@_handle_version_param
def load_dataset(name: str, *,
                 version: str = 'latest',
                 download: bool = True,
                 subdatasets: Union[Iterable[str], None] = None) -> Dict[str, Any]:
    """High level function that wraps :class:`Dataset` class's load and download functionality. Downloads to and loads
    from directory: `DATADIR/name/version` where ``DATADIR`` is in ``pydax.get_config().DATADIR``. ``DATADIR`` can
    be changed by calling :func:`pydax.init()`.

    :param name: Name of the dataset you want to load from PyDAX's available datasets. You can get a list of these
        datasets by calling :func:`pydax.list_all_datasets`.
    :param version: Version of the dataset to load. Latest version is used by default. You can get a list of all
        available versions for a dataset by calling :func:`pydax.list_all_datasets`.
    :param download: Whether or not the dataset should be downloaded before loading.
    :param subdatasets: An iterable containing the subdatasets to load. ``None`` means all subdatasets.
    :raises FileNotFoundError: The dataset files were not previously downloaded or can't be found, and ``download`` is
        False.
    :return: Dictionary that holds all subdatasets.

    Example load:

    >>> data = load_dataset('noaa_jfk')
    >>> assert('jfk_weather_cleaned' in data)
    """

    schema = export_schemata().schemata['datasets'].export_schema('datasets', name, version)

    data_dir = get_config().DATADIR / name / version
    dataset = Dataset(schema=schema, data_dir=data_dir, mode=Dataset.InitializationMode.LAZY)
    if download and not dataset.is_downloaded():
        dataset.download()
    try:
        dataset.load(subdatasets=subdatasets)
    except FileNotFoundError as e:
        raise FileNotFoundError('Failed to load the dataset because some files are not found. '
                                'Did you forget to download the dataset (by specifying `download=True`)?'
                                f'\nCaused by:\n{e}')

    return dataset.data


@_handle_name_param
@_handle_version_param
def get_dataset_metadata(name: str, *,
                         version: str = 'latest',
                         human: bool = True) -> Union[str, SchemaDict]:
    """Return a dataset's metadata either in human-readable form or as a copy of its schema.

    :param name: Name of the dataset you want get the metadata of. You can get a list of these
        datasets by calling :func:`pydax.list_all_datasets`.
    :param version: Version of the dataset to load. Latest version is used by default. You can get a list of all
        available versions for a dataset by calling :func:`pydax.list_all_datasets`.
    :param human: Whether to return the metadata as a string in human-readable form or to return a copy of the
        dataset's schema. Defaults to True.
    :return: Return a dataset's metadata either as a string or as a schema dictionary.

    Example get_dataset_metadata as string:

    >>> metadata = get_dataset_metadata('gmb')
    >>> print(metadata)  # doctest:+ELLIPSIS
    Dataset name: Groningen Meaning Bank Modified
    Description: A dataset of multi-sentence texts, together with annotations for parts-of-speech...
    Size: 10M
    Published date: 2019-12-19
    License: Community Data License Agreement – Sharing, Version 1.0 (CDLA-Sharing-1.0)
    Available subdatasets: gmb_subset_full

    Example get_dataset_metadata as dict

    >>> import pprint
    >>> metadata = get_dataset_metadata('gmb', human=False)
    >>> metadata['name']
    'Groningen Meaning Bank Modified'
    >>> metadata['description']  # doctest:+ELLIPSIS
    'A dataset of multi-sentence texts, together with annotations for parts-of-speech...
    >>> pprint.pprint(metadata['subdatasets'])
    {'gmb_subset_full': {'description': 'A full version of the raw dataset. Used '
                                        'to train MAX model – Named Entity Tagger.',
                         'format': 'txt',
                         'name': 'GMB Subset Full',
                         'path': 'groningen_meaning_bank_modified/gmb_subset_full.txt'}}
    """

    schema_manager = export_schemata()
    dataset_schema = schema_manager.schemata['datasets'].export_schema('datasets', name, version)
    license_schema = schema_manager.schemata['licenses'].export_schema('licenses')
    if human:
        return (f'Dataset name: {dataset_schema["name"]}\n'
                f'Description: {dataset_schema["description"]}\n'
                f'Size: {dataset_schema["estimated_size"]}\n'
                f'Published date: {dataset_schema["published"]}\n'
                f'License: {license_schema[dataset_schema["license"]]["name"]}\n'
                f'Available subdatasets: {", ".join(dataset_schema["subdatasets"].keys())}')
    else:
        return dataset_schema


def export_schemata() -> SchemaManager:
    "Return a copy of the ``SchemaManager`` object managed by high-level functions."

    return deepcopy(_get_schemata())


def load_schemata(*, force_reload: bool = False) -> None:
    """Loads a :class:`SchemaManager` object that stores all schemata. To export the loaded :class:`SchemaManager`
    object, please use :func:`.export_schemata`.

    :param force_reload: If ``True``, force reloading even if the provided URLs by :func:`pydax.init` are the same as
         provided last time. Otherwise, only those that are different from previous given ones are reloaded.
    """
    urls = {
        'datasets': get_config().DATASET_SCHEMA_URL,
        'formats': get_config().FORMAT_SCHEMA_URL,
        'licenses': get_config().LICENSE_SCHEMA_URL
    }

    global _schemata
    if force_reload or _schemata is None:  # Force reload or clean slate, create a new SchemaManager object
        _schemata = SchemaManager(**{name: Schema(url) for name, url in urls.items()})
    else:
        for name, schema in _schemata.schemata.items():
            if schema.retrieved_url_or_path != urls[name]:
                _schemata.add_schema(name, Schema(urls[name]))


def _get_schemata() -> SchemaManager:
    """Return the :class:`SchemaManager` object managed by high-level functions. If it is not created, create it. This
    function is used by high-level APIs but it should not be a high-level function itself. It should only be used
    internally when the need to modify the managed :class`SchemaManager` object arises. It should not be exposed for the
    same reason: users should not have this easy access to modify the managed :class`SchemaManager` object."""

    global _schemata

    load_schemata()

    # The return value is guranteed to be SchemaManager instead of Optional[SchemaManager] after load_schemata
    return _schemata  # type: ignore [return-value]
