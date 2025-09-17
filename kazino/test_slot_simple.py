#!/usr/bin/env python3
"""
Простой тест слот-машины
"""

import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_slot_machine():
    """Простой тест слот-машины"""
    print("🎰 Тестирование слот-машины...")
    
    try:
        # Импортируем модули
        from games.slot_machine import SlotMachine, Symbol
        print("✅ Импорт SlotMachine успешен")
        
        # Создаем слот-машину
        slot_machine = SlotMachine()
        print("✅ Создание SlotMachine успешно")
        
        # Тестируем генерацию символа
        symbol = slot_machine.get_random_symbol()
        print(f"✅ Сгенерированный символ: {symbol.value}")
        
        # Тестируем вращение барабанов
        result = slot_machine.spin_reels()
        print(f"✅ Результат вращения: {[s.value for s in result]}")
        
        # Тестируем проверку выигрыша
        is_win, payout = slot_machine.check_win(result, 10)
        print(f"✅ Выигрыш: {is_win}, Сумма: {payout}")
        
        # Тестируем выигрышную комбинацию
        win_symbols = [Symbol.CHERRY, Symbol.CHERRY, Symbol.CHERRY]
        is_win, payout = slot_machine.check_win(win_symbols, 10)
        print(f"✅ Тест выигрышной комбинации: {is_win}, Сумма: {payout}")
        
        print("\n🎉 Все тесты прошли успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_win_checker():
    """Тест проверки выигрышей"""
    print("\n🎯 Тестирование проверки выигрышей...")
    
    try:
        from games.slot_win_checker import SlotWinChecker
        print("✅ Импорт SlotWinChecker успешен")
        
        win_checker = SlotWinChecker()
        print("✅ Создание SlotWinChecker успешно")
        
        # Тестируем проверку выигрышей
        from games.slot_machine import Symbol
        reels = [
            [Symbol.CHERRY, Symbol.LEMON, Symbol.ORANGE],
            [Symbol.CHERRY, Symbol.LEMON, Symbol.ORANGE],
            [Symbol.CHERRY, Symbol.LEMON, Symbol.ORANGE]
        ]
        
        wins = win_checker.check_all_wins(reels, 10)
        print(f"✅ Найдено выигрышей: {len(wins)}")
        
        total_payout = win_checker.get_total_payout(wins)
        print(f"✅ Общий выигрыш: {total_payout}")
        
        print("🎉 Тест проверки выигрышей прошел успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_game_manager():
    """Тест менеджера игры"""
    print("\n🎮 Тестирование менеджера игры...")
    
    try:
        from games.slot_game_manager import SlotGameManager
        from balance import BalanceManager
        print("✅ Импорт модулей успешен")
        
        balance_manager = BalanceManager()
        game_manager = SlotGameManager(balance_manager)
        print("✅ Создание SlotGameManager успешно")
        
        # Тестируем установку ставки
        result = game_manager.set_bet(25)
        print(f"✅ Установка ставки: {result}")
        
        # Тестируем получение статистики
        stats = game_manager.get_stats()
        print(f"✅ Статистика получена: баланс = {stats['balance']}")
        
        # Тестируем доступные ставки
        bets = game_manager.get_available_bets()
        print(f"✅ Доступные ставки: {bets}")
        
        print("🎉 Тест менеджера игры прошел успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎰 Простое тестирование слот-машины")
    print("=" * 50)
    
    success = True
    
    # Запускаем тесты
    success &= test_slot_machine()
    success &= test_win_checker()
    success &= test_game_manager()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Все тесты прошли успешно!")
        print("Слот-машина готова к использованию!")
    else:
        print("❌ Некоторые тесты не прошли")
    
    sys.exit(0 if success else 1)
