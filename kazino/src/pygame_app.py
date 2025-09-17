from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

try:
    import pygame  # type: ignore
except Exception as e:  # noqa: BLE001
    raise RuntimeError("Pygame is required. Install with: pip install pygame") from e

try:
    from src.balance import BalanceManager
    from src.games.dice import roll_dice, resolve_guess
    from src.games.roulette import spin_wheel, resolve_bet as roulette_resolve
    from src.games.blackjack import create_deck, hand_value
    from src.games.slot_game_manager import SlotGameManager
    from src.games.slot_gui import SlotMachineGUI
except ModuleNotFoundError:
    from balance import BalanceManager  # type: ignore
    from games.dice import roll_dice, resolve_guess  # type: ignore
    from games.roulette import spin_wheel, resolve_bet as roulette_resolve  # type: ignore
    from games.blackjack import create_deck, hand_value  # type: ignore
    from games.slot_game_manager import SlotGameManager  # type: ignore
    from games.slot_gui import SlotMachineGUI  # type: ignore


WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (235, 238, 243)
PRIMARY = (33, 150, 243)
PRIMARY_DARK = (25, 118, 210)
RED = (211, 47, 47)
GREEN = (67, 160, 71)


def draw_text(surface: pygame.Surface, text: str, pos: Tuple[int, int], font: pygame.font.Font, color=BLACK) -> pygame.Rect:
    img = font.render(text, True, color)
    rect = img.get_rect(topleft=pos)
    surface.blit(img, rect)
    return rect


@dataclass
class Button:
    text: str
    rect: pygame.Rect
    on_click: Callable[[], None]
    enabled: bool = True

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        color = PRIMARY if self.enabled else (200, 200, 200)
        hover = self.rect.collidepoint(pygame.mouse.get_pos()) and self.enabled
        bg = PRIMARY_DARK if hover else color
        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        label = font.render(self.text, True, WHITE)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def handle(self, event: pygame.event.Event) -> None:
        if not self.enabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()


class TextInput:
    def __init__(self, rect: pygame.Rect, placeholder: str = "") -> None:
        self.rect = rect
        self.placeholder = placeholder
        self.text = ""
        self.focused = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=6)
        pygame.draw.rect(surface, (180, 190, 200), self.rect, width=2, border_radius=6)
        to_show = self.text if (self.text or self.focused) else self.placeholder
        color = BLACK if (self.text or self.focused) else (120, 130, 140)
        txt = font.render(to_show, True, color)
        surface.blit(txt, (self.rect.x + 8, self.rect.y + (self.rect.h - txt.get_height()) // 2))

    def handle(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
        if self.focused and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.focused = False
            else:
                if len(self.text) < 18:
                    ch = event.unicode
                    # Basic filter to visible ascii
                    if ch and 32 <= ord(ch) <= 126:
                        self.text += ch

    def get_int(self, default: int, min_value: Optional[int] = None, max_value: Optional[int] = None) -> Optional[int]:
        try:
            value = int(self.text)
        except ValueError:
            value = default
        if min_value is not None and value < min_value:
            return None
        if max_value is not None and value > max_value:
            return None
        return value


class OptionPicker:
    def __init__(self, rect: pygame.Rect, options: list[str], initial_index: int = 0) -> None:
        self.rect = rect
        self.options = options
        self.index = max(0, min(initial_index, len(options) - 1))

    def current(self) -> str:
        return self.options[self.index] if self.options else ""

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, label: str | None = None) -> None:
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=6)
        pygame.draw.rect(surface, (180, 190, 200), self.rect, width=2, border_radius=6)
        # arrows
        left = pygame.Rect(self.rect.x + 4, self.rect.y + 4, 28, self.rect.h - 8)
        right = pygame.Rect(self.rect.right - 32, self.rect.y + 4, 28, self.rect.h - 8)
        center = pygame.Rect(left.right + 4, self.rect.y + 4, self.rect.w - left.w - right.w - 8, self.rect.h - 8)
        pygame.draw.polygon(surface, (90, 100, 110), [(left.right - 6, left.centery), (left.x + 10, left.y + 6), (left.x + 10, left.bottom - 6)])
        pygame.draw.polygon(surface, (90, 100, 110), [(right.x + 6, right.centery), (right.right - 10, right.y + 6), (right.right - 10, right.bottom - 6)])
        text = self.current()
        if label:
            text = f"{label}: {text}"
        img = font.render(text, True, BLACK)
        surface.blit(img, img.get_rect(center=center.center))

    def handle(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.rect.collidepoint(mx, my):
                left = pygame.Rect(self.rect.x + 4, self.rect.y + 4, 28, self.rect.h - 8)
                right = pygame.Rect(self.rect.right - 32, self.rect.y + 4, 28, self.rect.h - 8)
                if left.collidepoint(mx, my):
                    if self.options:
                        self.index = (self.index - 1) % len(self.options)
                elif right.collidepoint(mx, my):
                    if self.options:
                        self.index = (self.index + 1) % len(self.options)


class NumberPicker:
    def __init__(self, rect: pygame.Rect, min_value: int, max_value: int, initial: int) -> None:
        self.rect = rect
        self.min_value = min_value
        self.max_value = max_value
        self.value = max(min_value, min(max_value, initial))

    def current(self) -> str:
        return str(self.value)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, label: str | None = None) -> None:
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=6)
        pygame.draw.rect(surface, (180, 190, 200), self.rect, width=2, border_radius=6)
        left = pygame.Rect(self.rect.x + 4, self.rect.y + 4, 28, self.rect.h - 8)
        right = pygame.Rect(self.rect.right - 32, self.rect.y + 4, 28, self.rect.h - 8)
        center = pygame.Rect(left.right + 4, self.rect.y + 4, self.rect.w - left.w - right.w - 8, self.rect.h - 8)
        pygame.draw.polygon(surface, (90, 100, 110), [(left.right - 6, left.centery), (left.x + 10, left.y + 6), (left.x + 10, left.bottom - 6)])
        pygame.draw.polygon(surface, (90, 100, 110), [(right.x + 6, right.centery), (right.right - 10, right.y + 6), (right.right - 10, right.bottom - 6)])
        text = self.current()
        if label:
            text = f"{label}: {text}"
        img = font.render(text, True, BLACK)
        surface.blit(img, img.get_rect(center=center.center))

    def handle(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.rect.collidepoint(mx, my):
                left = pygame.Rect(self.rect.x + 4, self.rect.y + 4, 28, self.rect.h - 8)
                right = pygame.Rect(self.rect.right - 32, self.rect.y + 4, 28, self.rect.h - 8)
                if left.collidepoint(mx, my):
                    self.value = self.min_value if self.value <= self.min_value else self.value - 1
                elif right.collidepoint(mx, my):
                    self.value = self.max_value if self.value >= self.max_value else self.value + 1

class Scene:
    def __init__(self, app: "PygameCasinoApp") -> None:
        self.app = app

    def draw(self, screen: pygame.Surface) -> None:
        raise NotImplementedError

    def handle(self, event: pygame.event.Event) -> None:
        raise NotImplementedError


class MenuScene(Scene):
    def __init__(self, app: "PygameCasinoApp") -> None:
        super().__init__(app)
        self.title_font = pygame.font.SysFont("segoeui", 36)
        self.ui_font = pygame.font.SysFont("segoeui", 22)
        w, h = app.size
        cx = w // 2
        buttons_w = 240
        y = 180
        self.buttons = [
            Button("Кости", pygame.Rect(cx - buttons_w // 2, y, buttons_w, 48), lambda: app.go("dice")),
            Button("Рулетка", pygame.Rect(cx - buttons_w // 2, y + 62, buttons_w, 48), lambda: app.go("roulette")),
            Button("Блэкджек", pygame.Rect(cx - buttons_w // 2, y + 124, buttons_w, 48), lambda: app.go("blackjack")),
            Button("Слот-машина", pygame.Rect(cx - buttons_w // 2, y + 186, buttons_w, 48), lambda: app.go("slot")),
        ]
        self.topup_button = Button("Пополнить +100", pygame.Rect(cx - buttons_w // 2, y + 248, buttons_w, 48), self._topup)

    def _topup(self) -> None:
        self.app.balance.deposit(100)
        

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(GRAY)
        draw_text(screen, "Казино", (40, 36), self.title_font)
        draw_text(screen, f"Баланс: {self.app.balance.get_balance()}", (40, 90), self.ui_font)
        for b in self.buttons:
            b.draw(screen, self.ui_font)
        # Top up is available in both windowed and fullscreen modes
        self.topup_button.enabled = True
        self.topup_button.draw(screen, self.ui_font)

    def handle(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle(event)
        self.topup_button.handle(event)


class DiceScene(Scene):
    def __init__(self, app: "PygameCasinoApp") -> None:
        super().__init__(app)
        self.title_font = pygame.font.SysFont("segoeui", 28)
        self.ui_font = pygame.font.SysFont("segoeui", 20)
        w, _ = app.size
        self.bet_input = TextInput(pygame.Rect(40, 80, 120, 36), "Ставка")
        self.guess_input = TextInput(pygame.Rect(180, 80, 120, 36), "Число 1-6")
        self.msg: str = ""
        self.roll_button = Button("Бросить", pygame.Rect(320, 80, 120, 36), self._on_roll)
        self.back_button = Button("Назад", pygame.Rect(w - 140, 20, 120, 36), lambda: app.go("menu"))
        self.animating = False
        self.anim_ticks = 0
        self.final_face: Optional[int] = None

    def _draw_die(self, surface: pygame.Surface, center: Tuple[int, int], size: int, face: int) -> None:
        x = center[0] - size // 2
        y = center[1] - size // 2
        pygame.draw.rect(surface, WHITE, (x, y, size, size), border_radius=10)
        pygame.draw.rect(surface, BLACK, (x, y, size, size), width=3, border_radius=10)
        r = max(6, size // 12)
        positions = [
            (x + size * 0.25, y + size * 0.25),
            (x + size * 0.5, y + size * 0.5),
            (x + size * 0.75, y + size * 0.75),
            (x + size * 0.25, y + size * 0.75),
            (x + size * 0.75, y + size * 0.25),
            (x + size * 0.25, y + size * 0.5),
            (x + size * 0.75, y + size * 0.5),
        ]
        mapping = {
            1: [1],
            2: [0, 2],
            3: [0, 1, 2],
            4: [0, 2, 3, 4],
            5: [0, 1, 2, 3, 4],
            6: [0, 3, 5, 2, 6, 4],
        }
        for idx in mapping.get(max(1, min(6, face)), []):
            px, py = positions[idx]
            pygame.draw.circle(surface, BLACK, (int(px), int(py)), r)

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(GRAY)
        draw_text(screen, "Кости", (40, 24), self.title_font)
        draw_text(screen, f"Баланс: {self.app.balance.get_balance()}", (40, 50), self.ui_font)
        self.bet_input.draw(screen, self.ui_font)
        self.guess_input.draw(screen, self.ui_font)
        self.roll_button.draw(screen, self.ui_font)
        self.back_button.draw(screen, self.ui_font)
        face = self.final_face if self.final_face is not None else ((pygame.time.get_ticks() // 120) % 6) + 1
        self._draw_die(screen, (160, 230), 120, face)
        if self.msg:
            draw_text(screen, self.msg, (40, 320), self.ui_font, color=(50, 60, 70))

    def handle(self, event: pygame.event.Event) -> None:
        self.bet_input.handle(event)
        self.guess_input.handle(event)
        self.roll_button.handle(event)
        self.back_button.handle(event)

    def _on_roll(self) -> None:
        if self.animating:
            return
        bet = self.bet_input.get_int(default=0, min_value=1)
        guess = self.guess_input.get_int(default=0, min_value=1, max_value=6)
        if bet is None or guess is None:
            self.msg = "Введите корректную ставку и число 1-6"
            return
        if self.app.balance.get_balance() < bet:
            self.msg = "Недостаточно средств"
            return
        self.animating = True
        self.anim_ticks = 18
        self.final_face = None

        def finish() -> None:
            outcome = roll_dice()
            self.final_face = outcome
            mult = resolve_guess(guess, outcome)
            try:
                new_balance = self.app.balance.apply_bet_result(bet, mult)
            except Exception as e:  # noqa: BLE001
                self.msg = f"Ошибка: {e}"
                self.animating = False
                return
            self.msg = f"Выпало: {outcome}. Выплата x{mult}. Баланс: {new_balance}"
            self.animating = False

        # Tie to a timer using pygame events
        pygame.time.set_timer(pygame.USEREVENT + 1, 50, loops=self.anim_ticks)

        def on_tick(_: int) -> None:
            if not self.animating:
                return
            self.anim_ticks -= 1
            if self.anim_ticks <= 0:
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                finish()

        self.app.register_timer_handler(pygame.USEREVENT + 1, on_tick)


class RouletteScene(Scene):
    def __init__(self, app: "PygameCasinoApp") -> None:
        super().__init__(app)
        self.title_font = pygame.font.SysFont("segoeui", 28)
        self.ui_font = pygame.font.SysFont("segoeui", 20)
        w, _ = app.size
        self.bet_input = TextInput(pygame.Rect(40, 80, 120, 36), "Ставка")
        # pickers for type and selection
        self.type_picker = OptionPicker(pygame.Rect(180, 80, 200, 36), ["color", "number", "even_odd", "low_high", "dozen", "column"]) 
        self._current_type = self.type_picker.current()
        # selection picker (updated on type change)
        self.sel_picker: OptionPicker | NumberPicker = OptionPicker(pygame.Rect(400, 80, 220, 36), ["red", "black"]) 
        self._update_selection_widget()
        self.spin_button = Button("Крутить", pygame.Rect(620, 80, 120, 36), self._on_spin)
        self.back_button = Button("Назад", pygame.Rect(w - 100, 20, 120, 36), lambda: app.go("menu"))
        self.msg: str = ""
        self.animating = False
        self.rotation = 0.0
        self.target_rotation = 0.0
        self._pending_outcome = None
        self.numbers = [
            0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8,
            23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12,
            35, 3, 26,
        ]

    def _sector_color(self, number: int) -> Tuple[int, int, int]:
        if number == 0:
            return (0, 150, 0)
        red_numbers = {
            1, 3, 5, 7, 9,
            12, 14, 16, 18,
            19, 21, 23, 25, 27,
            30, 32, 34, 36,
        }
        return RED if number in red_numbers else BLACK

    def _draw_wheel(self, surface: pygame.Surface, center: Tuple[int, int], radius: int) -> None:
        cx, cy = center
        pygame.draw.circle(surface, WHITE, (cx, cy), radius)
        sector_deg = 360 / len(self.numbers)
        for idx, num in enumerate(self.numbers):
            start_angle = math.radians(idx * sector_deg + self.rotation)
            end_angle = math.radians((idx + 1) * sector_deg + self.rotation)
            color = self._sector_color(num)
            # wedge
            points = [(cx, cy)]
            steps = 4
            for s in range(steps + 1):
                t = start_angle + (end_angle - start_angle) * (s / steps)
                points.append((cx + int(radius * math.cos(t)), cy + int(radius * math.sin(t))))
            pygame.draw.polygon(surface, color, points)
            # number label
            mid = (start_angle + end_angle) / 2
            tx = cx + int((radius - 24) * math.cos(mid))
            ty = cy + int((radius - 24) * math.sin(mid))
            label = self.ui_font.render(str(num), True, WHITE if color != (0, 150, 0) else BLACK)
            rect = label.get_rect(center=(tx, ty))
            surface.blit(label, rect)

        pygame.draw.circle(surface, BLACK, (cx, cy), radius, width=4)
        # pointer at top
        pygame.draw.polygon(surface, BLACK, [(cx, cy - radius - 8), (cx - 10, cy - radius + 10), (cx + 10, cy - radius + 10)])

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(GRAY)
        draw_text(screen, "Рулетка", (40, 24), self.title_font)
        draw_text(screen, f"Баланс: {self.app.balance.get_balance()}", (40, 50), self.ui_font)
        self.bet_input.draw(screen, self.ui_font)
        self.type_picker.draw(screen, self.ui_font, label="Тип")
        self.sel_picker.draw(screen, self.ui_font, label="Выбор")
        self.spin_button.draw(screen, self.ui_font)
        self.back_button.draw(screen, self.ui_font)
        rect = screen.get_rect()
        center = (rect.centerx, rect.centery + 40)
        radius = max(120, min(180, rect.h // 2 - 40, rect.w // 2 - 40))
        self._draw_wheel(screen, center, radius)
        if self.msg:
            draw_text(screen, self.msg, (40, screen.get_height() - 40), self.ui_font, color=(50, 60, 70))

    def handle(self, event: pygame.event.Event) -> None:
        self.bet_input.handle(event)
        prev_type = self.type_picker.current()
        self.type_picker.handle(event)
        if self.type_picker.current() != prev_type:
            self._current_type = self.type_picker.current()
            self._update_selection_widget()
        self.sel_picker.handle(event)
        self.spin_button.handle(event)
        self.back_button.handle(event)
        
        # Handle roulette wheel animation
        if event.type == pygame.USEREVENT + 2 and self.animating:
            self._update_rotation()

    def _update_rotation(self) -> None:
        """Update wheel rotation during animation"""
        if not self.animating:
            return
            
        # Calculate remaining rotation
        current = self.rotation % 360
        target = self.target_rotation % 360
        
        # Handle wrap-around case
        if target < current:
            remaining = (360 - current) + target
        else:
            remaining = target - current
            
        # Stop if close enough to target
        if remaining < 1.0:
            pygame.time.set_timer(pygame.USEREVENT + 2, 0)
            self.rotation = self.target_rotation % 360
            self.animating = False
            self._finalize_result()
            return
            
        # Decelerate as we approach target
        delta = max(1.0, remaining * 0.15)
        self.rotation = (self.rotation + delta) % 360

    def _finalize_result(self) -> None:
        """Finalize the roulette result after animation completes"""
        if self._pending_outcome is None:
            return
            
        outcome_num, outcome_col, bet_type, selection, bet = self._pending_outcome
        self._pending_outcome = None
        
        # Determine color for the outcome
        if outcome_num == 0:
            color = "green"
        else:
            red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
            color = "red" if outcome_num in red_numbers else "black"
        
        mult = roulette_resolve(bet_type, selection, outcome_num, color)
        try:
            new_balance = self.app.balance.apply_bet_result(bet, mult)
        except Exception as e:  # noqa: BLE001
            self.msg = f"Ошибка: {e}"
            return
            
        self.msg = f"Выпало: {outcome_num} ({color}). Выплата x{mult}. Баланс: {new_balance}"

    def _on_spin(self) -> None:
        if self.animating:
            return
        bet = self.bet_input.get_int(default=0, min_value=1)
        bet_type = self.type_picker.current()
        selection = self.sel_picker.current()
        valid_types = {"color", "number", "even_odd", "low_high", "dozen", "column"}
        if bet is None or bet_type not in valid_types:
            self.msg = "Неверная ставка/тип"
            return
        if self.app.balance.get_balance() < bet:
            self.msg = "Недостаточно средств"
            return

        outcome_num, outcome_col = spin_wheel()
        
        # Store the outcome for finalization
        self._pending_outcome = (outcome_num, outcome_col, bet_type, selection, bet)
        
        # Compute target rotation to align result at top (90 degrees reference)
        sector_deg = 360 / len(self.numbers)
        idx = self.numbers.index(outcome_num)
        sector_center = idx * sector_deg + sector_deg / 2
        # Align sector center to the top pointer (-90°). 270° == -90° mod 360
        final_rotation = (270 - sector_center) % 360
        self.target_rotation = final_rotation + 360 * 6  # Add multiple rotations for effect
        self.animating = True
        
        # Start animation timer
        pygame.time.set_timer(pygame.USEREVENT + 2, 20)

    def _update_selection_widget(self) -> None:
        # keep current selection when possible; otherwise reset
        rect = pygame.Rect(400, 80, 220, 36)
        t = self._current_type
        if t == "color":
            self.sel_picker = OptionPicker(rect, ["red", "black"]) 
        elif t == "number":
            # default to 0
            self.sel_picker = NumberPicker(rect, 0, 36, 0)
        elif t == "even_odd":
            self.sel_picker = OptionPicker(rect, ["even", "odd"]) 
        elif t == "low_high":
            self.sel_picker = OptionPicker(rect, ["low", "high"]) 
        elif t == "dozen":
            self.sel_picker = OptionPicker(rect, ["1st", "2nd", "3rd"]) 
        elif t == "column":
            self.sel_picker = OptionPicker(rect, ["col1", "col2", "col3"]) 


class BlackjackScene(Scene):
    def __init__(self, app: "PygameCasinoApp") -> None:
        super().__init__(app)
        self.title_font = pygame.font.SysFont("segoeui", 28)
        self.ui_font = pygame.font.SysFont("segoeui", 20)
        w, _ = app.size
        self.bet_input = TextInput(pygame.Rect(40, 80, 120, 36), "Ставка (>=10)")
        self.new_button = Button("Новая игра", pygame.Rect(180, 80, 140, 36), self._on_new)
        self.hit_button = Button("Взять", pygame.Rect(330, 80, 100, 36), self._on_hit)
        self.stand_button = Button("Стоп", pygame.Rect(440, 80, 100, 36), self._on_stand)
        self.back_button = Button("Назад", pygame.Rect(w - 140, 20, 120, 36), lambda: app.go("menu"))
        self.deck = []
        self.player: list[str] = []
        self.dealer: list[str] = []
        self.round_active = False
        self.current_bet = 0
        self.msg: str = "Нажмите Новая игра"

    def _draw_hand(self, surface: pygame.Surface, cards: list[str], origin: tuple[int, int]) -> None:
        x, y = origin
        for card in cards:
            self._draw_card(surface, (x, y), card)
            x += 70

    def _draw_card(self, surface: pygame.Surface, pos: tuple[int, int], card: str) -> None:
        x, y = pos
        w, h = 60, 86
        pygame.draw.rect(surface, WHITE, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, (40, 40, 40), (x, y, w, h), width=2, border_radius=6)
        rank = card[:-1]
        suit = card[-1]
        color = RED if suit in ("♥", "♦") else BLACK
        font_r = pygame.font.SysFont("segoeui", 18, bold=True)
        font_s = pygame.font.SysFont("segoeui", 20)
        surface.blit(font_r.render(rank, True, color), (x + 6, y + 6))
        surface.blit(font_s.render(suit, True, color), (x + w - 18, y + h - 26))

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(GRAY)
        draw_text(screen, "Блэкджек", (40, 24), self.title_font)
        draw_text(screen, f"Баланс: {self.app.balance.get_balance()}", (40, 50), self.ui_font)
        self.bet_input.draw(screen, self.ui_font)
        self.new_button.draw(screen, self.ui_font)
        self.hit_button.draw(screen, self.ui_font)
        self.stand_button.draw(screen, self.ui_font)
        self.back_button.draw(screen, self.ui_font)

        # dealer
        draw_text(screen, f"Дилер: {hand_value(self.dealer) if self.dealer else 0}", (40, 140), self.ui_font)
        self._draw_hand(screen, self.dealer, (40, 166))
        # player
        draw_text(screen, f"Игрок: {hand_value(self.player) if self.player else 0}", (40, 264), self.ui_font)
        self._draw_hand(screen, self.player, (40, 290))

        if self.msg:
            draw_text(screen, self.msg, (40, 360), self.ui_font, color=(50, 60, 70))

    def handle(self, event: pygame.event.Event) -> None:
        self.bet_input.handle(event)
        self.new_button.handle(event)
        self.hit_button.handle(event)
        self.stand_button.handle(event)
        self.back_button.handle(event)

    def _on_new(self) -> None:
        bet = self.bet_input.get_int(default=0, min_value=10)
        if bet is None:
            self.msg = "Ставка не менее 10"
            return
        if self.app.balance.get_balance() < bet:
            self.msg = "Недостаточно средств"
            return
        self.current_bet = bet
        self.deck = create_deck()
        random.shuffle(self.deck)
        self.player = [self.deck.pop(), self.deck.pop()]
        self.dealer = [self.deck.pop(), self.deck.pop()]
        self.round_active = True
        self.msg = "Ваш ход"

    def _on_hit(self) -> None:
        if not self.round_active:
            return
        self.player.append(self.deck.pop())
        if hand_value(self.player) > 21:
            self.round_active = False
            self._settle(0.0, "Перебор. Вы проиграли")
        else:
            self.msg = "Ваш ход"

    def _on_stand(self) -> None:
        if not self.round_active:
            return
        while hand_value(self.dealer) < 17 and self.deck:
            self.dealer.append(self.deck.pop())
        p = hand_value(self.player)
        d = hand_value(self.dealer)
        if d > 21 or p > d:
            self._settle(2.0, "Вы выиграли")
        elif p < d:
            self._settle(0.0, "Вы проиграли")
        else:
            self._settle(1.0, "Пуш")

    def _settle(self, mult: float, message: str) -> None:
        self.round_active = False
        try:
            new_balance = self.app.balance.apply_bet_result(self.current_bet, mult)
        except Exception as e:  # noqa: BLE001
            self.msg = f"Ошибка: {e}"
            return
        self.msg = f"{message}. Баланс: {new_balance}"

class PygameCasinoApp:
    def __init__(self, size: Tuple[int, int] = (720, 400)) -> None:
        pygame.init()
        pygame.display.set_caption("Казино - Pygame")
        self.windowed_size = size
        self.fullscreen = False
        self.screen = pygame.display.set_mode(self.windowed_size)
        self.size = self.windowed_size
        self.clock = pygame.time.Clock()
        self.balance = BalanceManager()
        self._timer_handlers: dict[int, Callable[[int], None]] = {}
        self.scenes = {
            "menu": MenuScene(self),
            "dice": DiceScene(self),
            "roulette": RouletteScene(self),
            "blackjack": BlackjackScene(self),
            "slot": SlotScene(self),
        }
        self.current: Scene = self.scenes["menu"]

    def register_timer_handler(self, event_type: int, handler: Callable[[int], None]) -> None:
        self._timer_handlers[event_type] = handler

    def go(self, scene_name: str) -> None:
        self.current = self.scenes.get(scene_name, self.current)

    def run(self) -> None:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                if event.type in self._timer_handlers:
                    self._timer_handlers[event.type](event.type)
                self.current.handle(event)

            # Обновляем состояние сцены (для анимаций)
            if hasattr(self.current, 'update'):
                self.current.update()
                
            self.current.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

    def toggle_fullscreen(self) -> None:
        if not self.fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
            self.size = (info.current_w, info.current_h)
            self.fullscreen = True
        else:
            self.screen = pygame.display.set_mode(self.windowed_size)
            self.size = self.windowed_size
            self.fullscreen = False


class SlotScene(Scene):
    def __init__(self, app: "PygameCasinoApp") -> None:
        super().__init__(app)
        self.slot_game_manager = SlotGameManager(app.balance)
        self.slot_gui = SlotMachineGUI(self.slot_game_manager, app.size[0], app.size[1])
        
    def draw(self, screen: pygame.Surface) -> None:
        self.slot_gui.draw(screen)
        
    def handle(self, event: pygame.event.Event) -> None:
        result = self.slot_gui.handle_event(event)
        if result == 'back_to_menu':
            self.app.go("menu")
        elif result == 'show_stats':
            # Здесь можно добавить показ детальной статистики
            pass
            
    def update(self) -> None:
        self.slot_gui.update()


def main() -> None:
    app = PygameCasinoApp()
    app.run()


if __name__ == "__main__":
    main()


