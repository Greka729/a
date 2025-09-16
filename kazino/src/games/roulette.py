import random
from typing import Literal, Tuple

Color = Literal["red", "black", "green"]


def spin_wheel() -> Tuple[int, Color]:
    number = random.randint(0, 36)
    if number == 0:
        color: Color = "green"
    else:
        # True European roulette color mapping
        red_numbers = {
            1, 3, 5, 7, 9,
            12, 14, 16, 18,
            19, 21, 23, 25, 27,
            30, 32, 34, 36,
        }
        color = "red" if number in red_numbers else "black"
    return number, color


def resolve_bet(
    bet_type: Literal[
        "color",
        "number",
        "even_odd",
        "low_high",
        "dozen",
        "column",
    ],
    selection: str,
    outcome_number: int,
    outcome_color: Color,
) -> float:
    # Straight number
    if bet_type == "number":
        try:
            selected_num = int(selection)
        except ValueError:
            return 0.0
        return 36.0 if selected_num == outcome_number else 0.0

    # Color bet (0 always loses)
    if bet_type == "color":
        if selection not in {"red", "black"}:
            return 0.0
        if outcome_number == 0:
            return 0.0
        return 2.0 if selection == outcome_color else 0.0

    # Even/Odd (0 loses)
    if bet_type == "even_odd":
        sel = selection.lower()
        if outcome_number == 0 or sel not in {"even", "odd"}:
            return 0.0
        is_even = outcome_number % 2 == 0
        return 2.0 if (is_even and sel == "even") or ((not is_even) and sel == "odd") else 0.0

    # Low/High (1-18 / 19-36). 0 loses
    if bet_type == "low_high":
        sel = selection.lower()
        if outcome_number == 0 or sel not in {"low", "high"}:
            return 0.0
        if sel == "low":
            return 2.0 if 1 <= outcome_number <= 18 else 0.0
        return 2.0 if 19 <= outcome_number <= 36 else 0.0

    # Dozens: 1st (1-12), 2nd (13-24), 3rd (25-36). 0 loses
    if bet_type == "dozen":
        sel = selection.lower()
        if outcome_number == 0 or sel not in {"1st", "2nd", "3rd", "first", "second", "third"}:
            return 0.0
        if sel in {"1st", "first"}:
            return 3.0 if 1 <= outcome_number <= 12 else 0.0
        if sel in {"2nd", "second"}:
            return 3.0 if 13 <= outcome_number <= 24 else 0.0
        return 3.0 if 25 <= outcome_number <= 36 else 0.0

    # Columns: col1 (1,4,7,...), col2, col3 (0 loses)
    if bet_type == "column":
        sel = selection.lower()
        if outcome_number == 0 or sel not in {"col1", "col2", "col3"}:
            return 0.0
        mod = outcome_number % 3
        # mod 1 -> col1, mod 2 -> col2, mod 0 -> col3
        hit = (mod == 1 and sel == "col1") or (mod == 2 and sel == "col2") or (mod == 0 and sel == "col3")
        return 3.0 if hit else 0.0

    return 0.0

try:
    from src.core.game import Game, register_game
    from src.utils import prompt_choice, prompt_int
except ModuleNotFoundError:
    # direct run fallback
    from core.game import Game, register_game  # type: ignore
    from utils import prompt_choice, prompt_int  # type: ignore


class RouletteGame:
    id = "roulette"
    name = "Рулетка"

    def run_cli(self, balance_manager) -> None:
        amount = _prompt_bet(balance_manager)
        if amount is None:
            return
        bet_type = prompt_choice("Ставка на 'color' или 'number'? ", ["color", "number"]).lower()
        if bet_type == "color":
            selection = prompt_choice("Выберите цвет (red/black): ", ["red", "black"]).lower()
        else:
            selection = str(prompt_int("Выберите номер (0-36): ", min_value=0, max_value=36))
        num, col = spin_wheel()
        mult = resolve_bet(bet_type, selection, num, col)
        new_balance = balance_manager.apply_bet_result(amount, mult)
        print(f"Выпало: {num} ({col}). Выплата x{mult}. Баланс: {new_balance}")


def _prompt_bet(balance_manager):
    try:
        from src.utils import prompt_bet_amount  # type: ignore
    except ModuleNotFoundError:
        from utils import prompt_bet_amount  # type: ignore
    return prompt_bet_amount(balance_manager.get_balance)


register_game(RouletteGame)


