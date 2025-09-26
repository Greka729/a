from __future__ import annotations

import sys
from typing import Callable, Dict, Optional, Tuple

from . import operations
from .history import HistoryManager
from .utils import format_result


OperationFunc = Callable[..., float]


def _prompt_number(prompt: str) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("Некорректное число. Повторите ввод.")


def _prompt_menu() -> str:
    print("\nВыберите операцию:")
    print(" 1) Сложение (+)")
    print(" 2) Вычитание (-)")
    print(" 3) Умножение (*)")
    print(" 4) Деление (/)")
    print(" 5) Степень (x^y)")
    print(" 6) Процент (p% от x)")
    print(" 7) Квадратный корень (√x)")
    print(" 8) Логарифм (log_b x)")
    print(" h) Показать историю")
    print(" c) Очистить историю")
    print(" q) Выход")
    return input("Ваш выбор: ").strip().lower()


def _get_operation(choice: str) -> Tuple[str, Optional[OperationFunc]]:
    mapping: Dict[str, Tuple[str, Optional[OperationFunc]]] = {
        "1": ("Сложение", operations.add),
        "+": ("Сложение", operations.add),
        "2": ("Вычитание", operations.subtract),
        "-": ("Вычитание", operations.subtract),
        "3": ("Умножение", operations.multiply),
        "*": ("Умножение", operations.multiply),
        "4": ("Деление", operations.divide),
        "/": ("Деление", operations.divide),
        "5": ("Степень", operations.power),
        "6": ("Процент", None),
        "7": ("Квадратный корень", operations.sqrt),
        "8": ("Логарифм", None),
    }
    return mapping.get(choice, ("", None))


def run_cli() -> None:
    print("Консольный калькулятор (Python). Введите 'q' для выхода.")
    history = HistoryManager()

    while True:
        choice = _prompt_menu()

        if choice in ("q", "quit", "exit"):
            print("Выход. До свидания!")
            return

        if choice == "h":
            rows = history.read_last(10)
            if not rows:
                print("История пуста.")
            else:
                print("Последние вычисления:")
                for timestamp, expr, result_str in rows:
                    print(f"- {timestamp} | {expr} = {result_str}")
            continue

        if choice == "c":
            confirm = input("Точно очистить историю? (y/n): ").strip().lower()
            if confirm in {"y", "yes", "д", "да"}:
                history.clear()
                print("История очищена.")
            else:
                print("Отменено.")
            continue

        label, func = _get_operation(choice)
        if not label and func is None:
            print("Неизвестная операция. Повторите выбор.")
            continue

        try:
            if choice in {"7"}:  # sqrt
                x = _prompt_number("Введите число x: ")
                result = operations.sqrt(x)
                expr = f"sqrt({x})"
            elif choice in {"6"}:  # percent
                x = _prompt_number("Введите число x: ")
                p = _prompt_number("Введите процент p: ")
                result = operations.percent(x, p)
                expr = f"{p}% от {x}"
            elif choice in {"8"}:  # log
                x = _prompt_number("Введите число x (> 0): ")
                base = input("Введите основание b (> 0, != 1) [по умолчанию e]: ").strip()
                if base == "":
                    result = operations.log(x)
                    expr = f"log_e({x})"
                else:
                    try:
                        b = float(base)
                    except ValueError:
                        print("Некорректное основание логарифма.")
                        continue
                    result = operations.log(x, b)
                    expr = f"log_{b}({x})"
            else:
                x = _prompt_number("Введите число x: ")
                y = _prompt_number("Введите число y: ")
                assert func is not None
                result = func(x, y)
                symbol = {
                    "1": "+", "+": "+",
                    "2": "-", "-": "-",
                    "3": "*", "*": "*",
                    "4": "/", "/": "/",
                    "5": "^",
                }.get(choice, "?")
                expr = f"{x} {symbol} {y}"

            print(f"Результат: {format_result(result)}")
            history.append(expr, result)
        except ZeroDivisionError as zde:
            print(f"Ошибка: {zde}")
        except ValueError as ve:
            print(f"Ошибка: {ve}")
        except Exception as ex:
            print(f"Непредвиденная ошибка: {ex}")


if __name__ == "__main__":
    try:
        run_cli()
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")
        sys.exit(0)


