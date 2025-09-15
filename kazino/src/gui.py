from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import List, Tuple
import math

try:
    from src.balance import BalanceManager
    from src.games.roulette import spin_wheel, resolve_bet as roulette_resolve
    from src.games.dice import roll_dice, resolve_guess
    from src.games.blackjack import create_deck, play_round_decision, hand_value
except ModuleNotFoundError:
    # Allow running this file directly: python src/gui.py
    import os
    import sys
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    if CURRENT_DIR not in sys.path:
        sys.path.append(CURRENT_DIR)
    from balance import BalanceManager  # type: ignore  # noqa: E402
    from games.roulette import spin_wheel, resolve_bet as roulette_resolve  # type: ignore  # noqa: E402
    from games.dice import roll_dice, resolve_guess  # type: ignore  # noqa: E402
    from games.blackjack import create_deck, play_round_decision, hand_value  # type: ignore  # noqa: E402


class CasinoApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Казино")
        self.geometry("420x260")
        self.resizable(False, False)

        self.balance = BalanceManager()

        self.balance_var = tk.StringVar(value=f"Баланс: {self.balance.get_balance()}")

        header = tk.Label(self, text="Казино", font=("Segoe UI", 16, "bold"))
        header.pack(pady=8)

        bal_label = tk.Label(self, textvariable=self.balance_var, font=("Segoe UI", 12))
        bal_label.pack(pady=4)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=8)

        tk.Button(btn_frame, text="Рулетка", width=16, command=self.open_roulette_window).grid(row=0, column=0, padx=6, pady=6)
        tk.Button(btn_frame, text="Кости", width=16, command=self.play_dice).grid(row=0, column=1, padx=6, pady=6)
        tk.Button(btn_frame, text="Блэкджек", width=16, command=self.open_blackjack_window).grid(row=1, column=0, padx=6, pady=6)
        tk.Button(btn_frame, text="Пополнить", width=16, command=self.top_up).grid(row=1, column=1, padx=6, pady=6)

        tk.Button(self, text="Выход", command=self.destroy).pack(pady=6)

    def refresh_balance(self) -> None:
        self.balance_var.set(f"Баланс: {self.balance.get_balance()}")

    def ask_bet(self, min_bet: int = 1) -> int | None:
        while True:
            value = simpledialog.askinteger("Ставка", f"Введите сумму ставки (мин. {min_bet})", minvalue=min_bet, parent=self)
            if value is None:
                return None
            if value > self.balance.get_balance():
                messagebox.showwarning("Недостаточно средств", "У вас недостаточно средств для этой ставки.")
                continue
            return value

    def top_up(self) -> None:
        amount = simpledialog.askinteger("Пополнение", "Введите сумму пополнения", minvalue=1, parent=self)
        if amount is None:
            return
        try:
            self.balance.deposit(int(amount))
            self.refresh_balance()
            messagebox.showinfo("Готово", "Баланс пополнен")
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка", str(e))

    def open_roulette_window(self) -> None:
        RouletteWindow(self)

    def play_dice(self) -> None:
        amount = self.ask_bet(min_bet=1)
        if amount is None:
            return
        guess = simpledialog.askinteger("Кости", "Угадайте число (1-6)", minvalue=1, maxvalue=6, parent=self)
        if guess is None:
            return
        rolled = roll_dice()
        multiplier = resolve_guess(int(guess), rolled)
        try:
            new_balance = self.balance.apply_bet_result(int(amount), multiplier)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка", str(e))
            return
        self.refresh_balance()
        messagebox.showinfo("Результат", f"Выпало: {rolled}. Выплата x{multiplier}. Баланс: {new_balance}")

    def play_blackjack(self) -> None:
        amount = self.ask_bet(min_bet=10)
        if amount is None:
            return
        deck = create_deck()
        actions: List[str] = []
        # Loop until stand or bust handled inside logic
        while True:
            action = simpledialog.askstring("Блэкджек", "Ход (hit/stand)", parent=self)
            if action is None:
                return
            action = action.strip().lower()
            if action not in {"hit", "stand"}:
                messagebox.showwarning("Некорректный ввод", "Введите 'hit' или 'stand'.")
                continue
            actions.append(action)
            if action == "stand":
                break
        multiplier, player, dealer = play_round_decision(deck, actions)
        try:
            new_balance = self.balance.apply_bet_result(int(amount), multiplier)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка", str(e))
            return
        self.refresh_balance()
        messagebox.showinfo(
            "Результат",
            f"Ваши карты: {' '.join(player)} | Очки: {self._sum_cards(player)}\n"
            f"Карты дилера: {' '.join(dealer)} | Очки: {self._sum_cards(dealer)}\n"
            f"Выплата x{multiplier}. Баланс: {new_balance}",
        )

    def open_blackjack_window(self) -> None:
        BlackjackWindow(self)

    @staticmethod
    def _sum_cards(cards: List[str]) -> int:
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


class RouletteWindow(tk.Toplevel):
    W = 380
    H = 380
    PADDING = 10

    def __init__(self, app: CasinoApp) -> None:
        super().__init__(app)
        self.app = app
        self.title("Рулетка")
        self.resizable(False, False)

        container = tk.Frame(self)
        container.pack(padx=8, pady=8)

        self.canvas = tk.Canvas(container, width=self.W, height=self.H, bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, rowspan=6, padx=(0, 10))

        self.balance_var = tk.StringVar(value=f"Баланс: {self.app.balance.get_balance()}")
        tk.Label(container, textvariable=self.balance_var, font=("Segoe UI", 11, "bold")).grid(row=0, column=1, sticky="w")

        tk.Label(container, text="Тип ставки:").grid(row=1, column=1, sticky="w")
        self.bet_type_var = tk.StringVar(value="color")
        tk.OptionMenu(container, self.bet_type_var, "color", "number", "even_odd", "low_high", "dozen", "column").grid(row=1, column=1, sticky="e")

        tk.Label(container, text="Выбор (red/black, 0-36, even/odd, low/high, 1st/2nd/3rd, col1/col2/col3):").grid(row=2, column=1, sticky="w")
        self.selection_entry = tk.Entry(container, width=18)
        self.selection_entry.grid(row=2, column=1, sticky="e")

        tk.Label(container, text="Ставка:").grid(row=3, column=1, sticky="w")
        self.amount_entry = tk.Entry(container, width=18)
        self.amount_entry.insert(0, "10")
        self.amount_entry.grid(row=3, column=1, sticky="e")

        self.spin_button = tk.Button(container, text="Сделать ставку и запустить", command=self.on_spin_click)
        self.spin_button.grid(row=4, column=1, pady=4, sticky="we")

        tk.Label(container, text="История:").grid(row=5, column=1, sticky="w")
        self.history_list = tk.Listbox(container, height=8, width=28)
        self.history_list.grid(row=6, column=0, columnspan=2, sticky="we", pady=(6, 0))

        # Wheel state
        self.sector_deg = 360 / 37
        self.rotation_deg = 0.0
        self.animating = False
        self.target_rotation = 0.0
        self._highlight_job = None

        # Number order: 0..36 (упрощённо)
        self.numbers = list(range(37))
        self.draw_wheel()
        self.draw_pointer()

    def draw_wheel(self) -> None:
        self.canvas.delete("sector")
        cx = self.W / 2
        cy = self.H / 2
        radius = min(self.W, self.H) / 2 - self.PADDING
        for idx, num in enumerate(self.numbers):
            start_angle = (idx * self.sector_deg + self.rotation_deg) % 360
            extent = self.sector_deg
            color = self._sector_color(num)
            self.canvas.create_arc(
                cx - radius, cy - radius, cx + radius, cy + radius,
                start=start_angle, extent=extent, fill=color, outline="white", width=2, tags="sector"
            )
            # Number label (approximate position)
            mid_angle = math.radians(start_angle + extent / 2)
            tx = cx + (radius - 30) * math.cos(mid_angle)
            ty = cy - (radius - 30) * math.sin(mid_angle)
            self.canvas.create_text(
                tx, ty,
                text=str(num),
                tags="sector",
                fill="white" if color != "green" else "black",
                font=("Segoe UI", 8, "bold"),
            )

    def draw_pointer(self) -> None:
        self.canvas.delete("pointer")
        cx = self.W / 2
        top_y = 6
        self.canvas.create_polygon(
            cx - 10, top_y + 22,
            cx + 10, top_y + 22,
            cx, top_y,
            fill="black",
            tags="pointer",
        )

    def _sector_color(self, number: int) -> str:
        if number == 0:
            return "green"
        return "red" if number % 2 == 1 else "black"

    def on_spin_click(self) -> None:
        if self.animating:
            return
        # clear previous highlight if any
        self.canvas.delete("highlight")
        bet_type = self.bet_type_var.get().strip().lower()
        selection = self.selection_entry.get().strip().lower()
        try:
            amount = int(self.amount_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Ошибка", "Введите корректную сумму ставки")
            return
        if amount <= 0:
            messagebox.showwarning("Ошибка", "Ставка должна быть положительной")
            return
        if self.app.balance.get_balance() < amount:
            messagebox.showwarning("Недостаточно средств", "Недостаточно средств для этой ставки")
            return
        if bet_type not in {"color", "number"}:
            messagebox.showwarning("Ошибка", "Тип ставки: color или number")
            return
        if bet_type == "color" and selection not in {"red", "black"}:
            messagebox.showwarning("Ошибка", "Для color введите red или black")
            return
        if bet_type == "number":
            try:
                num_val = int(selection)
            except ValueError:
                messagebox.showwarning("Ошибка", "Для number введите число 0-36")
                return
            if not (0 <= num_val <= 36):
                messagebox.showwarning("Ошибка", "Число должно быть 0-36")
                return

        outcome_num, outcome_col = spin_wheel()
        target_idx = self.numbers.index(outcome_num)
        sector_center = target_idx * self.sector_deg + self.sector_deg / 2
        final_rotation = (-sector_center) % 360
        self.target_rotation = final_rotation + 360 * 6
        self.spin_button.config(state="disabled")
        self.animating = True

        def step_anim(current: float = 0.0) -> None:
            if current >= self.target_rotation:
                self.rotation_deg = self.target_rotation % 360
                self.draw_wheel()
                self.animating = False
                self.spin_button.config(state="normal")
                self._highlight_sector(target_idx)
                self._finalize_bet(bet_type, selection, amount, outcome_num, outcome_col)
                return
            remaining = self.target_rotation - current
            delta = max(5.0, remaining * 0.12)
            self.rotation_deg = (current + delta) % 360
            self.draw_wheel()
            self.after(20, lambda: step_anim(current + delta))

        step_anim()

    def _finalize_bet(self, bet_type: str, selection: str, amount: int, outcome_num: int, outcome_col: str) -> None:
        mult = roulette_resolve(bet_type, selection, outcome_num, outcome_col)
        try:
            new_balance = self.app.balance.apply_bet_result(int(amount), mult)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка", str(e))
            return
        self.app.refresh_balance()
        self.balance_var.set(f"Баланс: {new_balance}")
        self.history_list.insert(0, f"{outcome_num} ({outcome_col}) x{mult}")
        messagebox.showinfo("Результат", f"Выпало: {outcome_num} ({outcome_col}). Выплата x{mult}. Баланс: {new_balance}")

    def _highlight_sector(self, idx: int, blinks: int = 6) -> None:
        # Blink yellow outline around winning sector
        self.canvas.delete("highlight")
        cx = self.W / 2
        cy = self.H / 2
        outer = min(self.W, self.H) / 2 - self.PADDING
        inner = outer - 6
        start_angle = (idx * self.sector_deg + self.rotation_deg) % 360
        extent = self.sector_deg

        def draw_on() -> None:
            # outer border
            self.canvas.create_arc(
                cx - outer, cy - outer, cx + outer, cy + outer,
                start=start_angle, extent=extent,
                style=tk.ARC, outline="yellow", width=5, tags="highlight"
            )
            # inner border to emphasize wedge
            self.canvas.create_arc(
                cx - inner, cy - inner, cx + inner, cy + inner,
                start=start_angle, extent=extent,
                style=tk.ARC, outline="yellow", width=5, tags="highlight"
            )

        def toggle(i: int) -> None:
            if i <= 0:
                self.canvas.delete("highlight")
                return
            if i % 2 == 0:
                self.canvas.delete("highlight")
            else:
                draw_on()
            self._highlight_job = self.after(180, lambda: toggle(i - 1))

        toggle(blinks)


class BlackjackWindow(tk.Toplevel):
    CANVAS_W = 560
    CANVAS_H = 300

    def __init__(self, app: CasinoApp) -> None:
        super().__init__(app)
        self.app = app
        self.title("Блэкджек")
        self.resizable(False, False)

        self.deck = create_deck()
        self.player: List[str] = []
        self.dealer: List[str] = []
        self.round_active = False

        # Top: dealer and player canvases
        top = tk.Frame(self)
        top.pack(padx=8, pady=8)

        self.dealer_canvas = tk.Canvas(top, width=self.CANVAS_W, height=self.CANVAS_H/2, bg="#f5f5f5", highlightthickness=0)
        self.dealer_canvas.pack()
        self.player_canvas = tk.Canvas(top, width=self.CANVAS_W, height=self.CANVAS_H/2, bg="#ffffff", highlightthickness=0)
        self.player_canvas.pack(pady=(6, 0))

        # Right/bottom: controls
        ctrl = tk.Frame(self)
        ctrl.pack(fill="x", padx=8, pady=(0, 8))

        self.balance_var = tk.StringVar(value=f"Баланс: {self.app.balance.get_balance()}")
        tk.Label(ctrl, textvariable=self.balance_var, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")

        tk.Label(ctrl, text="Ставка:").grid(row=0, column=1, padx=(12, 4))
        self.bet_entry = tk.Entry(ctrl, width=8)
        self.bet_entry.insert(0, "10")
        self.bet_entry.grid(row=0, column=2)

        self.info_var = tk.StringVar(value="Нажмите Новая игра")
        tk.Label(ctrl, textvariable=self.info_var).grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 6))

        self.btn_new = tk.Button(ctrl, text="Новая игра", command=self.on_new_round)
        self.btn_hit = tk.Button(ctrl, text="Взять карту", command=self.on_hit, state="disabled")
        self.btn_stand = tk.Button(ctrl, text="Остановиться", command=self.on_stand, state="disabled")
        self.btn_new.grid(row=2, column=0, pady=4)
        self.btn_hit.grid(row=2, column=1, pady=4)
        self.btn_stand.grid(row=2, column=2, pady=4)

        self._redraw()

    def _redraw(self) -> None:
        # Clear
        self.dealer_canvas.delete("all")
        self.player_canvas.delete("all")
        # Titles with scores
        dealer_score = hand_value(self.dealer) if self.dealer else 0
        player_score = hand_value(self.player) if self.player else 0
        self.dealer_canvas.create_text(6, 6, anchor="nw", text=f"Дилер: {dealer_score}", font=("Segoe UI", 10, "bold"))
        self.player_canvas.create_text(6, 6, anchor="nw", text=f"Игрок: {player_score}", font=("Segoe UI", 10, "bold"))
        # Draw cards
        self._draw_cards(self.dealer_canvas, self.dealer)
        self._draw_cards(self.player_canvas, self.player)

    def _draw_cards(self, canvas: tk.Canvas, cards: List[str]) -> None:
        x = 10
        y = 28
        for card in cards:
            self._draw_card(canvas, x, y, card)
            x += 70

    def _draw_card(self, canvas: tk.Canvas, x: int, y: int, card: str) -> None:
        w, h = 60, 86
        canvas.create_rectangle(x, y, x + w, y + h, fill="white", outline="#333", width=2)
        rank = card[:-1]
        suit = card[-1]
        color = "#d32f2f" if suit in ("♥", "♦") else "#111"
        canvas.create_text(x + 8, y + 12, text=rank, fill=color, anchor="nw", font=("Segoe UI", 11, "bold"))
        canvas.create_text(x + w - 8, y + h - 12, text=suit, fill=color, anchor="se", font=("Segoe UI", 16))

    def on_new_round(self) -> None:
        # Validate bet
        try:
            amount = int(self.bet_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Ошибка", "Введите корректную сумму ставки")
            return
        if amount <= 0:
            messagebox.showwarning("Ошибка", "Ставка должна быть положительной")
            return
        if self.app.balance.get_balance() < amount:
            messagebox.showwarning("Недостаточно средств", "Недостаточно средств для ставки")
            return
        self.current_bet = amount
        # Reset and deal
        self.deck = create_deck()
        self.player = []
        self.dealer = []
        for _ in range(2):
            self.player.append(self.deck.pop())
            self.dealer.append(self.deck.pop())
        self.round_active = True
        self.info_var.set("Ход игрока")
        self.btn_hit.config(state="normal")
        self.btn_stand.config(state="normal")
        self._redraw()

    def on_hit(self) -> None:
        if not self.round_active:
            return
        self.player.append(self.deck.pop())
        if hand_value(self.player) > 21:
            self.round_active = False
            self._settle(multiplier=0.0, message="Перебор. Вы проиграли")
            return
        self._redraw()

    def on_stand(self) -> None:
        if not self.round_active:
            return
        # Dealer plays
        while hand_value(self.dealer) < 17:
            self.dealer.append(self.deck.pop())
        # Compare
        player_total = hand_value(self.player)
        dealer_total = hand_value(self.dealer)
        if dealer_total > 21 or player_total > dealer_total:
            self._settle(multiplier=2.0, message="Вы выиграли")
        elif player_total < dealer_total:
            self._settle(multiplier=0.0, message="Вы проиграли")
        else:
            self._settle(multiplier=1.0, message="Пуш")

    def _settle(self, multiplier: float, message: str) -> None:
        self.round_active = False
        try:
            new_balance = self.app.balance.apply_bet_result(self.current_bet, multiplier)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка", str(e))
            return
        self.app.refresh_balance()
        self.balance_var.set(f"Баланс: {new_balance}")
        self.info_var.set(message)
        self.btn_hit.config(state="disabled")
        self.btn_stand.config(state="disabled")
        self._redraw()


def main() -> None:
    app = CasinoApp()
    app.mainloop()


if __name__ == "__main__":
    main()


