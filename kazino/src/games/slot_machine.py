"""
Модуль слот-машины для казино
Включает генерацию символов, вращение барабанов, проверку выигрышей
"""

import random
import time
from typing import List, Tuple, Dict, Optional
from enum import Enum
import pygame


class Symbol(Enum):
    """Символы для слот-машины"""
    CHERRY = "🍒"
    LEMON = "🍋"
    ORANGE = "🍊"
    PLUM = "🍇"
    BELL = "🔔"
    BAR = "📊"
    SEVEN = "7️⃣"
    DIAMOND = "💎"


class SlotMachine:
    """Основной класс слот-машины"""
    
    def __init__(self):
        # Символы с их весами (вероятностями)
        self.symbols = {
            Symbol.CHERRY: 0.25,    # 25%
            Symbol.LEMON: 0.20,     # 20%
            Symbol.ORANGE: 0.20,    # 20%
            Symbol.PLUM: 0.15,      # 15%
            Symbol.BELL: 0.10,      # 10%
            Symbol.BAR: 0.05,       # 5%
            Symbol.SEVEN: 0.03,     # 3%
            Symbol.DIAMOND: 0.02    # 2%
        }
        
        # Множители выигрышей
        self.payouts = {
            Symbol.CHERRY: {3: 5, 2: 2},      # 3 вишни = x5, 2 вишни = x2
            Symbol.LEMON: {3: 10, 2: 3},
            Symbol.ORANGE: {3: 10, 2: 3},
            Symbol.PLUM: {3: 15, 2: 5},
            Symbol.BELL: {3: 25, 2: 8},
            Symbol.BAR: {3: 50, 2: 15},
            Symbol.SEVEN: {3: 100, 2: 25},
            Symbol.DIAMOND: {3: 500, 2: 100}
        }
        
        self.reels = 3
        self.is_spinning = False
        self.spin_duration = 2.0  # секунды
        
    def get_random_symbol(self) -> Symbol:
        """Получить случайный символ на основе весов"""
        rand = random.random()
        cumulative = 0.0
        
        for symbol, weight in self.symbols.items():
            cumulative += weight
            if rand <= cumulative:
                return symbol
        
        return Symbol.CHERRY  # fallback
    
    def spin_reels(self) -> List[Symbol]:
        """Запустить вращение барабанов"""
        self.is_spinning = True
        result = []
        
        for _ in range(self.reels):
            result.append(self.get_random_symbol())
        
        self.is_spinning = False
        return result
    
    def check_win(self, symbols: List[Symbol], bet: int) -> Tuple[bool, int]:
        """
        Проверить выигрышную комбинацию
        Возвращает (есть_выигрыш, сумма_выигрыша)
        """
        if len(symbols) != self.reels:
            return False, 0
        
        # Подсчет одинаковых символов
        symbol_counts = {}
        for symbol in symbols:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        # Проверка выигрышных комбинаций
        for symbol, count in symbol_counts.items():
            if count >= 2 and symbol in self.payouts:
                if count == 3 and 3 in self.payouts[symbol]:
                    multiplier = self.payouts[symbol][3]
                    return True, bet * multiplier
                elif count == 2 and 2 in self.payouts[symbol]:
                    multiplier = self.payouts[symbol][2]
                    return True, bet * multiplier
        
        return False, 0
    
    def get_symbol_info(self, symbol: Symbol) -> Dict:
        """Получить информацию о символе"""
        return {
            'symbol': symbol,
            'emoji': symbol.value,
            'weight': self.symbols[symbol],
            'payouts': self.payouts.get(symbol, {})
        }


class SlotMachineGame:
    """Игровой менеджер слот-машины"""
    
    def __init__(self, initial_balance: int = 1000):
        self.slot_machine = SlotMachine()
        self.balance = initial_balance
        self.current_bet = 10
        self.last_result = []
        self.last_win = 0
        self.total_spins = 0
        self.total_wins = 0
        
    def place_bet(self, amount: int) -> bool:
        """Сделать ставку"""
        if amount <= 0 or amount > self.balance:
            return False
        
        self.current_bet = amount
        return True
    
    def spin(self) -> Tuple[List[Symbol], bool, int]:
        """
        Запустить игру
        Возвращает (результат_барабанов, есть_выигрыш, сумма_выигрыша)
        """
        if self.current_bet > self.balance:
            return [], False, 0
        
        # Списываем ставку
        self.balance -= self.current_bet
        self.total_spins += 1
        
        # Вращаем барабаны
        result = self.slot_machine.spin_reels()
        self.last_result = result
        
        # Проверяем выигрыш
        is_win, win_amount = self.slot_machine.check_win(result, self.current_bet)
        
        if is_win:
            self.balance += win_amount
            self.last_win = win_amount
            self.total_wins += 1
        else:
            self.last_win = 0
        
        return result, is_win, win_amount
    
    def get_stats(self) -> Dict:
        """Получить статистику игры"""
        win_rate = (self.total_wins / self.total_spins * 100) if self.total_spins > 0 else 0
        
        return {
            'balance': self.balance,
            'current_bet': self.current_bet,
            'total_spins': self.total_spins,
            'total_wins': self.total_wins,
            'win_rate': round(win_rate, 2),
            'last_result': self.last_result,
            'last_win': self.last_win
        }
    
    def can_spin(self) -> bool:
        """Можно ли запустить игру"""
        return self.balance >= self.current_bet and not self.slot_machine.is_spinning
    
    def reset_game(self, new_balance: int = 1000):
        """Сбросить игру"""
        self.balance = new_balance
        self.current_bet = 10
        self.last_result = []
        self.last_win = 0
        self.total_spins = 0
        self.total_wins = 0
