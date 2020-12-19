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
import os
import pathlib
import threading
from uuid import uuid4
from typing import Iterator

from . import _typing


class DirectoryLock:
    """Read/write lock for a directory.

    A lock file is named as ``{read|write}.{pid}.{uuid}.lock``. This should be able to resolve all potential name
    clashes. We put process ID here in case someone wants to figure out which process created the file.

    As a reservation for future compatibility, this class reserves all files starting with ``read.`` and ends with
    ``.lock`` for its own use.

    :param directory: The directory where lock files would be put.
    """

    def __init__(self, directory: _typing.PathLike):
        self._uuid: str = str(uuid4())
        self._directory: pathlib.Path = pathlib.Path(directory)
        self._thread_lock: threading.Lock = threading.Lock()

    @property
    def _lock_file_suffix(self) -> str:
        "The suffix of the lock file."
        return f'.{os.getpid()}.{self._uuid}.lock'

    def lock(self, *, write: bool) -> bool:
        """Lock the directory (create the lock file in the directory).

        :param write: Whether this is a write lock or a read lock. A write lock excludes others from both reading and
            writing, while a read lock only excludes writing. Multiple read locks can exist at the same time, but only
            one write lock may exist at any single moment.
        :return: True if lock succeeds, False if fails. This function does not throw exceptions because :meth:`.lock` is
            also used for peeking whether the lock is obtainable.
        """

        lock_file = self._directory / f'{"write" if write else "read"}{self._lock_file_suffix}'

        def does_read_lock_exist() -> bool:
            return next(self._directory.glob("read.*.lock"), None) is not None

        def does_write_lock_exist() -> bool:
            return next(self._directory.glob("write.*.lock"), None) is not None

        with self._thread_lock:
            if write:  # write lock
                if does_read_lock_exist() or does_write_lock_exist():
                    return False
                else:
                    lock_file.touch(exist_ok=False)
            else:  # read lock
                if does_write_lock_exist():
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
        yield self.lock(write=write)
        self.unlock()
