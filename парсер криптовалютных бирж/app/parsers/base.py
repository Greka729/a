from abc import ABC, abstractmethod
from typing import Dict, List

class BaseParser(ABC):
    """Абстрактный базовый класс для парсеров"""

    @abstractmethod
    async def get_current_price(self, symbol: str) -> Dict:
        pass

    @abstractmethod
    async def get_historical_data(self, symbol: str, days: int) -> List[Dict]:
        pass


