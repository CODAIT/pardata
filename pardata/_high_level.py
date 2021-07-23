#
# Copyright 2020--2021 IBM Corp. All Rights Reserved.
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

"High-level functions tailored for new users to quickly get started with ParData for common tasks."


# We don't use __all__ in this file because having every exposed function shown in __init__.py is more clear.

from collections import namedtuple
from copy import deepcopy
import dataclasses
import functools
import hashlib
from textwrap import dedent
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, TypeVar, Union, cast
import os
from packaging.version import parse as version_parser
import re

from ._config import Config
from ._dataset import Dataset
from . import typing as typing_
from ._schema import (DatasetSchemaCollection, FormatSchemaCollection, LicenseSchemaCollection,
                      SchemaDict, SchemaCollectionManager)
from ._schema_retrieval import is_url

# Global configurations --------------------------------------------------

_global_config: Config


def get_config() -> Config:
    """Returns global ParData configs.

    :return: Read-only global configs represented as a data class

    Example:

    >>> get_config()
    Config(DATASET_SCHEMA_FILE_URL=..., FORMAT_SCHEMA_FILE_URL=..., LICENSE_SCHEMA_FILE_URL=..., DATADIR=...)
    """
    return _global_config


# The SchemaCollectionManager object that is managed by high-level functions
_schema_collection_manager: Optional[SchemaCollectionManager] = None


def init(update_only: bool = True, **kwargs: Any) -> None:
    """
    (Re-)initialize high-level functions and their configurations.

    :param update_only: If ``True``, only update in the global configs what config is specified; reuse schemata loaded
        by high-level functions if URLs do not change. Otherwise, reset everything to default in global configs except
        those specified as keyword arguments; clear all schemata loaded by high-level functions.
    :param DATASET_SCHEMA_FILE_URL: The default dataset schema file URL.
    :param FORMAT_SCHEMA_FILE_URL: The default format schema file URL.
    :param LICENSE_SCHEMA_FILE_URL: The default license schema file URL.
    :param DATADIR: Default dataset directory to download/load to/from. The path can be either absolute or relative to
        the current working directory, but will be converted to the absolute path immediately in this function.
        Defaults to: :file:`~/.pardata/data`.
    """
    global _global_config, _schema_collection_manager

    if update_only:
        # We don't use dataclasses.replace here because it is uncertain whether it would work well with
        # pydantic.dataclasses.
        prev = dataclasses.asdict(_global_config)
        prev.update(kwargs)
        _global_config = Config(**prev)
    else:
        _global_config = Config(**kwargs)
        _schema_collection_manager = None


init(update_only=False)

# Dataset --------------------------------------------------


def list_all_datasets() -> Dict[str, Tuple]:
    """Show all available pardata datasets and their versions.

    :return: Mapping of available datasets and their versions.

    Example:

    >>> import pprint
    >>> datasets = list_all_datasets()
    >>> pprint.pprint(datasets)
    {...'gmb': ('1.0.2',),... 'wikitext103': ('1.0.1',)...}
    """

    dataset_schema = export_schema_collections().schema_collections['datasets'].export_schema('datasets')
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
    :raises KeyError: ``name`` is not a valid ParData dataset name.
    :return: Wrapped function that handles ``name`` parameter properly.
    """
    @functools.wraps(func)
    def name_wrapper(name: str, *args: Any, **kwargs: Any) -> Any:

        if not isinstance(name, str):
            raise TypeError('The name parameter must be supplied a str.')
        all_datasets = list_all_datasets()
        if name not in all_datasets.keys():
            raise KeyError(f'"{name}" is not a valid ParData dataset. '
                           'You can view all valid datasets and their versions '
                           'by running the function pardata.list_all_datasets().')
        return func(name, *args, **kwargs)
    return cast(_DecoratedFuncType, name_wrapper)


def _handle_version_param(func: _DecoratedFuncType) -> _DecoratedFuncType:
    """Decorator for handling ``version`` parameter. Must still be supplied a dataset ``name``.

    :raises TypeError: ``version`` is not a string.
    :raises KeyError: ``version`` is not a valid ParData version of ``name``.
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
            raise KeyError(f'"{version}" is not a valid ParData version for the dataset "{name}". You can view all '
                           'valid datasets and their versions by running the function pardata.list_all_datasets().')
        return func(name=name, version=version, *args, **kwargs)
    return cast(_DecoratedFuncType, version_wrapper)


@_handle_name_param
@_handle_version_param
def load_dataset(name: str, *,
                 version: str = 'latest',
                 download: bool = True,
                 subdatasets: Union[Iterable[str], None] = None) -> Dict[str, Any]:
    """High level function that wraps :class:`dataset.Dataset` class's load and download functionality. Downloads to and
    loads from directory: :file:`DATADIR/schema_name/name/version` where ``DATADIR`` is in
    ``pardata.get_config().DATADIR``. ``DATADIR`` can be changed by calling :func:`init`.

    :param name: Name of the dataset you want to load from ParData's available datasets. You can get a list of these
        datasets by calling :func:`list_all_datasets`.
    :param version: Version of the dataset to load. Latest version is used by default. You can get a list of all
        available versions for a dataset by calling :func:`list_all_datasets`.
    :param download: Whether or not the dataset should be downloaded before loading. This is useful in avoiding
        redownloading a large dataset once it has been downloaded once. If the dataset has never been downloaded before,
        this function raises a :class:`RuntimeError`.
    :param subdatasets: An iterable containing the subdatasets to load. ``None`` means all subdatasets.
    :raises RuntimeError: The dataset files can't be found or are corrupted. One possible cause for this is that the
        dataset files have never been downloaded but ``download`` is ``False``. See :meth:`Dataset.load` for more
        details.
    :return: Dictionary that holds all subdatasets.

    Example:

    >>> data = load_dataset('noaa_jfk')
    >>> data['jfk_weather_cleaned'][['DATE', 'HOURLYVISIBILITY', 'HOURLYDRYBULBTEMPF']].head(3)
                     DATE  HOURLYVISIBILITY  HOURLYDRYBULBTEMPF
    0 2010-01-01 01:00:00               6.0                33.0
    1 2010-01-01 02:00:00               6.0                33.0
    2 2010-01-01 03:00:00               5.0                33.0
    """

    schema_collection = export_schema_collections().schema_collections['datasets']
    schema = schema_collection.export_schema('datasets', name, version)
    dataset_schema_name = schema_collection.export_schema().get('name', 'default')

    data_dir = get_config().DATADIR / dataset_schema_name / name / version
    dataset = Dataset(schema=schema, data_dir=data_dir, mode=Dataset.InitializationMode.LAZY)
    if download and not dataset.is_downloaded():
        dataset.download()
    try:
        return dataset.load(subdatasets=subdatasets)
    except RuntimeError as e:
        raise RuntimeError(
            'Failed to load the dataset. This may be caused by missing dataset files or file corruption.\n'
            'Did you forget to download the dataset (by calling this function with `download=True` for at least once)?'
            f'\nCaused by:\n{e}')


def load_dataset_from_location(url_or_path: Union[str, typing_.PathLike], *,
                               schema: Optional[SchemaDict] = None,
                               force_redownload: bool = False) -> Dict[str, Any]:
    """ Load the dataset from ``url_or_path``. This function is equivalent to calling :class:`~pardata.Dataset`, where
    ``schema['download_url']`` is set to ``url_or_path``. In the returned :class:`dict` object, keys corresponding to
    empty values are removed (unlike :meth:`~pardata.Dataset.load`).

    :param url_or_path: The URL or path of the dataset archive.
    :param schema: The schema used for loading the dataset. If ``None``, it is set to a default schema that is designed
         to accommodate most common use cases.
    :param force_redownload: ``True`` if to force redownloading the dataset.
    :return: A dictionary that holds the dataset. It is structured the same as the return value of :func:`load_dataset`.
    """

    if not is_url(str(url_or_path)):
        url_or_path = os.path.abspath(url_or_path)  # Don't use pathlib.Path.resolve because it resolves symlinks
    url_or_path = cast(str, url_or_path)

    # Name of the data dir: {url_or_path with non-alphanums replaced by dashes}-sha512. The sha512 suffix is there to
    # prevent collision.
    data_dir_name = (f'{re.sub("[^0-9a-zA-Z]+", "-", url_or_path)}-'
                     f'{hashlib.sha512(url_or_path.encode("utf-8")).hexdigest()}')
    data_dir = get_config().DATADIR / '_location_direct' / data_dir_name
    if schema is None:
        # Construct the default schema
        schema = {
            'name': 'Direct from a location',
            'description': 'Loaded directly from a location',
            'subdatasets': {
            }
        }

        RegexFormatPair = namedtuple('RegexFormatPair', ['regex', 'format'])
        regex_format_pairs = (
            RegexFormatPair(regex=r'.*\.csv', format='table/csv'),
            RegexFormatPair(regex=r'.*\.wav', format='audio/wav'),
            RegexFormatPair(regex=r'.*\.(txt|log)', format='text/plain'),
            RegexFormatPair(regex=r'.*\.(jpg|jpeg)', format='image/jpeg'),
            RegexFormatPair(regex=r'.*\.png', format='image/png'),
        )

        for regex_format_pair in regex_format_pairs:
            schema['subdatasets'][regex_format_pair.format] = {
                'format': {
                    'id': regex_format_pair.format,
                },
                'path': {
                    'type': 'regex',
                    'value': regex_format_pair.regex
                }
            }
    schema['download_url'] = url_or_path

    dataset = Dataset(schema=schema, data_dir=data_dir, mode=Dataset.InitializationMode.LAZY)
    if force_redownload or not dataset.is_downloaded():
        dataset.download(check=False,  # Already checked by `is_downloaded` call above
                         verify_checksum=False)
    dataset.load()

    # strip empty values
    return {k: v for k, v in dataset.data.items() if len(v) > 0}


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
                         'format': 'text/plain',
                         'name': 'GMB Subset Full',
                         'path': 'groningen_meaning_bank_modified/gmb_subset_full.txt'}}
    """

    return export_schema_collections().schema_collections['datasets'].export_schema('datasets', name, version)


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
    Homepage: https://developer.ibm.com/exchanges/data/all/groningen-meaning-bank/
    Description: A dataset of multi-sentence texts, ...
    Size: 10M
    Published date: 2019-12-19
    License: Community Data License Agreement – Sharing, Version 1.0 (CDLA-Sharing-1.0)
    Available subdatasets: gmb_subset_full
    """

    schema_manager = export_schema_collections()
    dataset_schema = schema_manager.schema_collections['datasets'].export_schema('datasets', name, version)
    license_schema_collection = cast(LicenseSchemaCollection, schema_manager.schema_collections['licenses'])
    return dedent(f'''
            Dataset name: {dataset_schema["name"]}
            Homepage: {dataset_schema["homepage"]}
            Description: {dataset_schema["description"]}
            Size: {dataset_schema["estimated_size"]}
            Published date: {dataset_schema["published"]}
            License: {license_schema_collection.get_license_name(dataset_schema["license"])}
            Available subdatasets: {", ".join(dataset_schema["subdatasets"].keys())}
    ''').strip()


# Schemata --------------------------------------------------


def export_schema_collections() -> SchemaCollectionManager:
    """Return a copy of the :class:`schema.SchemaCollectionManager` object managed by high-level functions.

    :return: A copy of the :class:`schema.SchemaCollectionManager` object

    Example:

    >>> schema_manager = export_schema_collections()
    >>> schema_manager.schema_collections
    {'datasets': ..., 'formats': ..., 'licenses':...}
    """

    return deepcopy(_get_schema_collections())


def load_schema_collections(*,
                            force_reload: bool = False,
                            tls_verification: Union[bool, typing_.PathLike] = True) -> None:
    """Loads a :class:`schema.SchemaCollectionManager` object that stores all schema collections. To export the loaded
    :class:`schema.SchemaCollectionManager` object, please use :func:`export_schema_collections`.

    :param force_reload: If ``True``, force reloading even if the provided URLs by :func:`init` are the same as
         provided last time. Otherwise, only those that are different from previous given ones are reloaded.
    :param tls_verification: Same as ``tls_verification`` in :class:`schema.SchemaCollection`.
    :raises ValueError: See :class:`schema.SchemaCollection`.
    :raises InsecureConnectionError: See :class:`schema.SchemaCollection`.

    Example:
    >>> load_schema_collections()
    >>> loaded_schemata = export_schema_collections()
    >>> loaded_schemata.schema_collections
    {'datasets': ..., 'formats': ..., 'licenses':...}
    """

    SchemaCollectionInfo = namedtuple('SchemaCollectionInfo', ['url', 'type_'])
    infos = {
        'datasets': SchemaCollectionInfo(url=get_config().DATASET_SCHEMA_FILE_URL, type_=DatasetSchemaCollection),
        'formats': SchemaCollectionInfo(url=get_config().FORMAT_SCHEMA_FILE_URL, type_=FormatSchemaCollection),
        'licenses': SchemaCollectionInfo(url=get_config().LICENSE_SCHEMA_FILE_URL, type_=LicenseSchemaCollection),
    }

    global _schema_collection_manager
    if force_reload or _schema_collection_manager is None:
        # Force reload or clean slate, create a new SchemaCollectionManager object

        _schema_collection_manager = SchemaCollectionManager(**{
            name: info.type_(info.url, tls_verification=tls_verification) for name, info in infos.items()})
    else:
        for name, schema in _schema_collection_manager.schema_collections.items():
            info = infos[name]
            if schema.retrieved_url_or_path != info.url:
                _schema_collection_manager.add_schema_collection(
                    name, info.type_(info.url, tls_verification=tls_verification))


def _get_schema_collections() -> SchemaCollectionManager:
    """Return the :class:`SchemaCollectionManager` object managed by high-level functions. If it is not created, create
    it. This function is used by high-level APIs but it should not be a high-level function itself. It should only be
    used internally when the need to modify the managed :class`SchemaCollectionManager` object arises. It should not be
    exposed for the same reason: users should not have this easy access to modify the managed
    :class`SchemaCollectionManager` object."""

    global _schema_collection_manager

    load_schema_collections()

    # The return value is guaranteed to be SchemaCollectionManager instead of Optional[SchemaCollectionManager] after
    # load_schema_collections
    assert _schema_collection_manager is not None  # nosec: We use assertion for code clarity

    return _schema_collection_manager
