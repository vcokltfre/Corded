from abc import abstractmethod
from typing import Union, List, Dict, Any


class BaseCache:
    @abstractmethod
    async def set(self, key: str, value: str) -> bool:
        """Set a key to a given value."""
        pass

    @abstractmethod
    async def get(self, key: str) -> Union[str, None]:
        """Get the value of a given key."""
        pass

    @abstractmethod
    async def keys(self, pattern: str = None) -> List[str]:
        """Get all keys matching an optional pattern."""
        pass

    @abstractmethod
    async def items(self, pattern: str = None) -> Dict[str, Any]:
        """Get a dictionary of items, where the key matches an optional pattern."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear the cache."""
        pass


class MemoryCache(BaseCache):
    def __init__(self, namespace: str = None):
        """An im-memory cache for objects."""

        self._cache = {}

    async def set(self, key: str, value: str) -> bool:
        self._cache[key] = value
        return True

    async def get(self, key: str) -> Union[str, None]:
        return self._cache.get(key)

    async def keys(self, pattern: str = None) -> List[str]:
        if not pattern:
            return list(self._cache.keys())
        return [key for key in self._cache.keys() if pattern in key]

    async def items(self, pattern: str = None) -> Dict[str, Any]:
        if not pattern:
            return self._cache
        return dict((k, v) for k, v in self._cache.items() if pattern in k)

    async def clear(self) -> bool:
        self._cache = {}
        return True
