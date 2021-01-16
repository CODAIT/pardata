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

"High-level functions tailored for new users to quickly get started with PyDAX for common tasks."


# We don't use __all__ in this file because having every exposed function shown in __init__.py is more clear.

from copy import deepcopy
import dataclasses
import functools
from textwrap import dedent
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, TypeVar, Union, cast
from packaging.version import parse as version_parser

from ._config import Config
from ._dataset import Dataset
from . import typing as typing_
from ._schema import Schema, SchemaDict, SchemaManager

# Global configurations --------------------------------------------------

_global_config: Config


def get_config() -> Config:
    """Returns global PyDAX configs.

    :return: Read-only global configs represented as a data class

    Example:

    >>> get_config()
    Config(DATASET_SCHEMA_URL=..., FORMAT_SCHEMA_URL=..., LICENSE_SCHEMA_URL=..., DATADIR=...)
    """
    return _global_config


# The SchemaManager object that is managed by high-level functions
_schemata: Optional[SchemaManager] = None


def init(update_only: bool = True, **kwargs: Any) -> None:
    """
    (Re-)initialize high-level functions and their configurations.

    :param update_only: If ``True``, only update in the global configs what config is specified; reuse schemata loaded
        by high-level functions if URLs do not change. Otherwise, reset everything to default in global configs except
        those specified as keyword arguments; clear all schemata loaded by high-level functions.
    :param DATASET_SCHEMA_URL: The default dataset schema file URL.
    :param FORMAT_SCHEMA_URL: The default format schema file URL.
    :param LICENSE_SCHEMA_URL: The default license schema file URL.
    :param DATADIR: Default dataset directory to download/load to/from. The path can be either absolute or relative to
        the current working directory, but will be converted to the absolute path immediately in this function.
        Defaults to: :file:`~/.pydax/data`.
    """
    global _global_config, _schemata

    if update_only:
        # We don't use dataclasses.replace here because it is uncertain whether it would work well with
        # pydantic.dataclasses.
        prev = dataclasses.asdict(_global_config)
        prev.update(kwargs)
        _global_config = Config(**prev)
    else:
        _global_config = Config(**kwargs)
        _schemata = None


init(update_only=False)

# Dataset --------------------------------------------------


def list_all_datasets() -> Dict[str, Tuple]:
    """Show all available pydax datasets and their versions.

    :return: Mapping of available datasets and their versions.

    Example:

    >>> import pprint
    >>> datasets = list_all_datasets()
    >>> pprint.pprint(datasets)
    {...'gmb': ('1.0.2',),... 'wikitext103': ('1.0.1',)...}
    """

    dataset_schema = export_schemata().schemata['datasets'].export_schema('datasets')
    return {
        outer_k: tuple(inner_k for inner_k, inner_v in outer_v.items())
        for outer_k, outer_v in dataset_schema.items()
    }


# We would like to be more specific about what this function does and avoid using "cast", but this seems to be the best
# we can do at this moment: It at least preserves all type hints of the decorated functions. When callback protocols
# come out, we may be able to make improvements over this part:
# https://mypy.readthedocs.io/en/stable/protocols.html#callback-protocols
_DecoratedFuncType = TypeVar("_DecoratedFuncType", bound=Callable)


def _handle_name_param(func: _DecoratedFuncType) -> _DecoratedFuncType:
    """Decorator for handling ``name`` parameter.

    :raises TypeError: ``name`` is not a string.
    :raises KeyError: ``name`` is not a valid PyDAX dataset name.
    :return: Wrapped function that handles ``name`` parameter properly.
    """
    @functools.wraps(func)
    def name_wrapper(name: str, *args: Any, **kwargs: Any) -> Any:

        if not isinstance(name, str):
            raise TypeError('The name parameter must be supplied a str.')
        all_datasets = list_all_datasets()
        if name not in all_datasets.keys():
            raise KeyError(f'"{name}" is not a valid PyDAX dataset. You can view all valid datasets and their versions '
                           'by running the function pydax.list_all_datasets().')
        return func(name, *args, **kwargs)
    return cast(_DecoratedFuncType, name_wrapper)


def _handle_version_param(func: _DecoratedFuncType) -> _DecoratedFuncType:
    """Decorator for handling ``version`` parameter. Must still be supplied a dataset ``name``.

    :raises TypeError: ``version`` is not a string.
    :raises KeyError: ``version`` is not a valid PyDAX version of ``name``.
    :return: Wrapped function that handles ``version`` parameter properly.
    """
    @functools.wraps(func)
    def version_wrapper(name: str, version: str = 'latest', *args: Any, **kwargs: Any) -> Any:

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
    return cast(_DecoratedFuncType, version_wrapper)


@_handle_name_param
@_handle_version_param
def load_dataset(name: str, *,
                 version: str = 'latest',
                 download: bool = True,
                 subdatasets: Union[Iterable[str], None] = None) -> Dict[str, Any]:
    """High level function that wraps :class:`dataset.Dataset` class's load and download functionality. Downloads to
    and loads from directory: :file:`DATADIR/name/version` where ``DATADIR`` is in ``pydax.get_config().DATADIR``.
    ``DATADIR`` can be changed by calling :func:`init`.

    :param name: Name of the dataset you want to load from PyDAX's available datasets. You can get a list of these
        datasets by calling :func:`list_all_datasets`.
    :param version: Version of the dataset to load. Latest version is used by default. You can get a list of all
        available versions for a dataset by calling :func:`list_all_datasets`.
    :param download: Whether or not the dataset should be downloaded before loading.
    :param subdatasets: An iterable containing the subdatasets to load. ``None`` means all subdatasets.
    :raises FileNotFoundError: The dataset files were not previously downloaded or can't be found, and ``download`` is
        ``False``.
    :return: Dictionary that holds all subdatasets.

    Example:

    >>> data = load_dataset('noaa_jfk')
    >>> data['jfk_weather_cleaned'][['DATE', 'HOURLYVISIBILITY', 'HOURLYDRYBULBTEMPF']].head(3)
                     DATE  HOURLYVISIBILITY  HOURLYDRYBULBTEMPF
    0 2010-01-01 01:00:00               6.0                33.0
    1 2010-01-01 02:00:00               6.0                33.0
    2 2010-01-01 03:00:00               5.0                33.0
    """

    schema = export_schemata().schemata['datasets'].export_schema('datasets', name, version)

    data_dir = get_config().DATADIR / name / version
    dataset = Dataset(schema=schema, data_dir=data_dir, mode=Dataset.InitializationMode.LAZY)
    if download and not dataset.is_downloaded():
        dataset.download()
    try:
        return dataset.load(subdatasets=subdatasets)
    except RuntimeError as e:
        raise RuntimeError('Failed to load the dataset because some files are not found. '
                           'Did you forget to download the dataset (by specifying `download=True`)?'
                           f'\nCaused by:\n{e}')


@_handle_name_param
@_handle_version_param
def get_dataset_metadata(name: str, *, version: str = 'latest') -> SchemaDict:
    """Return a dataset's metadata either in human-readable form or as a copy of its schema.

    :param name: Name of the dataset you want get the metadata of. You can get a list of these
        datasets by calling :func:`list_all_datasets`.
    :param version: Version of the dataset to load. Latest version is used by default. You can get a list of all
        available versions for a dataset by calling :func:`list_all_datasets`.
    :return: A dataset's metadata.

    Example:

    >>> import pprint
    >>> metadata = get_dataset_metadata('gmb')
    >>> metadata['name']
    'Groningen Meaning Bank Modified'
    >>> metadata['description']
    'A dataset of multi-sentence texts, together with annotations for parts-of-speech...
    >>> pprint.pprint(metadata['subdatasets'])
    {'gmb_subset_full': {'description': 'A full version of the raw dataset. Used '
                                        'to train MAX model – Named Entity Tagger.',
                         'format': 'txt',
                         'name': 'GMB Subset Full',
                         'path': 'groningen_meaning_bank_modified/gmb_subset_full.txt'}}
    """

    return export_schemata().schemata['datasets'].export_schema('datasets', name, version)


@_handle_name_param
@_handle_version_param
def describe_dataset(name: str, *, version: str = 'latest') -> str:
    """Describe a dataset's metadata in human language. Parameters mean the same as :func:`.get_dataset_metadata`.

    :param name: Name of the dataset you want get the metadata of. You can get a list of these datasets by calling
        :func:`list_all_datasets`.
    :param version: Version of the dataset to load. Latest version is used by default. You can get a list of all
        available versions for a dataset by calling :func:`list_all_datasets`.
    :return: The description.

    Example:

    >>> print(describe_dataset('gmb'))
    Dataset name: Groningen Meaning Bank Modified
    Description: A dataset of multi-sentence texts, ...
    Size: 10M
    Published date: 2019-12-19
    License: Community Data License Agreement – Sharing, Version 1.0 (CDLA-Sharing-1.0)
    Available subdatasets: gmb_subset_full
    """

    schema_manager = export_schemata()
    dataset_schema = schema_manager.schemata['datasets'].export_schema('datasets', name, version)
    license_schema = schema_manager.schemata['licenses'].export_schema('licenses')
    return dedent(f'''
            Dataset name: {dataset_schema["name"]}
            Description: {dataset_schema["description"]}
            Size: {dataset_schema["estimated_size"]}
            Published date: {dataset_schema["published"]}
            License: {license_schema[dataset_schema["license"]]["name"]}
            Available subdatasets: {", ".join(dataset_schema["subdatasets"].keys())}
    ''').strip()


# Schemata --------------------------------------------------


def export_schemata() -> SchemaManager:
    """Return a copy of the :class:`schema.SchemaManager` object managed by high-level functions.

    :return: A copy of the :class:`schema.SchemaManager` object

    Example:

    >>> schema_manager = export_schemata()
    >>> schema_manager.schemata
    {'datasets': ..., 'formats': ..., 'licenses':...}
    """

    return deepcopy(_get_schemata())


def load_schemata(*, force_reload: bool = False, tls_verification: Union[bool, typing_.PathLike] = True) -> None:
    """Loads a :class:`schema.SchemaManager` object that stores all schemata. To export the loaded
    :class:`schema.SchemaManager` object, please use :func:`export_schemata`.

    :param force_reload: If ``True``, force reloading even if the provided URLs by :func:`init` are the same as
         provided last time. Otherwise, only those that are different from previous given ones are reloaded.
    :param tls_verification: Same as ``tls_verification`` in :class:`schema.Schema`.
    :raises ValueError: See :class:`schema.Schema`.
    :raises InsecureConnectionError: See :class:`schema.Schema`.

    Example:
    >>> load_schemata()
    >>> loaded_schemata = export_schemata()
    >>> loaded_schemata.schemata
    {'datasets': ..., 'formats': ..., 'licenses':...}
    """

    urls = {
        'datasets': get_config().DATASET_SCHEMA_URL,
        'formats': get_config().FORMAT_SCHEMA_URL,
        'licenses': get_config().LICENSE_SCHEMA_URL
    }

    global _schemata
    if force_reload or _schemata is None:  # Force reload or clean slate, create a new SchemaManager object
        _schemata = SchemaManager(**{
            name: Schema(url, tls_verification=tls_verification) for name, url in urls.items()})
    else:
        for name, schema in _schemata.schemata.items():
            if schema.retrieved_url_or_path != urls[name]:
                _schemata.add_schema(name, Schema(urls[name], tls_verification=tls_verification))


def _get_schemata() -> SchemaManager:
    """Return the :class:`SchemaManager` object managed by high-level functions. If it is not created, create it. This
    function is used by high-level APIs but it should not be a high-level function itself. It should only be used
    internally when the need to modify the managed :class`SchemaManager` object arises. It should not be exposed for the
    same reason: users should not have this easy access to modify the managed :class`SchemaManager` object."""

    global _schemata

    load_schemata()

    # The return value is guranteed to be SchemaManager instead of Optional[SchemaManager] after load_schemata
    assert _schemata is not None  # nosec: We use assertion for code clarity and mypy detection of _schemata's type

    return _schemata
