from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncIterator

import aiorwlock


class RWLock:
    def __init__(self) -> None:
        """
        Initializes a new instance of the ReaderWriterLock class.

        The constructor creates an underlying `aiorwlock.RWLock` instance and
        sets up the reader and writer locks.
        """
        _lock = aiorwlock.RWLock()
        self._reader_lock = _lock.reader
        self._writer_lock = _lock.writer

    @property
    def reader_lock(self) -> AsyncContextManager[None]:
        """
        Provides an asynchronous context manager for acquiring the reader lock.

        This lock allows multiple readers to access the shared resource simultaneously.
        Writers are blocked while any reader holds the lock.

        Returns:
            AsyncContextManager[None]: An asynchronous context manager for the reader lock.

        Example:
            ```python
            async with lock.reader_lock:
                # Read from the shared resource
            ```
        """

        @asynccontextmanager
        async def _reader_acm() -> AsyncIterator[None]:
            async with self._reader_lock:
                yield

        return _reader_acm()

    @property
    def writer_lock(self) -> AsyncContextManager[None]:
        """
        Provides an asynchronous context manager for acquiring the writer lock.

        This lock ensures exclusive access to the shared resource for writing.
        No readers or other writers are allowed while the writer lock is held.


        Returns:
            AsyncContextManager[None]: An asynchronous context manager for the writer lock.

        Example:
            ```python
            async with lock.writer_lock:
                # Write to the shared resource
            ```
        """

        @asynccontextmanager
        async def _writer_acm() -> AsyncIterator[None]:
            async with self._writer_lock:
                yield

        return _writer_acm()
