from abc import abstractmethod
from typing import Union, List, Dict


class BaseCache:
    @abstractmethod
    async def set(key: str, value: str) -> bool:
        pass

    @abstractmethod
    async def get(key: str) -> Union[str, None]:
        pass

    @abstractmethod
    async def keys(pattern: str = None) -> List[str]:
        pass

    @abstractmethod
    async def items(pattern: str = None) -> Dict[str]:
        pass

    @abstractmethod
    async def clear() -> bool:
        pass


class MemoryCache(BaseCache):
    def __init__(self, namespace: str = None):
        """An im-memory cache for objects.

        Args:
            namespace (str, optional): The namespace to use for caching. Defaults to no namespace.
        """

        self.namespace = namespace or ""
        self._cache = {}

    def set(self, key: str, value: str) -> bool:
        self._cache[key] = value
        return 1

    def get(self, key: str) -> Union[str, None]:
        return self._cache.get(key)

    def keys(self, pattern: str = None) -> List[str]:
        if not pattern:
            return list(self._cache.keys())
        return [key for key in self._cache.keys() if pattern in key]

    def items(self, pattern: str = None) -> Dict[str]:
        if not pattern:
            return self._cache
        return dict((k, v) for k, v in self._cache.items() if pattern in k)
