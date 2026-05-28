import time

from redis.exceptions import LockNotOwnedError
from redis.lock import Lock as RedisLock


def extend_lock(lock: RedisLock, timeout: int, last_lock_time: float) -> float:
    current_time = time.monotonic()
    if current_time - last_lock_time >= (timeout / 4):
        try:
            lock.reacquire()
        except LockNotOwnedError:
            # Lock expired during a long operation; re-acquire it.
            if not lock.acquire(blocking=False):
                raise
        last_lock_time = current_time

    return last_lock_time
