"""Unit test suite for WS-01.4B Thread-Local Context Propagation Engine."""

import asyncio
import threading
import pytest
from src.logging import (
    bind_log_context,
    clear_log_context,
    get_log_context,
    get_logger,
    unbind_log_context,
)


def setup_function() -> None:
    clear_log_context()


def test_bind_and_get_log_context() -> None:
    bind_log_context(correlation_id="uuid-1234", plant_code="PLANT-K01", batch_id="B-100")
    ctx = get_log_context()
    assert ctx["correlation_id"] == "uuid-1234"
    assert ctx["plant_code"] == "PLANT-K01"
    assert ctx["batch_id"] == "B-100"


def test_unbind_and_clear_log_context() -> None:
    bind_log_context(correlation_id="uuid-1234", plant_code="PLANT-K01")
    unbind_log_context("plant_code")
    assert "plant_code" not in get_log_context()
    assert get_log_context()["correlation_id"] == "uuid-1234"

    clear_log_context()
    assert len(get_log_context()) == 0


def test_overwrite_behavior() -> None:
    bind_log_context(plant_code="PLANT-01")
    bind_log_context(plant_code="PLANT-02")
    assert get_log_context()["plant_code"] == "PLANT-02"


def test_invalid_key_and_value_validation() -> None:
    with pytest.raises(TypeError):
        bind_log_context(**{123: "val"})  # type: ignore

    class NonSerializable:
        pass

    with pytest.raises(ValueError):
        bind_log_context(bad_val=NonSerializable())


def test_thread_isolation() -> None:
    bind_log_context(main_thread="yes")

    child_context = {}

    def worker() -> None:
        bind_log_context(worker_thread="yes")
        child_context.update(get_log_context())

    t = threading.Thread(target=worker)
    t.start()
    t.join()

    assert "main_thread" in get_log_context()
    assert "worker_thread" not in get_log_context()
    assert child_context.get("worker_thread") == "yes"
    assert "main_thread" not in child_context


def test_async_isolation() -> None:
    async def async_worker(tag: str) -> str:
        clear_log_context()
        bind_log_context(async_tag=tag)
        await asyncio.sleep(0.01)
        return get_log_context().get("async_tag", "")

    async def main() -> None:
        res1, res2 = await asyncio.gather(async_worker("task1"), async_worker("task2"))
        assert res1 == "task1"
        assert res2 == "task2"

    asyncio.run(main())


def test_logger_automatic_context_merge() -> None:
    clear_log_context()
    bind_log_context(correlation_id="corr-999", batch_id="B-888")
    log = get_logger("test_context_merge", component="domain")

    assert get_log_context()["correlation_id"] == "corr-999"
    assert get_log_context()["batch_id"] == "B-888"
