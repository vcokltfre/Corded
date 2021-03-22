from abc import abstractmethod
from typing import Union, List, Dict


class BaseCache:
    @abstractmethod
    async def set(key: str, value: str, namespace: str = None) -> int:
        pass

    @abstractmethod
    async def get(key: str, namespace: str = None) -> Union[str, None]:
        pass

    @abstractmethod
    async def keys(pattern: str = None, namespace: str = None) -> List[str]:
        pass

    @abstractmethod
    async def items(pattern: str = None, namespace: str = None) -> Dict[str]:
        pass

    @abstractmethod
    async def clear(namespace: str = None) -> int:
        pass
