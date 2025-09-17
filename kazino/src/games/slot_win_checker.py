"""
Модуль для проверки выигрышных комбинаций в слот-машине
Включает различные типы выигрышных линий и бонусные функции
"""

from typing import List, Tuple, Dict, Set
from enum import Enum
try:
    from .slot_machine import Symbol
except ImportError:
    from slot_machine import Symbol


class WinType(Enum):
    """Типы выигрышных комбинаций"""
    HORIZONTAL = "horizontal"      # Горизонтальная линия
    DIAGONAL_LEFT = "diagonal_left"  # Диагональ слева направо
    DIAGONAL_RIGHT = "diagonal_right"  # Диагональ справа налево
    VERTICAL = "vertical"          # Вертикальная линия
    SCATTER = "scatter"           # Разбросанные символы
    WILD = "wild"                 # Дикий символ


class WinLine:
    """Класс для описания выигрышной линии"""
    
    def __init__(self, positions: List[Tuple[int, int]], win_type: WinType, multiplier: float = 1.0):
        self.positions = positions  # Список позиций (reel, row)
        self.win_type = win_type
        self.multiplier = multiplier


class SlotWinChecker:
    """Проверяет выигрышные комбинации в слот-машине"""
    
    def __init__(self):
        # Определяем выигрышные линии
        self.win_lines = [
            # Горизонтальные линии
            WinLine([(0, 0), (1, 0), (2, 0)], WinType.HORIZONTAL),  # Верхняя
            WinLine([(0, 1), (1, 1), (2, 1)], WinType.HORIZONTAL),  # Средняя
            WinLine([(0, 2), (1, 2), (2, 2)], WinType.HORIZONTAL),  # Нижняя
            
            # Диагональные линии
            WinLine([(0, 0), (1, 1), (2, 2)], WinType.DIAGONAL_LEFT),
            WinLine([(0, 2), (1, 1), (2, 0)], WinType.DIAGONAL_RIGHT),
        ]
        
        # Специальные символы
        self.wild_symbols = {Symbol.DIAMOND}  # Бриллиант - дикий символ
        self.scatter_symbols = {Symbol.SEVEN}  # Семерка - разбросанный символ
        
        # Бонусные множители
        self.bonus_multipliers = {
            WinType.HORIZONTAL: 1.0,
            WinType.DIAGONAL_LEFT: 1.5,
            WinType.DIAGONAL_RIGHT: 1.5,
            WinType.SCATTER: 2.0,
            WinType.WILD: 3.0
        }
    
    def check_all_wins(self, reels: List[List[Symbol]], bet: int) -> List[Dict]:
        """
        Проверить все возможные выигрыши
        Возвращает список выигрышных комбинаций
        """
        wins = []
        
        # Проверяем обычные выигрышные линии
        for line in self.win_lines:
            win = self._check_line_win(reels, line, bet)
            if win:
                wins.append(win)
        
        # Проверяем разбросанные символы
        scatter_win = self._check_scatter_win(reels, bet)
        if scatter_win:
            wins.append(scatter_win)
        
        # Проверяем дикие символы
        wild_win = self._check_wild_win(reels, bet)
        if wild_win:
            wins.append(wild_win)
        
        return wins
    
    def _check_line_win(self, reels: List[List[Symbol]], line: WinLine, bet: int) -> Dict:
        """Проверить выигрыш по конкретной линии"""
        if len(reels) != 3 or any(len(reel) != 3 for reel in reels):
            return None
        
        # Получаем символы на линии
        line_symbols = []
        for reel_idx, row_idx in line.positions:
            if reel_idx < len(reels) and row_idx < len(reels[reel_idx]):
                line_symbols.append(reels[reel_idx][row_idx])
        
        if len(line_symbols) != 3:
            return None
        
        # Проверяем комбинацию
        symbol = self._get_winning_symbol(line_symbols)
        if symbol is None:
            return None
        
        # Подсчитываем количество одинаковых символов
        count = line_symbols.count(symbol)
        if count < 2:
            return None
        
        # Вычисляем выигрыш
        base_payout = self._get_symbol_payout(symbol, count)
        total_payout = int(base_payout * bet * line.multiplier * self.bonus_multipliers[line.win_type])
        
        return {
            'type': 'line_win',
            'win_type': line.win_type,
            'symbol': symbol,
            'count': count,
            'positions': line.positions,
            'payout': total_payout,
            'multiplier': line.multiplier * self.bonus_multipliers[line.win_type]
        }
    
    def _check_scatter_win(self, reels: List[List[Symbol]], bet: int) -> Dict:
        """Проверить выигрыш разбросанных символов"""
        scatter_count = 0
        scatter_positions = []
        
        for reel_idx, reel in enumerate(reels):
            for row_idx, symbol in enumerate(reel):
                if symbol in self.scatter_symbols:
                    scatter_count += 1
                    scatter_positions.append((reel_idx, row_idx))
        
        if scatter_count >= 3:
            # Бонус за разбросанные символы
            bonus_multiplier = scatter_count * 0.5
            payout = int(bet * 10 * bonus_multiplier)
            
            return {
                'type': 'scatter_win',
                'win_type': WinType.SCATTER,
                'symbol': Symbol.SEVEN,
                'count': scatter_count,
                'positions': scatter_positions,
                'payout': payout,
                'multiplier': bonus_multiplier
            }
        
        return None
    
    def _check_wild_win(self, reels: List[List[Symbol]], bet: int) -> Dict:
        """Проверить выигрыш с дикими символами"""
        wild_count = 0
        wild_positions = []
        
        for reel_idx, reel in enumerate(reels):
            for row_idx, symbol in enumerate(reel):
                if symbol in self.wild_symbols:
                    wild_count += 1
                    wild_positions.append((reel_idx, row_idx))
        
        if wild_count >= 2:
            # Бонус за дикие символы
            bonus_multiplier = wild_count * 2.0
            payout = int(bet * 5 * bonus_multiplier)
            
            return {
                'type': 'wild_win',
                'win_type': WinType.WILD,
                'symbol': Symbol.DIAMOND,
                'count': wild_count,
                'positions': wild_positions,
                'payout': payout,
                'multiplier': bonus_multiplier
            }
        
        return None
    
    def _get_winning_symbol(self, symbols: List[Symbol]) -> Symbol:
        """Определить выигрышный символ в комбинации"""
        # Проверяем дикие символы
        wild_symbols = [s for s in symbols if s in self.wild_symbols]
        regular_symbols = [s for s in symbols if s not in self.wild_symbols]
        
        if len(wild_symbols) >= 2:
            return wild_symbols[0]
        
        if len(regular_symbols) >= 2:
            # Ищем самый частый символ
            symbol_counts = {}
            for symbol in regular_symbols:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            # Возвращаем символ с максимальным количеством
            return max(symbol_counts, key=symbol_counts.get)
        
        return None
    
    def _get_symbol_payout(self, symbol: Symbol, count: int) -> float:
        """Получить базовый множитель для символа"""
        payouts = {
            Symbol.CHERRY: {2: 2, 3: 5},
            Symbol.LEMON: {2: 3, 3: 10},
            Symbol.ORANGE: {2: 3, 3: 10},
            Symbol.PLUM: {2: 5, 3: 15},
            Symbol.BELL: {2: 8, 3: 25},
            Symbol.BAR: {2: 15, 3: 50},
            Symbol.SEVEN: {2: 25, 3: 100},
            Symbol.DIAMOND: {2: 100, 3: 500}
        }
        
        return payouts.get(symbol, {}).get(count, 0)
    
    def get_total_payout(self, wins: List[Dict]) -> int:
        """Получить общий выигрыш"""
        return sum(win['payout'] for win in wins)
    
    def get_win_description(self, win: Dict) -> str:
        """Получить описание выигрыша"""
        if win['type'] == 'line_win':
            return f"{win['count']}x {win['symbol'].value} на {win['win_type'].value} линии"
        elif win['type'] == 'scatter_win':
            return f"{win['count']}x разбросанных {win['symbol'].value}"
        elif win['type'] == 'wild_win':
            return f"{win['count']}x диких {win['symbol'].value}"
        
        return "Неизвестный выигрыш"
