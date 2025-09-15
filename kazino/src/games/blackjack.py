import random
from typing import List, Tuple

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def create_deck(shuffles: int = 3) -> List[str]:
    deck = [f"{rank}{suit}" for suit in SUITS for rank in RANKS]
    for _ in range(shuffles):
        random.shuffle(deck)
    return deck


def hand_value(cards: List[str]) -> int:
    value = 0
    aces = 0
    for card in cards:
        rank = card[:-1]
        if rank in {"J", "Q", "K"}:
            value += 10
        elif rank == "A":
            aces += 1
            value += 11
        else:
            value += int(rank)
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value


def deal_card(deck: List[str]) -> Tuple[str, List[str]]:
    return deck.pop(), deck


def play_round_decision(deck: List[str], player_actions: List[str]) -> Tuple[float, List[str], List[str]]:
    """
    Simulate a round given a sequence of player actions (e.g., ["hit", "stand"]).
    Returns: payout_multiplier, player_hand, dealer_hand
    """
    player: List[str] = []
    dealer: List[str] = []
    # initial deal
    for _ in range(2):
        c, deck = deal_card(deck)
        player.append(c)
        c, deck = deal_card(deck)
        dealer.append(c)

    # player actions
    for action in player_actions:
        if action == "hit":
            c, deck = deal_card(deck)
            player.append(c)
            if hand_value(player) > 21:
                return 0.0, player, dealer
        elif action == "stand":
            break

    # dealer plays: hit until 17 or more
    while hand_value(dealer) < 17:
        c, deck = deal_card(deck)
        dealer.append(c)

    player_total = hand_value(player)
    dealer_total = hand_value(dealer)

    if player_total > 21:
        return 0.0, player, dealer
    if dealer_total > 21:
        return 2.0, player, dealer
    if player_total > dealer_total:
        return 2.0, player, dealer
    if player_total < dealer_total:
        return 0.0, player, dealer
    return 1.0, player, dealer  # push

try:
    from src.core.game import register_game
    from src.utils import prompt_choice
except ModuleNotFoundError:
    from core.game import register_game  # type: ignore
    from utils import prompt_choice  # type: ignore


class BlackjackGame:
    id = "blackjack"
    name = "Блэкджек"

    def run_cli(self, balance_manager) -> None:
        amount = _prompt_bet(balance_manager)
        if amount is None:
            return
        deck = create_deck()
        actions: List[str] = []
        while True:
            action = prompt_choice("Ваш ход (hit/stand): ", ["hit", "stand"]).lower()
            actions.append(action)
            if action == "stand":
                break
        mult, player, dealer = play_round_decision(deck, actions)
        new_balance = balance_manager.apply_bet_result(amount, mult)
        print(
            f"Ваши карты: {' '.join(player)} | Очки: {hand_value(player)}\n"
            f"Карты дилера: {' '.join(dealer)} | Очки: {hand_value(dealer)}\n"
            f"Выплата x{mult}. Баланс: {new_balance}"
        )


def _prompt_bet(balance_manager):
    try:
        from src.utils import prompt_bet_amount  # type: ignore
    except ModuleNotFoundError:
        from utils import prompt_bet_amount  # type: ignore
    return prompt_bet_amount(balance_manager.get_balance, min_bet=10)


register_game(BlackjackGame)


