from typing import Iterable, List


def prompt_int(prompt: str, min_value: int | None = None, max_value: int | None = None) -> int:
    while True:
        try:
            raw = input(prompt).strip()
            value = int(raw)
            if min_value is not None and value < min_value:
                print(f"Введите число не меньше {min_value}.")
                continue
            if max_value is not None and value > max_value:
                print(f"Введите число не больше {max_value}.")
                continue
            return value
        except ValueError:
            print("Некорректный ввод. Введите целое число.")


def prompt_choice(prompt: str, options: Iterable[str]) -> str:
    normalized: List[str] = [str(opt).strip().lower() for opt in options]
    while True:
        choice = input(prompt).strip().lower()
        if choice in normalized:
            return choice
        print(f"Выберите из: {', '.join(options)}")


def prompt_bet_amount(get_balance_fn, min_bet: int = 1) -> int:
    while True:
        balance = int(get_balance_fn())
        print(f"Текущий баланс: {balance}")
        amount = prompt_int(f"Введите сумму ставки (мин. {min_bet}): ", min_value=min_bet)
        if amount > balance:
            print("Недостаточно средств для этой ставки.")
            continue
        return amount


