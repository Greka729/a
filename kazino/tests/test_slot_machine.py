"""
Юнит-тесты для слот-машины
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from games.slot_machine import SlotMachine, Symbol, SlotMachineGame
from games.slot_win_checker import SlotWinChecker, WinType
from games.slot_game_manager import SlotGameManager, SlotGameState
from balance import BalanceManager


class TestSlotMachine(unittest.TestCase):
    """Тесты для основного класса слот-машины"""
    
    def setUp(self):
        self.slot_machine = SlotMachine()
    
    def test_get_random_symbol(self):
        """Тест генерации случайного символа"""
        symbol = self.slot_machine.get_random_symbol()
        self.assertIsInstance(symbol, Symbol)
        self.assertIn(symbol, Symbol)
    
    def test_spin_reels(self):
        """Тест вращения барабанов"""
        result = self.slot_machine.spin_reels()
        
        # Проверяем, что результат содержит 3 символа
        self.assertEqual(len(result), 3)
        
        # Проверяем, что все символы валидны
        for symbol in result:
            self.assertIsInstance(symbol, Symbol)
    
    def test_check_win_three_of_a_kind(self):
        """Тест выигрышной комбинации из трех одинаковых символов"""
        # Тестируем выигрыш с тремя вишнями
        symbols = [Symbol.CHERRY, Symbol.CHERRY, Symbol.CHERRY]
        is_win, payout = self.slot_machine.check_win(symbols, 10)
        
        self.assertTrue(is_win)
        self.assertEqual(payout, 50)  # 10 * 5 (множитель для 3 вишен)
    
    def test_check_win_two_of_a_kind(self):
        """Тест выигрышной комбинации из двух одинаковых символов"""
        # Тестируем выигрыш с двумя вишнями
        symbols = [Symbol.CHERRY, Symbol.CHERRY, Symbol.LEMON]
        is_win, payout = self.slot_machine.check_win(symbols, 10)
        
        self.assertTrue(is_win)
        self.assertEqual(payout, 20)  # 10 * 2 (множитель для 2 вишен)
    
    def test_check_win_no_win(self):
        """Тест отсутствия выигрышной комбинации"""
        # Тестируем проигрышную комбинацию
        symbols = [Symbol.CHERRY, Symbol.LEMON, Symbol.ORANGE]
        is_win, payout = self.slot_machine.check_win(symbols, 10)
        
        self.assertFalse(is_win)
        self.assertEqual(payout, 0)
    
    def test_check_win_invalid_input(self):
        """Тест с невалидным входом"""
        # Тестируем с неправильным количеством символов
        symbols = [Symbol.CHERRY, Symbol.LEMON]
        is_win, payout = self.slot_machine.check_win(symbols, 10)
        
        self.assertFalse(is_win)
        self.assertEqual(payout, 0)


class TestSlotWinChecker(unittest.TestCase):
    """Тесты для проверки выигрышных комбинаций"""
    
    def setUp(self):
        self.win_checker = SlotWinChecker()
    
    def test_check_line_win_horizontal(self):
        """Тест выигрыша по горизонтальной линии"""
        # Создаем сетку 3x3 с выигрышной комбинацией
        reels = [
            [Symbol.CHERRY, Symbol.LEMON, Symbol.ORANGE],
            [Symbol.CHERRY, Symbol.LEMON, Symbol.ORANGE],
            [Symbol.CHERRY, Symbol.LEMON, Symbol.ORANGE]
        ]
        
        wins = self.win_checker.check_all_wins(reels, 10)
        
        # Должны быть выигрыши по всем трем горизонтальным линиям
        self.assertGreater(len(wins), 0)
        
        # Проверяем, что есть выигрыш с вишнями
        cherry_wins = [w for w in wins if w['symbol'] == Symbol.CHERRY]
        self.assertGreater(len(cherry_wins), 0)
    
    def test_check_scatter_win(self):
        """Тест выигрыша разбросанных символов"""
        # Создаем сетку с тремя семерками
        reels = [
            [Symbol.SEVEN, Symbol.LEMON, Symbol.ORANGE],
            [Symbol.CHERRY, Symbol.SEVEN, Symbol.ORANGE],
            [Symbol.CHERRY, Symbol.LEMON, Symbol.SEVEN]
        ]
        
        wins = self.win_checker.check_all_wins(reels, 10)
        
        # Должен быть выигрыш разбросанных символов
        scatter_wins = [w for w in wins if w['type'] == 'scatter_win']
        self.assertGreater(len(scatter_wins), 0)
    
    def test_check_wild_win(self):
        """Тест выигрыша с дикими символами"""
        # Создаем сетку с двумя бриллиантами
        reels = [
            [Symbol.DIAMOND, Symbol.LEMON, Symbol.ORANGE],
            [Symbol.CHERRY, Symbol.DIAMOND, Symbol.ORANGE],
            [Symbol.CHERRY, Symbol.LEMON, Symbol.ORANGE]
        ]
        
        wins = self.win_checker.check_all_wins(reels, 10)
        
        # Должен быть выигрыш с дикими символами
        wild_wins = [w for w in wins if w['type'] == 'wild_win']
        self.assertGreater(len(wild_wins), 0)
    
    def test_get_total_payout(self):
        """Тест подсчета общего выигрыша"""
        wins = [
            {'payout': 50},
            {'payout': 25},
            {'payout': 10}
        ]
        
        total = self.win_checker.get_total_payout(wins)
        self.assertEqual(total, 85)


class TestSlotGameManager(unittest.TestCase):
    """Тесты для менеджера игры"""
    
    def setUp(self):
        # Создаем мок для BalanceManager
        self.balance_manager = Mock(spec=BalanceManager)
        self.balance_manager.get_balance.return_value = 1000
        self.balance_manager.can_place_bet.return_value = True
        self.balance_manager.apply_bet_result.return_value = 990
        self.balance_manager.deposit.return_value = None
        
        self.game_manager = SlotGameManager(self.balance_manager)
    
    def test_set_bet_valid(self):
        """Тест установки валидной ставки"""
        result = self.game_manager.set_bet(50)
        self.assertTrue(result)
        self.assertEqual(self.game_manager.current_bet, 50)
    
    def test_set_bet_invalid(self):
        """Тест установки невалидной ставки"""
        self.balance_manager.can_place_bet.return_value = False
        
        result = self.game_manager.set_bet(50)
        self.assertFalse(result)
    
    def test_spin_success(self):
        """Тест успешного вращения"""
        result, wins, payout = self.game_manager.spin()
        
        # Проверяем, что результат получен
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        
        # Проверяем, что все символы валидны
        for symbol in result:
            self.assertIsInstance(symbol, Symbol)
    
    def test_can_spin(self):
        """Тест проверки возможности вращения"""
        self.assertTrue(self.game_manager.can_spin())
        
        # Устанавливаем ставку больше баланса
        self.balance_manager.can_place_bet.return_value = False
        self.assertFalse(self.game_manager.can_spin())
    
    def test_get_stats(self):
        """Тест получения статистики"""
        stats = self.game_manager.get_stats()
        
        self.assertIn('balance', stats)
        self.assertIn('current_bet', stats)
        self.assertIn('total_spins', stats)
        self.assertIn('win_rate', stats)
    
    def test_get_available_bets(self):
        """Тест получения доступных ставок"""
        bets = self.game_manager.get_available_bets()
        
        self.assertIsInstance(bets, list)
        self.assertGreater(len(bets), 0)
        
        # Проверяем, что все ставки положительные
        for bet in bets:
            self.assertGreater(bet, 0)


class TestSlotGameState(unittest.TestCase):
    """Тесты для состояния игры"""
    
    def setUp(self):
        self.game_state = SlotGameState()
    
    def test_to_dict(self):
        """Тест преобразования в словарь"""
        data = self.game_state.to_dict()
        
        self.assertIn('total_spins', data)
        self.assertIn('total_wins', data)
        self.assertIn('symbol_stats', data)
        self.assertIn('win_line_stats', data)
    
    def test_from_dict(self):
        """Тест создания из словаря"""
        data = {
            'total_spins': 10,
            'total_wins': 3,
            'total_bet': 100,
            'total_payout': 150,
            'biggest_win': 50,
            'current_streak': 2,
            'longest_streak': 5,
            'last_win_time': None,
            'games_played': 10,
            'symbol_stats': {'🍒': 5, '🍋': 3, '🍊': 2},
            'win_line_stats': {'horizontal': 2, 'diagonal_left': 1}
        }
        
        state = SlotGameState.from_dict(data)
        
        self.assertEqual(state.total_spins, 10)
        self.assertEqual(state.total_wins, 3)
        self.assertEqual(state.biggest_win, 50)
        self.assertEqual(state.current_streak, 2)
        self.assertEqual(state.longest_streak, 5)


class TestSymbol(unittest.TestCase):
    """Тесты для символов"""
    
    def test_symbol_values(self):
        """Тест значений символов"""
        # Проверяем, что все символы имеют эмодзи
        for symbol in Symbol:
            self.assertIsInstance(symbol.value, str)
            self.assertGreater(len(symbol.value), 0)
    
    def test_symbol_enum(self):
        """Тест перечисления символов"""
        # Проверяем, что все символы уникальны
        symbols = list(Symbol)
        self.assertEqual(len(symbols), len(set(symbols)))


if __name__ == '__main__':
    # Создаем тестовый набор
    test_suite = unittest.TestSuite()
    
    # Добавляем тесты
    test_classes = [
        TestSlotMachine,
        TestSlotWinChecker,
        TestSlotGameManager,
        TestSlotGameState,
        TestSymbol
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Выводим результат
    if result.wasSuccessful():
        print("\n✅ Все тесты прошли успешно!")
    else:
        print(f"\n❌ Тесты завершились с ошибками: {len(result.failures)} неудач, {len(result.errors)} ошибок")
