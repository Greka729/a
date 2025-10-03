"""
Менеджер состояния игры слот-машины
Интегрируется с системой баланса казино
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .slot_machine import SlotMachine, Symbol
from .slot_win_checker import SlotWinChecker, WinLine
try:
    from ..balance import BalanceManager
except ImportError:
    from balance import BalanceManager


class SlotGameState:
    """Состояние игры слот-машины"""
    
    def __init__(self):
        self.total_spins = 0
        self.total_wins = 0
        self.total_bet = 0
        self.total_payout = 0
        self.biggest_win = 0
        self.current_streak = 0
        self.longest_streak = 0
        self.last_win_time = None
        self.games_played = 0
        self.symbol_stats = {symbol: 0 for symbol in Symbol}
        self.win_line_stats = {}
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь для сохранения"""
        return {
            'total_spins': self.total_spins,
            'total_wins': self.total_wins,
            'total_bet': self.total_bet,
            'total_payout': self.total_payout,
            'biggest_win': self.biggest_win,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'last_win_time': self.last_win_time.isoformat() if self.last_win_time else None,
            'games_played': self.games_played,
            'symbol_stats': {symbol.value: count for symbol, count in self.symbol_stats.items()},
            'win_line_stats': self.win_line_stats
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SlotGameState':
        """Создать из словаря"""
        state = cls()
        state.total_spins = data.get('total_spins', 0)
        state.total_wins = data.get('total_wins', 0)
        state.total_bet = data.get('total_bet', 0)
        state.total_payout = data.get('total_payout', 0)
        state.biggest_win = data.get('biggest_win', 0)
        state.current_streak = data.get('current_streak', 0)
        state.longest_streak = data.get('longest_streak', 0)
        
        last_win_time = data.get('last_win_time')
        if last_win_time:
            state.last_win_time = datetime.fromisoformat(last_win_time)
        
        state.games_played = data.get('games_played', 0)
        
        # Восстанавливаем статистику символов
        symbol_stats = data.get('symbol_stats', {})
        for symbol_value, count in symbol_stats.items():
            try:
                symbol = Symbol(symbol_value)
                state.symbol_stats[symbol] = count
            except ValueError:
                continue
        
        state.win_line_stats = data.get('win_line_stats', {})
        return state


class SlotGameManager:
    """Менеджер игры слот-машины"""
    
    def __init__(self, balance_manager: BalanceManager, state_file: str = "data/slot_state.json"):
        self.balance_manager = balance_manager
        self.state_file = state_file
        self.slot_machine = SlotMachine()
        self.win_checker = SlotWinChecker()
        self.game_state = SlotGameState()
        self.current_bet = 10
        self.last_result = []
        self.last_wins = []
        self.is_spinning = False
        
        # Загружаем состояние игры
        self._load_state()
    
    def _load_state(self):
        """Загрузить состояние игры из файла. При ошибке — авто-ремонт."""
        if not os.path.exists(self.state_file):
            return
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.game_state = SlotGameState.from_dict(data)
        except Exception as e:
            # Авто-ремонт: переименуем битый файл и создадим новый по умолчанию
            try:
                base, ext = os.path.splitext(self.state_file)
                backup = f"{base}.corrupted{ext}"
                if os.path.exists(self.state_file):
                    os.replace(self.state_file, backup)
                print(f"Состояние слотов повреждено и переименовано в: {backup}")
            except Exception:
                # тихо игнорируем проблемы с переименованием
                pass
            self.game_state = SlotGameState()
            # попытка сохранить чистое состояние
            self._save_state()
    
    def _save_state(self):
        """Сохранить состояние игры в файл"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.game_state.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения состояния игры: {e}")
    
    def set_bet(self, amount: int) -> bool:
        """Установить размер ставки"""
        if amount <= 0:
            return False
        
        if not self.balance_manager.can_place_bet(amount):
            return False
        
        self.current_bet = amount
        return True
    
    def spin(self) -> Tuple[List[Symbol], List[Dict], int]:
        """
        Запустить игру
        Возвращает (результат_барабанов, список_выигрышей, общий_выигрыш)
        """
        if self.is_spinning:
            return [], [], 0
        
        if not self.balance_manager.can_place_bet(self.current_bet):
            return [], [], 0
        
        self.is_spinning = True
        
        try:
            # Списываем ставку
            self.balance_manager.apply_bet_result(self.current_bet, 0.0)
            self.game_state.total_bet += self.current_bet
            self.game_state.total_spins += 1
            self.game_state.games_played += 1
            
            # Вращаем барабаны
            result = self.slot_machine.spin_reels()
            self.last_result = result
            
            # Обновляем статистику символов
            for symbol in result:
                self.game_state.symbol_stats[symbol] += 1
            
            # Проверяем выигрыши
            wins = self.win_checker.check_all_wins(result, self.current_bet)
            self.last_wins = wins
            
            # Вычисляем общий выигрыш
            total_payout = self.win_checker.get_total_payout(wins)
            
            if total_payout > 0:
                # Есть выигрыш
                self.balance_manager.deposit(total_payout)
                self.game_state.total_payout += total_payout
                self.game_state.total_wins += 1
                self.game_state.current_streak += 1
                self.game_state.last_win_time = datetime.now()
                
                if total_payout > self.game_state.biggest_win:
                    self.game_state.biggest_win = total_payout
                
                if self.game_state.current_streak > self.game_state.longest_streak:
                    self.game_state.longest_streak = self.game_state.current_streak
                
                # Обновляем статистику выигрышных линий
                for win in wins:
                    win_type = win.get('win_type', 'unknown')
                    self.game_state.win_line_stats[win_type] = self.game_state.win_line_stats.get(win_type, 0) + 1
            else:
                # Проигрыш
                self.game_state.current_streak = 0
            
            # Сохраняем состояние
            self._save_state()
            
            return result, wins, total_payout
            
        finally:
            self.is_spinning = False
    
    def get_balance(self) -> int:
        """Получить текущий баланс"""
        return self.balance_manager.get_balance()
    
    def get_stats(self) -> Dict:
        """Получить статистику игры"""
        win_rate = (self.game_state.total_wins / self.game_state.total_spins * 100) if self.game_state.total_spins > 0 else 0
        rtp = (self.game_state.total_payout / self.game_state.total_bet * 100) if self.game_state.total_bet > 0 else 0
        
        return {
            'balance': self.get_balance(),
            'current_bet': self.current_bet,
            'total_spins': self.game_state.total_spins,
            'total_wins': self.game_state.total_wins,
            'win_rate': round(win_rate, 2),
            'rtp': round(rtp, 2),  # Return to Player
            'biggest_win': self.game_state.biggest_win,
            'current_streak': self.game_state.current_streak,
            'longest_streak': self.game_state.longest_streak,
            'games_played': self.game_state.games_played,
            'last_result': self.last_result,
            'last_wins': self.last_wins,
            'symbol_stats': self.game_state.symbol_stats,
            'win_line_stats': self.game_state.win_line_stats
        }
    
    def can_spin(self) -> bool:
        """Можно ли запустить игру"""
        return not self.is_spinning and self.balance_manager.can_place_bet(self.current_bet)
    
    def get_available_bets(self) -> List[int]:
        """Получить доступные размеры ставок"""
        balance = self.get_balance()
        bets = [5, 10, 25, 50, 100, 250, 500]
        return [bet for bet in bets if bet <= balance]
    
    def reset_stats(self):
        """Сбросить статистику игры"""
        self.game_state = SlotGameState()
        self._save_state()
    
    def get_symbol_info(self) -> Dict:
        """Получить информацию о символах и их выплатах"""
        return {
            'symbols': {symbol.value: {
                'weight': self.slot_machine.symbols[symbol],
                'payouts': self.slot_machine.payouts[symbol]
            } for symbol in Symbol},
            'win_lines': len(self.win_checker.win_lines),
            'bonus_multipliers': self.win_checker.bonus_multipliers
        }
