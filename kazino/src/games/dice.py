import random


def roll_dice() -> int:
    return random.randint(1, 6)


def resolve_guess(guess: int, outcome: int) -> float:
    """Return payout multiplier. Exact guess pays 6x (fair)."""
    if guess == outcome:
        return 6.0
    return 0.0

try:
    from src.core.game import register_game
    from src.utils import prompt_int
except ModuleNotFoundError:
    from core.game import register_game  # type: ignore
    from utils import prompt_int  # type: ignore


class DiceGame:
    id = "dice"
    name = "Кости"

    def run_cli(self, balance_manager) -> None:
        amount = _prompt_bet(balance_manager)
        if amount is None:
            return
        guess = prompt_int("Угадайте число (1-6): ", min_value=1, max_value=6)
        outcome = roll_dice()
        mult = resolve_guess(guess, outcome)
        new_balance = balance_manager.apply_bet_result(amount, mult)
        print(f"Выпало: {outcome}. Выплата x{mult}. Баланс: {new_balance}")


def _prompt_bet(balance_manager):
    try:
        from src.utils import prompt_bet_amount  # type: ignore
    except ModuleNotFoundError:
        from utils import prompt_bet_amount  # type: ignore
    return prompt_bet_amount(balance_manager.get_balance)


register_game(DiceGame)


