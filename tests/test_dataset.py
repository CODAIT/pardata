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
import json
from json import JSONDecodeError
import os
import pathlib
import tarfile

import pandas as pd
import pytest

from pydax.dataset import Dataset
from pydax.exceptions import DirectoryLockAcquisitionError
from pydax.loaders import FormatLoaderMap
from pydax.loaders.text import PlainTextLoader


class TestDataset:
    "Test Dataset class functionality."

    def test_mode(self, tmp_path, gmb_schema):
        "Test if Dataset class catches an invalid mode."

        with pytest.raises(ValueError) as e:
            Dataset(gmb_schema, data_dir=tmp_path, mode='DOWNLOAD_ONLY')
        assert str(e.value) == 'DOWNLOAD_ONLY not a valid mode'

    def test_data_dir(self, tmp_path, gmb_schema):
        "Test ``Dataset._data_dir``."
        # Automatic creation
        dataset = Dataset(gmb_schema, data_dir=tmp_path / 'data_dir', mode=Dataset.InitializationMode.LAZY)
        assert dataset._data_dir == tmp_path / 'data_dir'

        # Non-directory present
        dataset = Dataset(gmb_schema, data_dir='setup.py', mode=Dataset.InitializationMode.LAZY)
        with pytest.raises(NotADirectoryError) as e:
            dataset._data_dir
        assert str(e.value) == f'"{pathlib.Path.cwd()/"setup.py"}" exists and is not a directory.'

    def test_pydax_dir(self, tmp_path, gmb_schema):
        "Test ``Dataset._pydax_dir``."
        # Automatic creation
        pydax_dir = tmp_path / 'data_dir' / '.pydax.dataset'
        dataset = Dataset(gmb_schema, data_dir=tmp_path / 'data_dir', mode=Dataset.InitializationMode.LAZY)
        assert dataset._pydax_dir == pydax_dir
        # Non-directory present
        pydax_dir.rmdir()
        assert pydax_dir.exists() is False
        pydax_dir.touch()
        with pytest.raises(NotADirectoryError) as e:
            dataset._pydax_dir
        assert str(e.value) == f'"{pydax_dir}" exists and is not a directory.'

        # Non-directory parent present
        dataset = Dataset(gmb_schema, data_dir='setup.py', mode=Dataset.InitializationMode.LAZY)
        # These are raised by pathlib.Path.mkdir
        # Also see https://bugs.python.org/issue42872
        ExceptionClass = FileExistsError if os.name == 'nt' else NotADirectoryError
        with pytest.raises(ExceptionClass) as e:
            dataset._pydax_dir
        # This error message may be generated by pathlib.Path.mkdir() (as in DirectoryLock.lock()). We only make sure
        # the path is in the string.
        # On Windows, backslashes in the error message are doubled:
        #
        #   "[WinError 183] Cannot create a file when that file already exists: 'D:\\\\a\\\\pydax\\\\pydax\\\\setup.py'"
        assert str(pathlib.Path.cwd() / "setup.py").replace('\\', '\\\\') in str(e.value)

    @pytest.mark.parametrize('schema', ('gmb_schema', 'gmb_schema_zip'))
    def test_dataset_download(self, tmp_path, schema, request):
        "Test Dataset class downloads a dataset properly."

        gmb_schema = request.getfixturevalue(schema)
        data_dir = tmp_path / 'gmb'
        gmb_dataset = Dataset(gmb_schema, data_dir=data_dir, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        assert len(list(data_dir.iterdir())) == 2  # 'groningen_meaning_bank_modified' and '.pydax.dataset'
        unarchived_data_dir = data_dir / 'groningen_meaning_bank_modified'
        unarchived_data_dir_files = ['gmb_subset_full.txt', 'LICENSE.txt', 'README.txt']
        assert unarchived_data_dir.is_dir()
        assert len(list(unarchived_data_dir.iterdir())) == len(unarchived_data_dir_files)
        assert all(f.name in unarchived_data_dir_files for f in unarchived_data_dir.iterdir())

        # Force check previously downloaded dataset should error
        with pytest.raises(RuntimeError) as e:
            gmb_dataset.download(check=True)
        assert str(e.value) == ('Dataset.download() was previously called. To overwrite existing data files, rerun '
                                'Dataset.download() with ``check`` set to ``False``.')

    def test_invalid_sha512(self, tmp_path, gmb_schema):
        "Test if Dataset class catches an invalid hash."

        gmb_schema['sha512sum'] = 'invalid hash example'

        with pytest.raises(IOError) as e:
            Dataset(gmb_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        assert 'the file may by corrupted' in str(e.value)

    def test_invalid_archive(self, tmp_path, gmb_schema, schema_file_https_url, schema_file_relative_dir):
        "Test if Dataset class catches an invalid archive file."

        fake_schema = gmb_schema
        fake_schema['download_url'] = schema_file_https_url + '/datasets.yaml'
        fake_schema['sha512sum'] = hashlib.sha512((schema_file_relative_dir / 'datasets.yaml').read_bytes()).hexdigest()

        with pytest.raises(RuntimeError) as e:
            Dataset(fake_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        assert 'Failed to unarchive' in str(e.value)

    def test_load(self, downloaded_wikitext103_dataset):
        "Test basic loading functionality."

        data = downloaded_wikitext103_dataset.load()
        assert data is downloaded_wikitext103_dataset.data

        assert (hashlib.sha512(data['train'].encode()).hexdigest() ==
                ('df7615f77cb9dd19975881f271e3e3525bee38c08a67fea36a51c96be69a3ecabc9e05c02cbaf'
                 '6fc63a0082efb44156f61c81061d3b0272bbccd7657c682e791'))

        assert (hashlib.sha512(data['valid'].encode()).hexdigest() ==
                ('e4834d365d5f8313503895fd8304d29a566ff4a2df77efb32457fdc353304fb61460511f89bb9'
                 '0f14a47132c1539aaa324d3e71f5f56045a61a7292ad25a3c02'))

        assert (hashlib.sha512(data['test'].encode()).hexdigest() ==
                ('6fe665d33c0f788eba76da50539f0ca02432c70c94b788a493da491215e86043fc732dbeef9bb'
                 '49a72341c7283ea55f59d10941ac41f7ac58aea3bdcd72f5cd8'))

    def test_load_format_loader_map_param(self, downloaded_noaa_jfk_dataset):
        "Test ``format_loader_map`` param in ``Dataset.load``."

        # Default
        data = downloaded_noaa_jfk_dataset.load(format_loader_map=None)
        cleaned_data = data['jfk_weather_cleaned']
        assert isinstance(cleaned_data, pd.DataFrame)

        # Load CSV using the plain text loader
        data = downloaded_noaa_jfk_dataset.load(format_loader_map=FormatLoaderMap({
            'csv': PlainTextLoader()
        }))
        cleaned_data = data['jfk_weather_cleaned']
        assert isinstance(cleaned_data, str)

    def test_constructor_download_and_load(self, tmp_path, wikitext103_schema):
        "Test the full power of Dataset.__init__() (mode being ``InitializationMode.DOWNLOAD_AND_LOAD``)."

        dataset = Dataset(wikitext103_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_AND_LOAD)

        assert (hashlib.sha512(dataset.data['train'].encode()).hexdigest() ==
                ('df7615f77cb9dd19975881f271e3e3525bee38c08a67fea36a51c96be69a3ecabc9e05c02cbaf'
                 '6fc63a0082efb44156f61c81061d3b0272bbccd7657c682e791'))

        assert (hashlib.sha512(dataset.data['valid'].encode()).hexdigest() ==
                ('e4834d365d5f8313503895fd8304d29a566ff4a2df77efb32457fdc353304fb61460511f89bb9'
                 '0f14a47132c1539aaa324d3e71f5f56045a61a7292ad25a3c02'))

        assert (hashlib.sha512(dataset.data['test'].encode()).hexdigest() ==
                ('6fe665d33c0f788eba76da50539f0ca02432c70c94b788a493da491215e86043fc732dbeef9bb'
                 '49a72341c7283ea55f59d10941ac41f7ac58aea3bdcd72f5cd8'))

    def test_loading_undownloaded(self, tmp_path, gmb_schema):
        "Test loading before ``Dataset.download()`` has been called."

        dataset = Dataset(gmb_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.LAZY)

        with pytest.raises(FileNotFoundError) as e:
            dataset.load(check=False)
        assert ('Failed to load subdataset "gmb_subset_full" because some files are not found. '
                'Did you forget to call Dataset.download()?\nCaused by:\n') in str(e.value)

        # Half-loaded data objects should get reset to None
        assert dataset._data is None
        with pytest.raises(RuntimeError) as e:
            dataset.data
        assert str(e.value) == ('Data has not been downloaded and/or loaded yet. Call Dataset.download() to download '
                                'data, call Dataset.load() to load data.')

        # Force check undownloaded dataset should error
        with pytest.raises(RuntimeError) as e:
            dataset.load(check=True)
        assert str(e.value) == (f'Downloaded data files are not present in {dataset._data_dir_} or are corrupted.')

    def test_unloaded_access_to_data(self, tmp_path, gmb_schema):
        "Test access to ``Dataset.data`` when no data has been loaded."

        dataset = Dataset(gmb_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.LAZY)
        with pytest.raises(RuntimeError) as e:
            dataset.data
        assert str(e.value) == ('Data has not been downloaded and/or loaded yet. Call Dataset.download() to download '
                                'data, call Dataset.load() to load data.')

        # Same after downloading
        dataset.download()
        with pytest.raises(RuntimeError) as e:
            dataset.data
        assert str(e.value) == ('Data has not been downloaded and/or loaded yet. Call Dataset.download() to download '
                                'data, call Dataset.load() to load data.')

    def test_deleting_data_dir(self, tmp_path, gmb_schema):
        "Test ``Dataset.delete()``."

        # Note we don't use tmp_sub_dir fixture because we want data_dir to be non-existing at the beginning of the
        # test.
        data_dir = tmp_path / 'data-dir'
        dataset = Dataset(gmb_schema, data_dir=data_dir, mode=Dataset.InitializationMode.LAZY)
        assert not data_dir.exists()  # sanity check: data_dir doesn't exist
        dataset.delete()  # no exception should be raised here
        assert not data_dir.exists()  # sanity check: data_dir doesn't exist

        dataset.download()
        # Sanity check: Files are in place
        assert dataset.is_downloaded()
        assert len(os.listdir(data_dir)) > 0
        # Delete the dir
        dataset.delete()
        assert not data_dir.exists()

    def test_download_data_dir_is_not_a_dir(self, gmb_schema):
        "Test when downloading when ``data_dir`` exists and is not a dir."

        # These are raised by pathlib.Path.mkdir
        # Also see https://bugs.python.org/issue42872
        ExceptionClass = FileExistsError if os.name == 'nt' else NotADirectoryError
        with pytest.raises(ExceptionClass) as e:
            Dataset(gmb_schema, data_dir='./setup.py', mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        # This error message may be generated by pathlib.Path.mkdir() (as in DirectoryLock.lock()). We only make sure
        # the path is in the string.
        # On Windows, backslashes in the error message are doubled:
        #
        #   "[WinError 183] Cannot create a file when that file already exists: 'D:\\\\a\\\\pydax\\\\pydax\\\\setup.py'"
        assert str(pathlib.Path.cwd() / "setup.py").replace('\\', '\\\\') in str(e.value)

    def test_relative_data_dir(self, gmb_schema, chdir_tmp_path, tmp_sub_dir, tmp_relative_sub_dir):
        "Test when ``data_dir`` is relative."

        dataset = Dataset(gmb_schema, data_dir=tmp_relative_sub_dir, mode=Dataset.InitializationMode.LAZY)
        assert dataset._data_dir == tmp_sub_dir
        assert dataset._data_dir.is_absolute()

    def test_symlink_data_dir(self, tmp_symlink_dir, gmb_schema):
        "Test when ``data_dir`` is a symlink. The symlink should not be resolved."

        dataset = Dataset(gmb_schema, data_dir=tmp_symlink_dir, mode=Dataset.InitializationMode.LAZY)
        assert dataset._data_dir == tmp_symlink_dir

    def test_is_downloaded(self, tmp_path, gmb_schema):
        "Test is_downloaded method."

        data_dir = tmp_path / 'non-existing-dir'
        assert not data_dir.exists()  # Sanity check: data_dir must not exist
        gmb = Dataset(gmb_schema, data_dir=data_dir, mode=Dataset.InitializationMode.LAZY)
        assert gmb.is_downloaded() is False

        gmb.download()
        assert gmb.is_downloaded() is True

        # content of the file list
        with open(gmb._file_list_file, mode='r') as f:
            file_list = json.load(f)

        def test_incorrect_file_list(change: dict):
            "Test a single case that somewhere in the file list things are wrong."

            wrong_file_list = copy.deepcopy(file_list)
            wrong_file_list.update(change)
            with open(gmb._file_list_file, mode='w') as f:
                json.dump(wrong_file_list, f)
            assert gmb.is_downloaded() is False

        # Can't find a file
        test_incorrect_file_list({'non-existing-file': {'type': int(tarfile.REGTYPE)}})
        # File type incorrect
        test_incorrect_file_list({'groningen_meaning_bank_modified': {'type': int(tarfile.REGTYPE)}})
        test_incorrect_file_list({'groningen_meaning_bank_modified/LICENSE.txt': {'type': int(tarfile.DIRTYPE)}})
        test_incorrect_file_list({'groningen_meaning_bank_modified/README.txt': {'type': int(tarfile.SYMTYPE)}})
        # size incorrect
        changed = copy.deepcopy(file_list['groningen_meaning_bank_modified/README.txt'])
        changed['size'] += 100
        test_incorrect_file_list({'groningen_meaning_bank_modified/README.txt': changed})

        # JSON decoding error
        gmb._file_list_file.write_text("nonsense\n", encoding='utf-8')
        with pytest.raises(JSONDecodeError):
            # We don't check the value of the exception because we clearly only are only interested in ensuring that the
            # file isn't decodable
            gmb.is_downloaded()

    def test_cache_dir_is_not_a_dir(self, tmp_path, gmb_schema):
        "Test when ``pydax_dir`` (i.e., ``data_dir/.pydax.dataset``) exists and is not a dir."
        (tmp_path / '.pydax.dataset').touch()  # Occupy this path with a regular file
        with pytest.raises(NotADirectoryError) as e:
            Dataset(gmb_schema, data_dir=tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        assert str(e.value) == f"\"{tmp_path/'.pydax.dataset'}\" exists and is not a directory."

    def _test_lock_exception(self, func, *, write, directory):
        "Helper for asserting lock exception."
        with pytest.raises(DirectoryLockAcquisitionError) as e:
            func()
        assert str(e.value) == f'Failed to acquire directory {"write" if write else "read"} lock for "{directory}"'

    def test_directory_write_lock_present(self, downloaded_gmb_dataset):
        "Test various functions when a write directory lock is present."

        lock_file = downloaded_gmb_dataset._pydax_dir_ / 'write.ding-dong.lock'
        lock_file.touch()

        f_stat = downloaded_gmb_dataset._file_list_file_.stat()
        self._test_lock_exception(
            lambda: downloaded_gmb_dataset.download(check=False),
            write=True,
            directory=downloaded_gmb_dataset._pydax_dir_)
        assert f_stat == downloaded_gmb_dataset._file_list_file_.stat()  # _file_list_file_ wasn't overwritten

        self._test_lock_exception(
            lambda: downloaded_gmb_dataset.load(), write=False, directory=downloaded_gmb_dataset._pydax_dir_)
        with pytest.raises(RuntimeError) as e:
            downloaded_gmb_dataset.data
        assert str(e.value) == ('Data has not been downloaded and/or loaded yet. Call Dataset.download() to download '
                                'data, call Dataset.load() to load data.')

        self._test_lock_exception(
            lambda: downloaded_gmb_dataset.delete(), write=True, directory=downloaded_gmb_dataset._pydax_dir_)
        assert downloaded_gmb_dataset._file_list_file_.exists()  # Files are still there
        downloaded_gmb_dataset.delete(force=True)
        # We purposefully use _file_list_file instead of _file_list_file_ to create the parent directory so that
        # TemporaryDirectory doesn't complain during test cleanup of downloaded_gmb_dataset (Python < 3.8)
        assert not downloaded_gmb_dataset._file_list_file.exists()

    def test_directory_read_lock_present(self, downloaded_gmb_dataset):
        "Test various functions when a directory read lock is present."

        lock_file = downloaded_gmb_dataset._pydax_dir_ / 'read.king-kong.lock'
        lock_file.touch()

        f_stat = downloaded_gmb_dataset._file_list_file_.stat()
        self._test_lock_exception(
            lambda: downloaded_gmb_dataset.download(check=False),
            write=True,
            directory=downloaded_gmb_dataset._pydax_dir_)
        assert f_stat == downloaded_gmb_dataset._file_list_file_.stat()  # _file_list_file_ wasn't overwritten

        downloaded_gmb_dataset.load()  # No exception raised
        assert downloaded_gmb_dataset.data is not None

        self._test_lock_exception(
            lambda: downloaded_gmb_dataset.delete(), write=True, directory=downloaded_gmb_dataset._pydax_dir_)
        assert downloaded_gmb_dataset._file_list_file_.exists()  # Files are still there
        downloaded_gmb_dataset.delete(force=True)
        # We purposefully use _file_list_file instead of _file_list_file_ to create the parent directory so that
        # TemporaryDirectory doesn't complain during test cleanup of downloaded_gmb_dataset (Python < 3.8)
        assert not downloaded_gmb_dataset._file_list_file.exists()
