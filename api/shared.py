"""State the WhatsApp bridge shares across API processes: outbox, pending sign-in codes, rate limits, worker heartbeat.

In memory by default (one process, as on the free plan). With REDIS_URL set, the same calls go to Redis, so several
uvicorn workers or several instances behind a load balancer see one outbox and one set of codes. Nothing stored here
is personal beyond a phone number and a hash of the code; every key expires.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from collections import deque

P = "rw:"  # key prefix


class Memory:
    kind = "memory"

    def __init__(self):
        self.outbox: list[dict] = []
        self.evt: asyncio.Event | None = None
        self.otp: dict[str, tuple[dict, float]] = {}
        self.hits: dict[str, deque] = {}
        self.w = {"state": "offline", "seen": 0.0, "number": None}

    def _evt(self) -> asyncio.Event:
        if self.evt is None:
            self.evt = asyncio.Event()
        return self.evt

    async def put(self, msg: dict):
        self.outbox.append(msg)
        self._evt().set()

    async def take(self, wait: float) -> list[dict]:
        if not self.outbox:
            self._evt().clear()
            try:
                await asyncio.wait_for(self._evt().wait(), timeout=wait)
            except asyncio.TimeoutError:
                pass
        msgs, self.outbox[:] = list(self.outbox), []
        return msgs

    async def otp_set(self, m: str, rec: dict, ttl: int):
        self.otp[m] = (rec, time.time() + ttl)

    async def otp_get(self, m: str) -> dict | None:
        rec = self.otp.get(m)
        if rec and rec[1] > time.time():
            return rec[0]
        self.otp.pop(m, None)
        return None

    async def otp_del(self, m: str):
        self.otp.pop(m, None)

    async def wait_for(self, key: str, n: int, window: int, now: float) -> int:
        """0 when allowed, else seconds to wait. Does not record the hit (see hit)."""
        q = self.hits.setdefault(key, deque())
        while q and now - q[0] >= window:
            q.popleft()
        return int(window - (now - q[0])) + 1 if len(q) >= n else 0

    async def hit(self, key: str, now: float, window: int):
        self.hits.setdefault(key, deque()).append(now)

    async def beat(self, state: str | None = None, number: str | None = None):
        self.w["seen"] = time.time()
        if state:
            self.w["state"] = state
        if number is not None:
            self.w["number"] = number

    async def worker(self) -> dict:
        return dict(self.w)


class Redis:
    kind = "redis"

    def __init__(self, url: str):
        import redis.asyncio as aioredis
        self.r = aioredis.from_url(url, decode_responses=True)

    async def put(self, msg: dict):
        await self.r.rpush(P + "outbox", json.dumps(msg, ensure_ascii=False))

    async def take(self, wait: float) -> list[dict]:
        first = await self.r.blpop([P + "outbox"], timeout=max(1, int(wait)))  # long poll across processes
        if not first:
            return []
        rest = await self.r.lpop(P + "outbox", 100) or []
        return [json.loads(x) for x in [first[1], *rest]]

    async def otp_set(self, m: str, rec: dict, ttl: int):
        await self.r.set(P + "otp:" + m, json.dumps(rec), ex=ttl)

    async def otp_get(self, m: str) -> dict | None:
        v = await self.r.get(P + "otp:" + m)
        return json.loads(v) if v else None

    async def otp_del(self, m: str):
        await self.r.delete(P + "otp:" + m)

    async def wait_for(self, key: str, n: int, window: int, now: float) -> int:
        k = P + "rl:" + key
        await self.r.zremrangebyscore(k, 0, now - window)
        if await self.r.zcard(k) < n:
            return 0
        oldest = await self.r.zrange(k, 0, 0, withscores=True)
        return int(window - (now - oldest[0][1])) + 1 if oldest else 0

    async def hit(self, key: str, now: float, window: int):
        k = P + "rl:" + key
        await self.r.zadd(k, {f"{now}:{os.urandom(4).hex()}": now})
        await self.r.expire(k, window)

    async def beat(self, state: str | None = None, number: str | None = None):
        fields = {"seen": time.time()}
        if state:
            fields["state"] = state
        if number is not None:
            fields["number"] = number
        await self.r.hset(P + "worker", mapping=fields)
        await self.r.expire(P + "worker", 3600)

    async def worker(self) -> dict:
        w = await self.r.hgetall(P + "worker")
        return {"state": w.get("state", "offline"), "seen": float(w.get("seen", 0) or 0), "number": w.get("number")}


_state: Memory | Redis | None = None


def state() -> Memory | Redis:
    global _state
    if _state is None:
        url = os.environ.get("REDIS_URL")
        _state = Redis(url) if url else Memory()
    return _state
