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

"Directory lock."


from contextlib import contextmanager
import itertools
import os
import pathlib
import threading
from uuid import uuid4
from typing import Iterator

from . import typing as typing_


class DirectoryLockAcquisitionError(RuntimeError):
    "Raised when failed to acquire a lock."


class DirectoryLock:
    """Read/write lock for a directory.

    A lock file is named as ``{read|write}.{pid}.{uuid}.lock``. This should be able to resolve all potential name
    clashes. We put process ID here in case someone wants to figure out which process created the file.

    As a reservation for future compatibility, this class reserves all files starting with ``read.``/``write.`` and ends
    with ``.lock`` for its own use.

    :param directory: The directory where lock files would be put.
    """

    def __init__(self, directory: typing_.PathLike):
        self._uuid: str = str(uuid4())
        self._directory: pathlib.Path = pathlib.Path(directory)
        self._thread_lock: threading.Lock = threading.Lock()

    @property
    def _lock_file_suffix(self) -> str:
        "The suffix of the lock file."
        return f'.{os.getpid()}.{self._uuid}.lock'

    def _get_read_locks(self) -> Iterator[pathlib.Path]:
        """Get a list of read lock files.

        :return: An iterable of read lock file paths. Empty if there's no read lock file.
        """
        return self._directory.glob("read.*.lock")

    def _get_write_locks(self) -> Iterator[pathlib.Path]:
        """Get a list of write lock files.

        :return: An iterable of write lock file paths. Empty if there's no write lock file.
        """

        return self._directory.glob("write.*.lock")

    def _does_read_lock_exist(self) -> bool:
        "Returns True if a read lock file exists, otherwise False."
        return next(self._get_read_locks(), None) is not None

    def _does_write_lock_exist(self) -> bool:
        "Returns True if a write lock file exists, otherwise False."
        return next(self._get_write_locks(), None) is not None

    def lock(self, *, write: bool) -> bool:
        """Lock the directory (create the lock file in the directory). If the directory does not exist, create it.

        :param write: Whether this is a write lock or a read lock. A write lock excludes others from both reading and
            writing, while a read lock only excludes writing. Multiple read locks can exist at the same time, but only
            one write lock may exist at any single moment.
        :return: True if lock succeeds, False if fails. This function does not throw exceptions because :meth:`.lock` is
            also used for peeking whether the lock is obtainable.
        """

        lock_file = self._directory / f'{"write" if write else "read"}{self._lock_file_suffix}'

        with self._thread_lock:
            if not self._directory.exists():
                self._directory.mkdir(parents=True)
            if not self._directory.is_dir():
                raise NotADirectoryError(f'"{self._directory}" exists and is not a directory.')
            if write:  # write lock
                if self._does_read_lock_exist() or self._does_write_lock_exist():
                    return False
                else:
                    lock_file.touch(exist_ok=False)
            else:  # read lock
                if self._does_write_lock_exist():
                    return False
                else:
                    lock_file.touch(exist_ok=False)

        return True

    def unlock(self) -> bool:
        """Unlock the directory.

        :return: True if unlock succeeds, False if there is no lock to remove. This function does not throw exceptions
            because it is commonplace to call :meth:`.unlock` from multiple locations and we consider the situation
            where the lock has been removed as an expected usage.
        """
        with self._thread_lock:
            lock_existed: bool = False
            write_lock_file = self._directory / f'write{self._lock_file_suffix}'
            if write_lock_file.exists():
                write_lock_file.unlink()
                lock_existed = True
            read_lock_file = self._directory / f'read{self._lock_file_suffix}'
            if read_lock_file.exists():
                read_lock_file.unlink()
                lock_existed = True
            return lock_existed

    @contextmanager
    def locking(self, *, write: bool) -> Iterator[bool]:
        """Same as :meth:`.lock`, but used in ``with`` statements.

        Example:

        .. code-block:: python

           with some_lock.locking(write=True):
               # do the work ...
        """
        try:
            yield self.lock(write=write)
        finally:
            self.unlock()

    @contextmanager
    def locking_with_exception(self, *, write: bool) -> Iterator[None]:
        """Similar to :meth:`.locking`, but raises exceptions if the lock is failed to acquire.

        :raises DirectoryLockAcquisitionError: Failed to acquire the directory lock.

        Example:

        .. code-block:: python

           with some_lock.locking_with_exception(write=True):
               # do the work ...
        """
        with self.locking(write=write) as lock:
            if not lock:
                raise DirectoryLockAcquisitionError(
                    f'Failed to acquire directory {"write" if write else "read"} lock for "{self._directory}"')
            yield

    def force_clear_all_locks(self) -> None:
        """Force clear all read locks. This is useful in situations such as those when system crashes and locks must be
        reset.
        """

        for f in itertools.chain(self._get_read_locks(), self._get_write_locks()):
            os.remove(f)
