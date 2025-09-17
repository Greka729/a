#!/usr/bin/env python3
"""
Скрипт для запуска тестов слот-машины
"""

import sys
import os
import unittest

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_slot_tests():
    """Запустить тесты слот-машины"""
    print("🎰 Запуск тестов слот-машины...")
    print("=" * 50)
    
    # Импортируем тесты
    from tests.test_slot_machine import (
        TestSlotMachine,
        TestSlotWinChecker, 
        TestSlotGameManager,
        TestSlotGameState,
        TestSymbol
    )
    
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
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ Все тесты прошли успешно!")
        print(f"Запущено тестов: {result.testsRun}")
        return True
    else:
        print(f"❌ Тесты завершились с ошибками:")
        print(f"   Неудач: {len(result.failures)}")
        print(f"   Ошибок: {len(result.errors)}")
        print(f"   Запущено тестов: {result.testsRun}")
        
        if result.failures:
            print("\nНеудачные тесты:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
        
        if result.errors:
            print("\nОшибки:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('\\n')[-2]}")
        
        return False

def run_quick_test():
    """Быстрый тест основных функций"""
    print("🚀 Быстрый тест основных функций...")
    
    try:
        # Тест импорта модулей
        from games.slot_machine import SlotMachine, Symbol
        from games.slot_win_checker import SlotWinChecker
        from games.slot_game_manager import SlotGameManager
        from balance import BalanceManager
        
        print("✅ Импорт модулей успешен")
        
        # Тест создания объектов
        slot_machine = SlotMachine()
        win_checker = SlotWinChecker()
        balance_manager = BalanceManager()
        game_manager = SlotGameManager(balance_manager)
        
        print("✅ Создание объектов успешно")
        
        # Тест базовой функциональности
        result = slot_machine.spin_reels()
        assert len(result) == 3, "Должно быть 3 символа"
        assert all(isinstance(s, Symbol) for s in result), "Все символы должны быть валидными"
        
        print("✅ Базовая функциональность работает")
        
        # Тест проверки выигрыша
        is_win, payout = slot_machine.check_win(result, 10)
        assert isinstance(is_win, bool), "is_win должен быть булевым"
        assert isinstance(payout, int), "payout должен быть целым числом"
        
        print("✅ Проверка выигрыша работает")
        
        print("\n🎉 Все быстрые тесты прошли успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в быстром тесте: {e}")
        return False

if __name__ == "__main__":
    print("🎰 Тестирование слот-машины казино")
    print("=" * 50)
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        success = run_quick_test()
    else:
        success = run_slot_tests()
    
    # Завершаем с соответствующим кодом
    sys.exit(0 if success else 1)
