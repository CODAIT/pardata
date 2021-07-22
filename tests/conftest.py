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

import copy
import hashlib
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
from pathlib import Path
import requests
import shutil
from ssl import PROTOCOL_TLS_SERVER, SSLContext
import tarfile
from tempfile import TemporaryDirectory
import threading
from typing import Callable
from urllib.request import urlretrieve
import uuid

import certifi
import pytest

from pardata import init
from pardata._high_level import _get_schema_collections
from pardata.dataset import Dataset
from pardata.schema import (DatasetSchemaCollection, FormatSchemaCollection, LicenseSchemaCollection,
                            SchemaDict, SchemaCollectionManager)

# Basic utilities --------------------------------


@pytest.fixture
def tmp_sub_dir(tmp_path):
    "A ``pathlib.Path`` object that points to a temporary dir, created as a subdir of ``tmp_path``."

    with TemporaryDirectory(dir=tmp_path) as d:
        yield Path(d).absolute()


@pytest.fixture
def tmp_relative_sub_dir(tmp_path, tmp_sub_dir):
    """The path of ``tmp_sub_dir`` relative to ``tmp_dir``. This can be useful (in conjunction with ``chdir_tmp_path``)
    for some tests that focus on an absolute path vis-a-vis its relative path form. In these tests, the use of
    ``os.path.relpath()`` is discouraged, because it would fail if the input is on a different drive from the working
    directory on Windows. Instead, use `tmp_sub_dir` and ``tmp_relative_sub_dir``."""

    return tmp_sub_dir.relative_to(tmp_path)


@pytest.fixture
def tmp_symlink_dir(tmp_path, tmp_sub_dir):
    "A ``pathlib.Path`` object that points to a temporary symlink to ``tmp_sub_dir``. It always sits in ``tmp_dir``."

    while True:
        symlink_dir = tmp_path / str(uuid.uuid4())
        # A collision is extremely unlikely, but for the sake of completeness, this check never hurts.
        if not symlink_dir.exists():
            break

    symlink_dir.symlink_to(tmp_sub_dir, target_is_directory=True)

    yield symlink_dir

    symlink_dir.unlink()


@pytest.fixture
def chdir_tmp_path(tmp_path):
    "Make the test run in ``tmp_path`` as the current working directory."

    cur_dir = Path.cwd()
    os.chdir(tmp_path)
    yield
    os.chdir(cur_dir)


@pytest.fixture(scope='session')
def local_http_server() -> HTTPServer:
    "A local http server that serves the source directory."

    with HTTPServer(("localhost", 8080), SimpleHTTPRequestHandler) as httpd:
        # Start a new thread, because httpd.serve_forever is blocking
        threading.Thread(target=httpd.serve_forever, name='Local Http Server', daemon=True).start()
        yield httpd
        httpd.shutdown()


@pytest.fixture(scope='session')
def local_http_server_root_url(local_http_server) -> str:
    "Root URL of the local http server."

    return f'http://{local_http_server.server_address[0]}:{local_http_server.server_address[1]}'


@pytest.fixture(scope='session')
def local_https_server() -> HTTPServer:
    "A local https server that serves the source directory."

    # Merge certifi's CA bundle (used as default by requests) with ours. This is done by a simple concatenation of the
    # two pem files. Although pem files are text files, we treat them as binaries to avoid unexpected EOL conversions.
    ca_bundle = Path('tests/tls/test_ca_bundle.pem')
    ca_bundle.write_bytes(
        Path(certifi.where()).read_bytes() + Path('tests/tls/server.pem').read_bytes())
    os.environ['REQUESTS_CA_BUNDLE'] = str(ca_bundle)
    # Ensure CURL_CA_BUNDLE isn't involved
    os.environ.pop('CURL_CA_BUNDLE', None)

    with HTTPServer(("localhost", 8081), SimpleHTTPRequestHandler) as httpd:
        context = SSLContext(PROTOCOL_TLS_SERVER)
        context.load_cert_chain('tests/tls/server.pem', keyfile='tests/tls/server.key')
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        # Start a new thread, because httpd.serve_forever is blocking
        threading.Thread(target=httpd.serve_forever, name='Local Https Server', daemon=True).start()
        yield httpd
        httpd.shutdown()


@pytest.fixture(scope='session')
def local_https_server_root_url(local_https_server) -> str:
    "Root URL of the local https server."

    return f'https://{local_https_server.server_address[0]}:{local_https_server.server_address[1]}'


@pytest.fixture
def untrust_self_signed_cert(local_https_server):
    # local_https_server is here to ensure that environment variables have been initialized
    """Untrust our self signed TLS certificate of our test local HTTPS server, and let requests uses the default trusted
    CA bundle."""
    self_signed = os.environ.pop('REQUESTS_CA_BUNDLE')
    yield
    os.environ['REQUESTS_CA_BUNDLE'] = self_signed


@pytest.fixture(autouse=True)
def pardata_initialization(schema_file_https_url, schema_localized_url):
    """Create the default initialization used for all tests. This is mainly for having a uniform initialization for all
    tests as well as avoiding using the actual default schema file URLs so as to decouple the two lines of development
    (default schema files and this library). It also replaces all download URLs with localized URLs."""

    init(update_only=False,
         DATASET_SCHEMA_FILE_URL=f'{schema_file_https_url}/datasets.yaml',
         FORMAT_SCHEMA_FILE_URL=f'{schema_file_https_url}/formats.yaml',
         LICENSE_SCHEMA_FILE_URL=f'{schema_file_https_url}/licenses.yaml')

    # Use local dataset locations by default in our tests
    datasets = _get_schema_collections().schema_collections['datasets']._schema_collection['datasets']
    for name, versions in datasets.items():
        for version in versions:
            datasets[name][version] = schema_localized_url(name, version)

# Dataset --------------------------------------


@pytest.fixture(scope='session')
def dataset_base_url(local_https_server_root_url) -> str:
    "The base local HTTPS server URL that stores datasets for testing purposes."

    return f'{local_https_server_root_url}/tests/datasets'


@pytest.fixture(scope='session')
def dataset_dir() -> Path:
    "The directory that stores datasets for testing purposes."

    d = Path('tests/datasets')
    d.mkdir(exist_ok=True)

    return d


def _make_zip_copy(tar_path: Path, zip_path: Path):
    "Convert a tarball to a zip file."

    with TemporaryDirectory() as tmpdir:
        with tarfile.open(tar_path) as f:
            f.extractall(tmpdir)
        shutil.make_archive(base_name=zip_path.with_suffix(''), format='zip', root_dir=tmpdir)

    # Calculate sha512sum of the zip archive
    zip_path.with_name(zip_path.name + '.sha512sum').write_text(
        hashlib.sha512(zip_path.read_bytes()).hexdigest())


@pytest.fixture(scope='session')
def _download_dataset(dataset_dir, _loaded_schema_collections) -> Callable[[str], None]:
    """Utility function for downloading datasets to ``tests/datasets/{name}-{version}`` for testing purpose. These files
    will not be deleted after the test session terminates, and they are cached for future test sessions. Accordingly, if
    ``tests/datasets/{name}-{version}`` is already present, this fixture does nothing.
    """
    # We use _loaded_schemata instead of loaded_schemata to avoid scope mismatch error (a session-scoped fixture can't
    # call a function-scoped fixture)

    def _download_dataset_impl(name, version):
        # we drop the 'tar.gz' extension here -- our package should work regardless of the extension, and we allow the
        # file to be archived in a different compression format.
        local_destination = dataset_dir / f'{name}-{version}'

        schema = _loaded_schema_collections.schema_collections['datasets'].export_schema('datasets', name, version)

        if local_destination.exists() and \
           hashlib.sha512(local_destination.read_bytes()).hexdigest() == schema['sha512sum']:
            # The file has been completely downloaded before
            return

        # We use urllib instead of requests to avoid running the same code path with our downloading implementation
        urlretrieve(schema['download_url'], filename=local_destination)

        # Create a zip copy if the file size is smaller than 10M
        if local_destination.stat().st_size < 10_000_000:
            _make_zip_copy(local_destination, local_destination.parent / (local_destination.name + '.zip'))

    return _download_dataset_impl

# Schema fixtures --------------------------------------------------


@pytest.fixture(scope='session')
def schema_localized_url(_loaded_schema_collections,
                         _download_dataset, dataset_base_url) -> Callable[[str, str], SchemaDict]:
    "Utility function fixture for generating schema fixtures with its downloading URL modified to the local HTTPS URL."
    # We use _loaded_schemata instead of loaded_schemata to avoid scope mismatch error (a session-scoped fixture can't
    # call a function-scoped fixture)

    def _schema_localized_url_impl(name, version):
        _download_dataset(name, version)
        schema = _loaded_schema_collections.schema_collections['datasets'].export_schema('datasets', name, version)
        schema['download_url'] = str(f'{dataset_base_url}/{name}-{version}')
        return schema

    return _schema_localized_url_impl


@pytest.fixture(scope='session')
def _loaded_schema_collections(schema_file_relative_dir) -> SchemaCollectionManager:
    """A loaded ``SchemaCollectionManager`` object, but this should never be modified. This object manages ``Schema``
    objects corresponding to ``tests/{datasets,formats,licenses}.yaml``. Note that these are not necessarily the same as
    the ones used in other schema fixtures, so please do not assume that it is equal to other schema fixtures. One
    purpose of this fixture is to reduce repeated call in the test to the same function when ``loaded_schemata`` is
    used. The other purpose is to provide other session-scoped fixtures access to the loaded schemata, because
    session-scoped fixtures can't load function-scoped fixtures.
    """

    return SchemaCollectionManager(datasets=DatasetSchemaCollection(schema_file_relative_dir / 'datasets.yaml'),
                                   formats=FormatSchemaCollection(schema_file_relative_dir / 'formats.yaml'),
                                   licenses=LicenseSchemaCollection(schema_file_relative_dir / 'licenses.yaml'))


@pytest.fixture
def loaded_schema_collections(_loaded_schema_collections) -> SchemaCollectionManager:
    """A copy of _loaded_schema_collections. Tests outside this file should always use this one so as to avoid
    mistakenly modifying the content."""

    return copy.deepcopy(_loaded_schema_collections)


# Every _*_schema fixture also implies that a session wide test dataset file is downloaded. They should only be read
# because we want them to be session-scoped. All tests should use the fixture without a leading underscore.

# We don't create a function that automatically generates all the following fixtures because explicitly listing them
# would be easier to understand the error when a test fails.

@pytest.fixture(scope='session')
def _gmb_schema(schema_localized_url):
    return schema_localized_url('gmb', '1.0.2')


@pytest.fixture
def gmb_schema(_gmb_schema):
    return copy.deepcopy(_gmb_schema)


@pytest.fixture
def gmb_schema_zip(gmb_schema):
    "Same as ``gmb_schema``, but in zip format."

    # TODO: put this process to a generic utility function
    gmb_schema['download_url'] += '.zip'
    gmb_schema['sha512sum'] = requests.get(gmb_schema['download_url'] + '.sha512sum').text.strip()
    return gmb_schema


@pytest.fixture(scope='session')
def _noaa_jfk_schema(schema_localized_url):
    return schema_localized_url('noaa_jfk', '1.1.4')


@pytest.fixture
def noaa_jfk_schema(_noaa_jfk_schema):
    return copy.deepcopy(_noaa_jfk_schema)


@pytest.fixture(scope='session')
def _tensorflow_speech_commands_schema(schema_localized_url):
    return schema_localized_url('tensorflow_speech_commands', '1.0.1')


@pytest.fixture
def tensorflow_speech_commands_schema(_tensorflow_speech_commands_schema):
    return copy.deepcopy(_tensorflow_speech_commands_schema)


@pytest.fixture(scope='session')
def _wikitext103_schema(schema_localized_url):
    return schema_localized_url('wikitext103', '1.0.1')


@pytest.fixture
def wikitext103_schema(_wikitext103_schema):
    return copy.deepcopy(_wikitext103_schema)


# Schema file locations fixture --------------------------------------


@pytest.fixture(scope='session')
def schema_file_absolute_dir() -> Path:
    "The base of the absolute path to the dir that contains test schema files."

    return Path.cwd() / 'tests' / 'schemata'


@pytest.fixture(scope='session')
def schema_file_relative_dir() -> Path:
    "The base of the relative path to the dir that contains test schema files."

    return Path('tests/schemata')


@pytest.fixture(scope='session')
def schema_file_file_url(schema_file_absolute_dir) -> str:
    "The base of file:// schema file URLs."

    return schema_file_absolute_dir.as_uri()


@pytest.fixture(scope='session')
def schema_file_http_url(local_http_server_root_url) -> str:
    "The base of remote http:// test schema file URLs."

    return f"{local_http_server_root_url}/tests/schemata"


@pytest.fixture(scope='session')
def schema_file_https_url(local_https_server_root_url) -> str:
    "The base of remote https:// test schema file URLs."

    return f"{local_https_server_root_url}/tests/schemata"


# Downloaded datasets -------------------------------------


@pytest.fixture
def downloaded_gmb_dataset(gmb_schema) -> Dataset:
    with TemporaryDirectory() as tmp_data_dir:
        yield Dataset(gmb_schema, data_dir=tmp_data_dir, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)


@pytest.fixture
def downloaded_noaa_jfk_dataset(noaa_jfk_schema) -> Dataset:
    with TemporaryDirectory() as tmp_data_dir:
        yield Dataset(noaa_jfk_schema, data_dir=tmp_data_dir, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)


@pytest.fixture
def downloaded_tensorflow_speech_commands_dataset(tensorflow_speech_commands_schema) -> Dataset:
    with TemporaryDirectory() as tmp_data_dir:
        yield Dataset(tensorflow_speech_commands_schema, data_dir=tmp_data_dir,
                      mode=Dataset.InitializationMode.DOWNLOAD_ONLY)


@pytest.fixture
def downloaded_wikitext103_dataset(wikitext103_schema) -> Dataset:
    with TemporaryDirectory() as tmp_data_dir:
        yield Dataset(wikitext103_schema, data_dir=tmp_data_dir, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)


# Assets -------------------------------------------------

@pytest.fixture(scope='session')
def asset_dir() -> Path:
    "Path to the asset directory."

    return Path.cwd() / 'tests' / 'assets'


@pytest.fixture
def saturn_image(asset_dir) -> Path:
    "Path to the saturn.jpg."

    return asset_dir / 'saturn.jpg'


@pytest.fixture
def bell_sound(asset_dir) -> Path:
    "Path to the service-bell.wav."

    return asset_dir / 'service-bell.wav'
