from __future__ import annotations

import sys
from typing import List

try:
    from src.balance import BalanceManager
    from src.utils import prompt_int, prompt_choice, prompt_bet_amount
    from src.games.roulette import spin_wheel, resolve_bet as roulette_resolve
    from src.games.dice import roll_dice, resolve_guess
    from src.games.blackjack import create_deck, play_round_decision
except ModuleNotFoundError:
    # Allow running this file directly: python src/main.py
    import os
    import sys
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    if CURRENT_DIR not in sys.path:
        sys.path.append(CURRENT_DIR)
    from balance import BalanceManager  # type: ignore  # noqa: E402
    from utils import prompt_int, prompt_choice, prompt_bet_amount  # type: ignore  # noqa: E402
    from games.roulette import spin_wheel, resolve_bet as roulette_resolve  # type: ignore  # noqa: E402
    from games.dice import roll_dice, resolve_guess  # type: ignore  # noqa: E402
    from games.blackjack import create_deck, play_round_decision  # type: ignore  # noqa: E402
try:
    from src.core.game import list_games  # new registry
except ModuleNotFoundError:
    from core.game import list_games  # type: ignore


def menu() -> int:
    games = list(list_games().values())
    print("\n=== Казино ===")
    for idx, game in enumerate(games, start=1):
        print(f"{idx}) {game.name}")
    print(f"{len(games)+1}) Пополнить баланс")
    print("0) Выход")
    return prompt_int("Выберите пункт меню: ", min_value=0, max_value=len(games)+1)


def top_up(balance: BalanceManager) -> None:
    amount = prompt_int("Введите сумму пополнения: ", min_value=1)
    try:
        balance.deposit(amount)
        print(f"Баланс пополнен. Новый баланс: {balance.get_balance()}")
    except ValueError as e:
        print(f"Ошибка: {e}")


def play_roulette(balance: BalanceManager) -> None:
    amount = prompt_bet_amount(balance.get_balance)
    choice_type = prompt_choice("Ставка на 'color' или 'number'? ", ["color", "number"])  # noqa: E501
    if choice_type == "color":
        selection = prompt_choice("Выберите цвет (red/black): ", ["red", "black"])  # noqa: E501
    else:
        selection = str(prompt_int("Выберите номер (0-36): ", min_value=0, max_value=36))

    num, col = spin_wheel()
    multiplier = roulette_resolve(choice_type, selection, num, col)
    new_balance = balance.apply_bet_result(amount, multiplier)
    print(f"Выпало: {num} ({col}). Выплата x{multiplier}. Баланс: {new_balance}")


def play_dice(balance: BalanceManager) -> None:
    amount = prompt_bet_amount(balance.get_balance)
    guess = prompt_int("Угадайте число (1-6): ", min_value=1, max_value=6)
    outcome = roll_dice()
    multiplier = resolve_guess(guess, outcome)
    new_balance = balance.apply_bet_result(amount, multiplier)
    print(f"Выпало: {outcome}. Выплата x{multiplier}. Баланс: {new_balance}")


def play_blackjack(balance: BalanceManager) -> None:
    amount = prompt_bet_amount(balance.get_balance, min_bet=10)
    deck = create_deck()
    actions: List[str] = []
    while True:
        action = prompt_choice("Ваш ход (hit/stand): ", ["hit", "stand"])
        actions.append(action)
        if action == "stand":
            break
        # If player busts, play_round_decision will handle
        # We collect actions until stand or bust
    multiplier, player, dealer = play_round_decision(deck, actions)
    new_balance = balance.apply_bet_result(amount, multiplier)
    print(f"Ваши карты: {' '.join(player)} | Очки: {sum_blackjack(player)}")
    print(f"Карты дилера: {' '.join(dealer)} | Очки: {sum_blackjack(dealer)}")
    print(f"Выплата x{multiplier}. Баланс: {new_balance}")


def sum_blackjack(cards: List[str]) -> int:
    # Helper mirrors blackjack.hand_value without importing to avoid UI cross-talk
    total = 0
    aces = 0
    for card in cards:
        rank = card[:-1]
        if rank in {"J", "Q", "K"}:
            total += 10
        elif rank == "A":
            aces += 1
            total += 11
        else:
            total += int(rank)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def main() -> None:
    balance = BalanceManager()
    print("Добро пожаловать в казино!")
    while True:
        print(f"Текущий баланс: {balance.get_balance()}")
        choice = menu()
        if choice == 0:
            print("До встречи!")
            sys.exit(0)
        games = list(list_games().values())
        if 1 <= choice <= len(games):
            games[choice - 1].run_cli(balance)
        elif choice == len(games) + 1:
            top_up(balance)


if __name__ == "__main__":
    main()


