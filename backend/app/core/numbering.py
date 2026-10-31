import threading
from typing import Dict

_counters: Dict[str, int] = {}
_lock = threading.Lock()

def next_number(prefix: str, year: int = 2026) -> str:
    key = f"{prefix}-{year}"
    with _lock:
        current = _counters.get(key, 0) + 1
        _counters[key] = current
        return f"{prefix}-{year}-{current:06d}"

def set_counter(prefix: str, year: int, val: int) -> None:
    key = f"{prefix}-{year}"
    with _lock:
        _counters[key] = max(_counters.get(key, 0), val)
