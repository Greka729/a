#!/usr/bin/env python3
"""
Демонстрационный скрипт для слот-машины
Показывает основные возможности без графического интерфейса
"""

import sys
import os
import time
import random

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_header():
    """Печать заголовка"""
    print("🎰" + "=" * 60 + "🎰")
    print("           ДЕМОНСТРАЦИЯ СЛОТ-МАШИНЫ")
    print("🎰" + "=" * 60 + "🎰")
    print()

def print_symbols_info():
    """Показать информацию о символах"""
    print("📋 СИМВОЛЫ И ВЫПЛАТЫ:")
    print("-" * 40)
    
    symbols_info = [
        ("🍒 Вишня", "25%", "x2", "x5"),
        ("🍋 Лимон", "20%", "x3", "x10"),
        ("🍊 Апельсин", "20%", "x3", "x10"),
        ("🍇 Слива", "15%", "x5", "x15"),
        ("🔔 Колокол", "10%", "x8", "x25"),
        ("📊 Бар", "5%", "x15", "x50"),
        ("7️⃣ Семерка", "3%", "x25", "x100"),
        ("💎 Бриллиант", "2%", "x100", "x500")
    ]
    
    print(f"{'Символ':<12} {'Вероятность':<12} {'2x':<8} {'3x':<8}")
    print("-" * 40)
    for symbol, prob, two, three in symbols_info:
        print(f"{symbol:<12} {prob:<12} {two:<8} {three:<8}")
    print()

def demo_single_spin():
    """Демонстрация одного вращения"""
    print("🎲 ДЕМОНСТРАЦИЯ ВРАЩЕНИЯ:")
    print("-" * 30)
    
    try:
        from games.slot_machine import SlotMachine
        
        slot_machine = SlotMachine()
        
        # Показываем анимацию вращения
        print("Вращение барабанов...", end="", flush=True)
        for i in range(3):
            time.sleep(0.5)
            print(".", end="", flush=True)
        print()
        
        # Получаем результат
        result = slot_machine.spin_reels()
        
        # Показываем результат
        print(f"Результат: {' | '.join([s.value for s in result])}")
        
        # Проверяем выигрыш
        bet = 10
        is_win, payout = slot_machine.check_win(result, bet)
        
        if is_win:
            print(f"🎉 ВЫИГРЫШ! Выигрыш: ${payout} (ставка: ${bet})")
        else:
            print(f"😔 Проигрыш. Ставка: ${bet}")
        
        print()
        return is_win, payout
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False, 0

def demo_multiple_spins():
    """Демонстрация множественных вращений"""
    print("🎯 ДЕМОНСТРАЦИЯ СТАТИСТИКИ (10 вращений):")
    print("-" * 45)
    
    try:
        from games.slot_machine import SlotMachine
        
        slot_machine = SlotMachine()
        
        total_bet = 0
        total_payout = 0
        wins = 0
        
        for i in range(10):
            bet = 10
            total_bet += bet
            
            result = slot_machine.spin_reels()
            is_win, payout = slot_machine.check_win(result, bet)
            
            if is_win:
                wins += 1
                total_payout += payout
                status = f"🎉 ВЫИГРЫШ ${payout}"
            else:
                status = "😔 Проигрыш"
            
            print(f"Спин {i+1:2d}: {' | '.join([s.value for s in result])} - {status}")
            time.sleep(0.3)
        
        print("-" * 45)
        print(f"Итого ставок: ${total_bet}")
        print(f"Итого выигрышей: ${total_payout}")
        print(f"Количество выигрышей: {wins}/10")
        print(f"Процент выигрышей: {wins*10}%")
        print(f"RTP (Return to Player): {(total_payout/total_bet*100):.1f}%")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def demo_win_checker():
    """Демонстрация проверки выигрышей"""
    print("🔍 ДЕМОНСТРАЦИЯ ПРОВЕРКИ ВЫИГРЫШЕЙ:")
    print("-" * 40)
    
    try:
        from games.slot_win_checker import SlotWinChecker
        from games.slot_machine import Symbol
        
        win_checker = SlotWinChecker()
        
        # Тестовые комбинации
        test_cases = [
            ([Symbol.CHERRY, Symbol.CHERRY, Symbol.CHERRY], "Три вишни"),
            ([Symbol.SEVEN, Symbol.SEVEN, Symbol.SEVEN], "Три семерки"),
            ([Symbol.DIAMOND, Symbol.DIAMOND, Symbol.DIAMOND], "Три бриллианта"),
            ([Symbol.CHERRY, Symbol.LEMON, Symbol.ORANGE], "Разные символы"),
            ([Symbol.SEVEN, Symbol.LEMON, Symbol.SEVEN], "Две семерки"),
        ]
        
        for symbols, description in test_cases:
            wins = win_checker.check_all_wins([symbols], 10)
            total_payout = win_checker.get_total_payout(wins)
            
            print(f"{description}: {' | '.join([s.value for s in symbols])}")
            print(f"  Выигрышей: {len(wins)}, Общий выигрыш: ${total_payout}")
            
            for win in wins:
                print(f"    - {win_checker.get_win_description(win)}: ${win['payout']}")
            print()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def demo_game_manager():
    """Демонстрация менеджера игры"""
    print("🎮 ДЕМОНСТРАЦИЯ МЕНЕДЖЕРА ИГРЫ:")
    print("-" * 35)
    
    try:
        from games.slot_game_manager import SlotGameManager
        from balance import BalanceManager
        
        # Создаем менеджер с начальным балансом
        balance_manager = BalanceManager()
        balance_manager.deposit(1000)  # Начальный баланс
        game_manager = SlotGameManager(balance_manager)
        
        print(f"Начальный баланс: ${game_manager.get_balance()}")
        
        # Устанавливаем ставку
        game_manager.set_bet(25)
        print(f"Установлена ставка: ${game_manager.current_bet}")
        
        # Делаем несколько спинов
        for i in range(5):
            if game_manager.can_spin():
                result, wins, payout = game_manager.spin()
                
                print(f"Спин {i+1}: {' | '.join([s.value for s in result])}")
                if payout > 0:
                    print(f"  🎉 Выигрыш: ${payout}")
                else:
                    print(f"  😔 Проигрыш")
                print(f"  Баланс: ${game_manager.get_balance()}")
                print()
            else:
                print("Недостаточно средств для игры")
                break
        
        # Показываем статистику
        stats = game_manager.get_stats()
        print("📊 СТАТИСТИКА:")
        print(f"  Всего спинов: {stats['total_spins']}")
        print(f"  Выигрышей: {stats['total_wins']}")
        print(f"  Процент выигрышей: {stats['win_rate']}%")
        print(f"  Самый большой выигрыш: ${stats['biggest_win']}")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def interactive_demo():
    """Интерактивная демонстрация"""
    print("🎮 ИНТЕРАКТИВНАЯ ДЕМОНСТРАЦИЯ:")
    print("-" * 35)
    print("Нажмите Enter для вращения, 'q' для выхода")
    print()
    
    try:
        from games.slot_machine import SlotMachine
        
        slot_machine = SlotMachine()
        balance = 100
        bet = 10
        
        print(f"Начальный баланс: ${balance}")
        print(f"Ставка: ${bet}")
        print()
        
        while balance >= bet:
            user_input = input("Нажмите Enter для вращения (или 'q' для выхода): ").strip().lower()
            
            if user_input == 'q':
                break
            
            balance -= bet
            result = slot_machine.spin_reels()
            is_win, payout = slot_machine.check_win(result, bet)
            
            if is_win:
                balance += payout
                print(f"🎉 ВЫИГРЫШ! {' | '.join([s.value for s in result])} - Выигрыш: ${payout}")
            else:
                print(f"😔 Проигрыш: {' | '.join([s.value for s in result])}")
            
            print(f"Баланс: ${balance}")
            print()
        
        print("Игра окончена! Спасибо за игру!")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    """Главная функция демонстрации"""
    print_header()
    
    # Показываем информацию о символах
    print_symbols_info()
    
    # Демонстрации
    demo_single_spin()
    demo_multiple_spins()
    demo_win_checker()
    demo_game_manager()
    
    # Спрашиваем, хочет ли пользователь интерактивную демонстрацию
    print("🎮 Хотите попробовать интерактивную демонстрацию? (y/n): ", end="")
    try:
        if input().strip().lower() in ['y', 'yes', 'да', 'д']:
            interactive_demo()
    except KeyboardInterrupt:
        print("\nДемонстрация прервана пользователем")
    
    print("🎰" + "=" * 60 + "🎰")
    print("           ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("🎰" + "=" * 60 + "🎰")
    print()
    print("Для запуска полной графической версии используйте:")
    print("python src/pygame_app.py")
    print()

if __name__ == "__main__":
    main()
