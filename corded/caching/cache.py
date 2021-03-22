from abc import abstractmethod
from typing import Union, List, Dict


class BaseCache:
    @abstractmethod
    async def set(key: str, value: str) -> int:
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
    async def clear() -> int:
        pass
