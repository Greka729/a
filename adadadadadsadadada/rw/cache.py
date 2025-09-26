from collections import OrderedDict
from typing import Optional, Tuple


class LRUCache:
    def __init__(self, capacity: int = 20):
        self.capacity = capacity
        self._store: "OrderedDict[str, Tuple[str, str, str]]" = OrderedDict()

    def get(self, key: str) -> Optional[Tuple[str, str, str]]:
        if key not in self._store:
            return None
        value = self._store.pop(key)
        self._store[key] = value
        return value

    def put(self, key: str, value: Tuple[str, str, str]) -> None:
        if key in self._store:
            self._store.pop(key)
        self._store[key] = value
        if len(self._store) > self.capacity:
            self._store.popitem(last=False)

    def keys(self):
        return list(self._store.keys())

    def items(self):
        return list(self._store.items())


