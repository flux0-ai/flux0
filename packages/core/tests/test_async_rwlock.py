import asyncio
from typing import List

from flux0_core.async_utils import RWLock


async def test_multiple_readers() -> None:
    """
    Test that multiple readers can acquire the lock simultaneously.
    """
    lock = RWLock()
    results: List[str] = []

    async def reader_task(name: str) -> None:
        async with lock.reader_lock:
            results.append(f"{name} started reading")
            await asyncio.sleep(0.1)  # Simulate some work
            results.append(f"{name} finished reading")

    # Start multiple readers
    await asyncio.gather(
        reader_task("Reader 1"),
        reader_task("Reader 2"),
        reader_task("Reader 3"),
    )

    # Verify that all readers executed concurrently
    assert "Reader 1 started reading" in results
    assert "Reader 2 started reading" in results
    assert "Reader 3 started reading" in results
    assert "Reader 1 finished reading" in results
    assert "Reader 2 finished reading" in results
    assert "Reader 3 finished reading" in results


async def test_writer_exclusive_access() -> None:
    """
    Test that a writer has exclusive access to the resource.
    """
    lock = RWLock()
    results: List[str] = []

    async def writer_task(name: str) -> None:
        async with lock.writer_lock:
            results.append(f"{name} started writing")
            await asyncio.sleep(0.1)  # Simulate some work
            results.append(f"{name} finished writing")

    async def reader_task(name: str) -> None:
        async with lock.reader_lock:
            results.append(f"{name} started reading")
            await asyncio.sleep(0.1)  # Simulate some work
            results.append(f"{name} finished reading")

    # Start a writer and a reader
    await asyncio.gather(
        writer_task("Writer 1"),
        reader_task("Reader 1"),
    )

    # Verify that the writer executed exclusively
    assert results == [
        "Writer 1 started writing",
        "Writer 1 finished writing",
        "Reader 1 started reading",
        "Reader 1 finished reading",
    ]


async def test_writers_block_each_other() -> None:
    """
    Test that writers block each other and execute sequentially.
    """
    lock = RWLock()
    results: List[str] = []

    async def writer_task(name: str) -> None:
        async with lock.writer_lock:
            results.append(f"{name} started writing")
            await asyncio.sleep(0.1)  # Simulate some work
            results.append(f"{name} finished writing")

    # Start multiple writers
    await asyncio.gather(
        writer_task("Writer 1"),
        writer_task("Writer 2"),
        writer_task("Writer 3"),
    )

    # Verify that writers executed sequentially
    assert results == [
        "Writer 1 started writing",
        "Writer 1 finished writing",
        "Writer 2 started writing",
        "Writer 2 finished writing",
        "Writer 3 started writing",
        "Writer 3 finished writing",
    ]


async def test_readers_block_writer() -> None:
    """
    Test that readers block a writer until they are done.
    """
    lock = RWLock()
    results: List[str] = []

    async def reader_task(name: str) -> None:
        async with lock.reader_lock:
            results.append(f"{name} started reading")
            await asyncio.sleep(0.1)  # Simulate some work
            results.append(f"{name} finished reading")

    async def writer_task(name: str) -> None:
        async with lock.writer_lock:
            results.append(f"{name} started writing")
            await asyncio.sleep(0.1)  # Simulate some work
            results.append(f"{name} finished writing")

    # Start readers first, then a writer
    await asyncio.gather(
        reader_task("Reader 1"),
        reader_task("Reader 2"),
        writer_task("Writer 1"),
    )

    # Verify that the writer waited for the readers to finish
    assert results == [
        "Reader 1 started reading",
        "Reader 2 started reading",
        "Reader 1 finished reading",
        "Reader 2 finished reading",
        "Writer 1 started writing",
        "Writer 1 finished writing",
    ]


async def test_writer_blocks_readers() -> None:
    """
    Test that a writer blocks readers until it is done.
    """
    lock = RWLock()
    results: List[str] = []

    async def reader_task(name: str) -> None:
        async with lock.reader_lock:
            results.append(f"{name} started reading")
            await asyncio.sleep(0.1)  # Simulate some work
            results.append(f"{name} finished reading")

    async def writer_task(name: str) -> None:
        async with lock.writer_lock:
            results.append(f"{name} started writing")
            await asyncio.sleep(0.1)  # Simulate some work
            results.append(f"{name} finished writing")

    # Start a writer first, then readers
    await asyncio.gather(
        writer_task("Writer 1"),
        reader_task("Reader 1"),
        reader_task("Reader 2"),
    )

    # Verify that the readers waited for the writer to finish
    assert results == [
        "Writer 1 started writing",
        "Writer 1 finished writing",
        "Reader 1 started reading",
        "Reader 2 started reading",
        "Reader 1 finished reading",
        "Reader 2 finished reading",
    ]
