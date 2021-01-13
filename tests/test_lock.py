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

import os

import pytest

from pydax._lock import DirectoryLock
from pydax.exceptions import DirectoryLockAcquisitionError


class TestDirectoryLock:
    "Test :class:`DirectoryLock`."

    @staticmethod
    def _ensure_lock_unlock_succeeds(directory: os.PathLike, write: bool):
        "A utility function that ensures some locks and unlocks should succeed."
        lock = DirectoryLock(directory)
        prefix = 'write' if write else 'read'
        assert lock.lock(write=write) is True
        assert (directory / f'{prefix}{lock._lock_file_suffix}').exists()
        assert lock.unlock() is True
        assert not (directory / f'{prefix}{lock._lock_file_suffix}').exists()

        with lock.locking(write=write) as succeed:
            assert (directory / f'{prefix}{lock._lock_file_suffix}').exists()
            assert succeed is True
        assert not (directory / f'{prefix}{lock._lock_file_suffix}').exists()

        with lock.locking_with_exception(write=write):
            assert (directory / f'{prefix}{lock._lock_file_suffix}').exists()
        assert not (directory / f'{prefix}{lock._lock_file_suffix}').exists()

    @staticmethod
    def _ensure_lock_fails(directory: os.PathLike, write: bool):
        "A utility function that ensures some locks should fail."
        lock = DirectoryLock(directory)
        prefix = 'write' if write else 'read'
        assert lock.lock(write=write) is False
        assert not (directory / f'{prefix}{lock._lock_file_suffix}').exists()

        with lock.locking(write=write) as succeed:
            assert succeed is False
            assert not (directory / f'{prefix}{lock._lock_file_suffix}').exists()
        assert not (directory / f'{prefix}{lock._lock_file_suffix}').exists()

        with pytest.raises(DirectoryLockAcquisitionError) as e:
            with lock.locking_with_exception(write=write):
                pass
        assert str(e.value) == f'Failed to acquire directory {"write" if write else "read"} lock for "{directory}"'
        assert not (directory / f'{prefix}{lock._lock_file_suffix}').exists()

    @staticmethod
    def _ensure_unlock_fails(directory: os.PathLike):
        "A utility function that ensures some unlocks should fail."
        lock = DirectoryLock(directory)
        assert lock.unlock() is False

    def test_lock_empty(self, tmp_path):
        "Test lock in an empty directory. Unlocking without locking should also fail."
        for write in (True, False):
            self._ensure_lock_unlock_succeeds(tmp_path, write)

        self._ensure_unlock_fails(tmp_path)

    @pytest.mark.parametrize('lock_file_list',
                             [
                                 # One write lock
                                 ('write.ding.dong.lock',),
                                 # Two write locks
                                 ('write.dong.ding.lock', 'write.777.lock'),
                                 # One write lock and one read lock
                                 ('write.ding.dong.lock', 'read.ibm-codait.lock'),
                             ])
    def test_failing_write_lock(self, tmp_path, lock_file_list):
        "Test locking when other write locks are present. Unlocking without locking should also fail."

        for f in lock_file_list:
            (tmp_path / f).touch()

        # Sanity check: lock files exist
        assert all((tmp_path / f).exists() for f in lock_file_list)

        for write in (True, False):
            self._ensure_lock_fails(tmp_path, write)

        self._ensure_unlock_fails(tmp_path)

    @pytest.mark.parametrize('lock_file_list',
                             [
                                 # One read lock
                                 ('read.ding.dong.lock',),
                                 # Two read locks
                                 ('read.dong.ding.lock', 'read.777.lock'),
                             ])
    def test_failing_read_lock(self, tmp_path, lock_file_list):
        "Test locking when other read locks are present. Unlocking without locking should also fail."

        for f in lock_file_list:
            (tmp_path / f).touch()

        # Sanity check: lock files exist
        assert all((tmp_path / f).exists() for f in lock_file_list)

        self._ensure_lock_fails(tmp_path, write=True)
        self._ensure_lock_unlock_succeeds(tmp_path, write=False)
        self._ensure_unlock_fails(tmp_path)

    @pytest.mark.parametrize('lock_file_list',
                             [
                                 # One write lock
                                 ('write.ding.dong.lock',),
                                 # Two write locks
                                 ('write.dong.ding.lock', 'write.777.lock'),
                                 # One write lock and one read lock
                                 ('write.ding.dong.lock', 'read.ibm-codait.lock'),
                                 # 100 write and read locks
                                 tuple(f'write.{i}.lock' for i in range(100)) +
                                 tuple(f'read.{i}.lock' for i in range(100)),
                             ])
    def test_force_clear_all_locks(self, tmp_path, lock_file_list):
        "Test clearing all locks."

        for f in lock_file_list:
            (tmp_path / f).touch()

        # Sanity check: lock files exist
        assert all((tmp_path / f).exists() for f in lock_file_list)

        DirectoryLock(tmp_path).force_clear_all_locks()

        assert all(not (tmp_path / f).exists() for f in lock_file_list)
