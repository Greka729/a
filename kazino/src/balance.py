import json
import os
from typing import Any, Dict


class BalanceManager:
    """Manages user balance with JSON persistence."""

    def __init__(self, storage_path: str = os.path.join("data", "balance.json"), default_balance: int = 1000) -> None:
        self.storage_path = storage_path
        self.default_balance = default_balance
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self._state: Dict[str, Any] = {"balance": default_balance}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.storage_path):
            self._save()
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and isinstance(data.get("balance"), (int, float)):
                    self._state["balance"] = int(data["balance"])
                else:
                    self._save()
        except Exception:
            # In case of corrupted file, reset to default
            self._state["balance"] = self.default_balance
            self._save()

    def _save(self) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)

    def get_balance(self) -> int:
        return int(self._state["balance"])  # ensure int

    def deposit(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self._state["balance"] = int(self._state["balance"]) + int(amount)
        self._save()

    def can_place_bet(self, amount: int) -> bool:
        return amount > 0 and self.get_balance() >= amount

    def apply_bet_result(self, bet_amount: int, payout_multiplier: float) -> int:
        """
        Apply bet result: subtract bet, then add winnings according to multiplier.
        multiplier examples: 0.0 (lose), 1.0 (push), 2.0 (win even money), 2.5, 3.0, etc.
        Returns new balance.
        """
        if bet_amount <= 0:
            raise ValueError("Ставка должна быть положительной")
        if not self.can_place_bet(bet_amount):
            raise ValueError("Недостаточно средств для ставки")

        balance = self.get_balance()
        balance -= bet_amount
        winnings = int(round(bet_amount * payout_multiplier))
        balance += winnings
        self._state["balance"] = balance
        self._save()
        return balance


