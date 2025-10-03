from __future__ import annotations

from typing import List

try:
    from src.core.game import register_game
    from src.utils import prompt_choice, prompt_bet_amount
    from src.games.slot_game_manager import SlotGameManager
except ModuleNotFoundError:  # direct run fallback
    from core.game import register_game  # type: ignore
    from utils import prompt_choice, prompt_bet_amount  # type: ignore
    from games.slot_game_manager import SlotGameManager  # type: ignore


class SlotCLIGame:
    id = "slot"
    name = "Слоты"

    def run_cli(self, balance_manager) -> None:  # pragma: no cover - UI glue
        manager = SlotGameManager(balance_manager)
        while True:
            print("\n=== Слоты ===")
            print(f"Баланс: {manager.get_balance()}")
            print(f"Текущая ставка: {manager.current_bet}")
            action = prompt_choice("Действие (bet/spin/info/back): ", ["bet", "spin", "info", "back"]).lower()
            if action == "back":
                return
            if action == "bet":
                amount = prompt_bet_amount(manager.get_balance)
                if not manager.set_bet(amount):
                    print("Невозможно установить ставку. Проверьте баланс.")
                continue
            if action == "info":
                stats = manager.get_stats()
                print(
                    f"Спинов: {stats['total_spins']} | Побед: {stats['total_wins']} | WinRate: {stats['win_rate']}% | RTP: {stats['rtp']}%"
                )
                continue
            if action == "spin":
                if not manager.can_spin():
                    print("Недостаточно средств для ставки. Измените ставку или пополните баланс.")
                    continue
                result, wins, total = manager.spin()
                symbols_line = " ".join(s.value for s in result)
                if total > 0:
                    details: List[str] = [f"{w['count']}x {w['symbol'].value} = +{w['payout']}" for w in wins]
                    print(f"Результат: {symbols_line} | Выигрыш: {total} | {'; '.join(details)} | Баланс: {manager.get_balance()}")
                else:
                    print(f"Результат: {symbols_line} | Проигрыш | Баланс: {manager.get_balance()}")


register_game(SlotCLIGame)


