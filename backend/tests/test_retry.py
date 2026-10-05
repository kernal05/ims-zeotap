import asyncio
from app.db.retry import with_retry


def test_retries_then_succeeds():
    calls = {"n": 0}

    @with_retry(max_attempts=3, delay=0)
    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("boom")
        return "ok"

    assert asyncio.run(flaky()) == "ok"
    assert calls["n"] == 3


def test_gives_up_after_max_attempts():
    calls = {"n": 0}

    @with_retry(max_attempts=3, delay=0)
    async def always_fails():
        calls["n"] += 1
        raise RuntimeError("down")

    try:
        asyncio.run(always_fails())
        assert False, "should have raised"
    except RuntimeError:
        pass
    assert calls["n"] == 3
