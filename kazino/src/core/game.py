from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Protocol


@dataclass
class GameResult:
    payout_multiplier: float
    message: str


class Game(Protocol):
    id: str
    name: str

    def run_cli(self, balance_manager) -> None:  # pragma: no cover - UI glue
        ...


_REGISTRY: Dict[str, Game] = {}


def register_game(factory: Callable[[], Game]) -> Game:
    game = factory()
    if game.id in _REGISTRY:
        raise ValueError(f"Game with id '{game.id}' already registered")
    _REGISTRY[game.id] = game
    return game


def list_games() -> Dict[str, Game]:
    return dict(_REGISTRY)


