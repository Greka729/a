"""
Графический интерфейс для слот-машины
Интегрируется с pygame приложением
"""

import pygame
import time
from typing import List, Dict, Tuple, Optional
try:
    from .slot_machine import Symbol
    from .slot_game_manager import SlotGameManager
    from .slot_win_checker import WinType
    from .slot_sounds import SlotSoundManager
except ImportError:
    from slot_machine import Symbol
    from slot_game_manager import SlotGameManager
    from slot_win_checker import WinType
    from slot_sounds import SlotSoundManager


class SlotReel:
    """Класс для анимации барабана"""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.symbols = []
        self.current_symbol = Symbol.CHERRY
        self.is_spinning = False
        self.spin_speed = 0.1
        self.last_spin_time = 0
        self.target_symbol = Symbol.CHERRY
        
    def start_spin(self, target_symbol: Symbol):
        """Начать вращение барабана"""
        self.is_spinning = True
        self.target_symbol = target_symbol
        self.last_spin_time = time.time()
    
    def stop_spin(self):
        """Остановить вращение барабана"""
        self.is_spinning = False
        self.current_symbol = self.target_symbol
    
    def update(self):
        """Обновить анимацию барабана"""
        if self.is_spinning:
            current_time = time.time()
            if current_time - self.last_spin_time >= self.spin_speed:
                # Переключаем на случайный символ для эффекта вращения
                self.current_symbol = list(Symbol)[int(time.time() * 10) % len(Symbol)]
                self.last_spin_time = current_time
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font, icons: Dict[Symbol, pygame.Surface]):
        """Нарисовать барабан"""
        # Рамка барабана
        pygame.draw.rect(surface, (50, 50, 50), (self.x, self.y, self.width, self.height), 3)
        pygame.draw.rect(surface, (200, 200, 200), (self.x + 3, self.y + 3, self.width - 6, self.height - 6))
        
        # Символ (иконка или эмодзи)
        icon = icons.get(self.current_symbol)
        if icon is not None:
            icon_rect = icon.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
            surface.blit(icon, icon_rect)
        else:
            symbol_text = self.current_symbol.value
            text_surface = font.render(symbol_text, True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
            surface.blit(text_surface, text_rect)


class SlotMachineGUI:
    """Графический интерфейс слот-машины"""
    
    def __init__(self, game_manager: SlotGameManager, screen_width: int = 800, screen_height: int = 600):
        self.game_manager = game_manager
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Цвета
        self.colors = {
            'background': (34, 139, 34),  # Зеленый фон казино
            'machine': (139, 69, 19),     # Коричневый корпус
            'screen': (0, 0, 0),          # Черный экран
            'button': (255, 215, 0),      # Золотая кнопка
            'button_hover': (255, 255, 0), # Желтая кнопка при наведении
            'text': (255, 255, 255),      # Белый текст
            'win': (255, 215, 0),         # Золотой цвет выигрыша
            'lose': (255, 0, 0)           # Красный цвет проигрыша
        }
        
        # Шрифты
        pygame.font.init()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Барабаны
        reel_width = 120
        reel_height = 120
        reel_spacing = 20
        start_x = (screen_width - (3 * reel_width + 2 * reel_spacing)) // 2
        start_y = 150
        
        self.reels = []
        for i in range(3):
            x = start_x + i * (reel_width + reel_spacing)
            self.reels.append(SlotReel(x, start_y, reel_width, reel_height))

        # Иконки символов
        self.symbol_icons: Dict[Symbol, pygame.Surface] = {}
        self._load_icons(icon_box_size=(reel_width - 24, reel_height - 24))
        
        # Кнопки
        self.buttons = {}
        self._create_buttons()
        
        # Состояние анимации
        self.is_spinning = False
        self.spin_start_time = 0
        self.spin_duration = 2.0
        self.last_result = []
        self.last_wins = []
        self.win_animation_time = 0
        self.show_win_message = False
        
        # Звуки
        self.sound_manager = SlotSoundManager()
    
    def _create_buttons(self):
        """Создать кнопки интерфейса"""
        button_width = 120
        button_height = 40
        button_spacing = 10
        
        # Кнопка SPIN
        spin_x = (self.screen_width - button_width) // 2
        spin_y = 350
        self.buttons['spin'] = pygame.Rect(spin_x, spin_y, button_width, button_height)
        
        # Кнопки ставок
        bet_buttons_y = 400
        bet_amounts = [5, 10, 25, 50, 100]
        total_bet_width = len(bet_amounts) * button_width + (len(bet_amounts) - 1) * button_spacing
        bet_start_x = (self.screen_width - total_bet_width) // 2
        
        for i, amount in enumerate(bet_amounts):
            x = bet_start_x + i * (button_width + button_spacing)
            self.buttons[f'bet_{amount}'] = pygame.Rect(x, bet_buttons_y, button_width, button_height)
        
        # Кнопка статистики
        self.buttons['stats'] = pygame.Rect(20, 20, 100, 30)
        
        # Кнопка возврата в меню
        self.buttons['back'] = pygame.Rect(self.screen_width - 120, 20, 100, 30)

    def _load_icons(self, icon_box_size: Tuple[int, int]) -> None:
        """Создать иконки символов программно"""
        for symbol in Symbol:
            icon = self._create_symbol_icon(symbol, icon_box_size)
            self.symbol_icons[symbol] = icon
    
    def _create_symbol_icon(self, symbol: Symbol, size: Tuple[int, int]) -> pygame.Surface:
        """Создать иконку символа программно"""
        width, height = size
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Цвета для разных символов
        colors = {
            Symbol.CHERRY: (255, 0, 0),      # Красный
            Symbol.LEMON: (255, 255, 0),     # Желтый
            Symbol.ORANGE: (255, 165, 0),    # Оранжевый
            Symbol.PLUM: (128, 0, 128),      # Фиолетовый
            Symbol.BELL: (255, 215, 0),      # Золотой
            Symbol.BAR: (0, 0, 255),         # Синий
            Symbol.SEVEN: (255, 255, 255),   # Белый
            Symbol.DIAMOND: (0, 255, 255),   # Голубой
        }
        
        color = colors.get(symbol, (128, 128, 128))
        
        if symbol == Symbol.CHERRY:
            self._draw_cherry(surface, width, height, color)
        elif symbol == Symbol.LEMON:
            self._draw_lemon(surface, width, height, color)
        elif symbol == Symbol.ORANGE:
            self._draw_orange(surface, width, height, color)
        elif symbol == Symbol.PLUM:
            self._draw_plum(surface, width, height, color)
        elif symbol == Symbol.BELL:
            self._draw_bell(surface, width, height, color)
        elif symbol == Symbol.BAR:
            self._draw_bar(surface, width, height, color)
        elif symbol == Symbol.SEVEN:
            self._draw_seven(surface, width, height, color)
        elif symbol == Symbol.DIAMOND:
            self._draw_diamond(surface, width, height, color)
        
        return surface
    
    def _draw_cherry(self, surface: pygame.Surface, width: int, height: int, color: Tuple[int, int, int]):
        """Нарисовать вишню"""
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 3
        
        # Две вишни
        pygame.draw.circle(surface, color, (center_x - radius//2, center_y), radius)
        pygame.draw.circle(surface, color, (center_x + radius//2, center_y), radius)
        
        # Стебель
        pygame.draw.line(surface, (0, 100, 0), (center_x, center_y - radius), (center_x, center_y - radius*2), 3)
    
    def _draw_lemon(self, surface: pygame.Surface, width: int, height: int, color: Tuple[int, int, int]):
        """Нарисовать лимон"""
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 3
        
        # Овал (лимон)
        pygame.draw.ellipse(surface, color, (center_x - radius, center_y - radius//2, radius*2, radius))
        
        # Текстура лимона
        for i in range(3):
            y = center_y - radius//2 + i * radius//3
            pygame.draw.line(surface, (200, 200, 0), (center_x - radius//2, y), (center_x + radius//2, y), 2)
    
    def _draw_orange(self, surface: pygame.Surface, width: int, height: int, color: Tuple[int, int, int]):
        """Нарисовать апельсин"""
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 3
        
        # Круг (апельсин)
        pygame.draw.circle(surface, color, (center_x, center_y), radius)
        
        # Текстура апельсина
        for i in range(4):
            angle = i * 45
            start_x = center_x + int(radius * 0.7 * pygame.math.Vector2(1, 0).rotate(angle).x)
            start_y = center_y + int(radius * 0.7 * pygame.math.Vector2(1, 0).rotate(angle).y)
            end_x = center_x + int(radius * 0.9 * pygame.math.Vector2(1, 0).rotate(angle).x)
            end_y = center_y + int(radius * 0.9 * pygame.math.Vector2(1, 0).rotate(angle).y)
            pygame.draw.line(surface, (255, 200, 0), (start_x, start_y), (end_x, end_y), 2)
    
    def _draw_plum(self, surface: pygame.Surface, width: int, height: int, color: Tuple[int, int, int]):
        """Нарисовать сливу"""
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 3
        
        # Овал (слива)
        pygame.draw.ellipse(surface, color, (center_x - radius, center_y - radius//2, radius*2, radius))
        
        # Стебель
        pygame.draw.line(surface, (0, 100, 0), (center_x, center_y - radius//2), (center_x, center_y - radius), 3)
    
    def _draw_bell(self, surface: pygame.Surface, width: int, height: int, color: Tuple[int, int, int]):
        """Нарисовать колокольчик"""
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 3
        
        # Колокольчик (треугольник с закругленным низом)
        points = [
            (center_x, center_y - radius),
            (center_x - radius, center_y + radius//2),
            (center_x + radius, center_y + radius//2)
        ]
        pygame.draw.polygon(surface, color, points)
        
        # Звонок внутри
        pygame.draw.circle(surface, (200, 200, 0), (center_x, center_y), radius//3)
        
        # Ручка
        pygame.draw.line(surface, (139, 69, 19), (center_x, center_y - radius), (center_x, center_y - radius*1.5), 4)
    
    def _draw_bar(self, surface: pygame.Surface, width: int, height: int, color: Tuple[int, int, int]):
        """Нарисовать бар"""
        center_x, center_y = width // 2, height // 2
        bar_width = width // 2
        bar_height = height // 3
        
        # Прямоугольник
        rect = pygame.Rect(center_x - bar_width//2, center_y - bar_height//2, bar_width, bar_height)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, (0, 0, 0), rect, 3)
        
        # Текст "BAR"
        font = pygame.font.Font(None, min(width, height) // 4)
        text = font.render("BAR", True, (255, 255, 255))
        text_rect = text.get_rect(center=(center_x, center_y))
        surface.blit(text, text_rect)
    
    def _draw_seven(self, surface: pygame.Surface, width: int, height: int, color: Tuple[int, int, int]):
        """Нарисовать семерку"""
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 3
        
        # Большая семерка
        font = pygame.font.Font(None, min(width, height) // 2)
        text = font.render("7", True, color)
        text_rect = text.get_rect(center=(center_x, center_y))
        surface.blit(text, text_rect)
        
        # Звездочки вокруг
        star_size = min(width, height) // 8
        for i in range(4):
            angle = i * 90
            star_x = center_x + int(radius * 0.8 * pygame.math.Vector2(1, 0).rotate(angle).x)
            star_y = center_y + int(radius * 0.8 * pygame.math.Vector2(1, 0).rotate(angle).y)
            pygame.draw.circle(surface, (255, 255, 0), (star_x, star_y), star_size)
    
    def _draw_diamond(self, surface: pygame.Surface, width: int, height: int, color: Tuple[int, int, int]):
        """Нарисовать алмаз"""
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 3
        
        # Алмаз (ромб)
        points = [
            (center_x, center_y - radius),
            (center_x + radius, center_y),
            (center_x, center_y + radius),
            (center_x - radius, center_y)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (0, 0, 0), points, 2)
        
        # Блеск
        pygame.draw.circle(surface, (255, 255, 255), (center_x - radius//3, center_y - radius//3), radius//6)
    
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Обработать событие"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                return self._handle_click(event.pos)
        
        return None
    
    def _handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Обработать клик мыши"""
        # Проверяем кнопки
        for button_name, rect in self.buttons.items():
            if rect.collidepoint(pos):
                if button_name == 'spin':
                    if not self.is_spinning and self.game_manager.can_spin():
                        self._start_spin()
                elif button_name.startswith('bet_'):
                    amount = int(button_name.split('_')[1])
                    if self.game_manager.set_bet(amount):
                        self.sound_manager.play_click_sound()
                elif button_name == 'stats':
                    return 'show_stats'
                elif button_name == 'back':
                    return 'back_to_menu'
        
        return None
    
    def _start_spin(self):
        """Начать вращение барабанов"""
        if self.is_spinning:
            return
        
        self.is_spinning = True
        self.spin_start_time = time.time()
        self.show_win_message = False
        
        # Запускаем анимацию барабанов
        for reel in self.reels:
            reel.start_spin(Symbol.CHERRY)  # Временно, будет заменено на реальный результат
        
        self.sound_manager.play_spin_sound()
    
    def _stop_spin(self):
        """Остановить вращение барабанов"""
        if not self.is_spinning:
            return
        
        self.is_spinning = False
        
        # Получаем результат от игрового менеджера
        result, wins, total_payout = self.game_manager.spin()
        self.last_result = result
        self.last_wins = wins
        
        # Устанавливаем финальные символы на барабаны
        for i, symbol in enumerate(result):
            if i < len(self.reels):
                self.reels[i].stop_spin()
                self.reels[i].current_symbol = symbol
        
        # Показываем сообщение о выигрыше/проигрыше
        if total_payout > 0:
            self.show_win_message = True
            self.win_animation_time = time.time()
            self.sound_manager.play_win_sound()
        else:
            self.sound_manager.play_lose_sound()
    
    def update(self):
        """Обновить состояние интерфейса"""
        current_time = time.time()
        
        # Обновляем анимацию барабанов
        for reel in self.reels:
            reel.update()
        
        # Проверяем, нужно ли остановить вращение
        if self.is_spinning and current_time - self.spin_start_time >= self.spin_duration:
            self._stop_spin()
        
        # Скрываем сообщение о выигрыше через 3 секунды
        if self.show_win_message and current_time - self.win_animation_time >= 3.0:
            self.show_win_message = False
    
    def draw(self, surface: pygame.Surface):
        """Нарисовать интерфейс"""
        # Фон
        surface.fill(self.colors['background'])
        
        # Корпус слот-машины
        machine_rect = pygame.Rect(50, 50, self.screen_width - 100, self.screen_height - 100)
        pygame.draw.rect(surface, self.colors['machine'], machine_rect)
        pygame.draw.rect(surface, (0, 0, 0), machine_rect, 5)
        
        # Экран слот-машины
        screen_rect = pygame.Rect(100, 100, self.screen_width - 200, 200)
        pygame.draw.rect(surface, self.colors['screen'], screen_rect)
        pygame.draw.rect(surface, (255, 255, 255), screen_rect, 3)
        
        # Барабаны
        for reel in self.reels:
            reel.draw(surface, self.font_large, self.symbol_icons)
        
        # Кнопки
        self._draw_buttons(surface)
        
        # Информация о балансе и ставке
        self._draw_info(surface)
        
        # Сообщение о выигрыше/проигрыше
        if self.show_win_message:
            self._draw_win_message(surface)
        
        # Статистика
        self._draw_stats(surface)
    
    def _draw_buttons(self, surface: pygame.Surface):
        """Нарисовать кнопки"""
        mouse_pos = pygame.mouse.get_pos()
        
        # Кнопка SPIN
        spin_rect = self.buttons['spin']
        spin_color = self.colors['button_hover'] if spin_rect.collidepoint(mouse_pos) else self.colors['button']
        if self.is_spinning or not self.game_manager.can_spin():
            spin_color = (150, 150, 150)
        
        pygame.draw.rect(surface, spin_color, spin_rect)
        pygame.draw.rect(surface, (0, 0, 0), spin_rect, 2)
        
        spin_text = "SPINNING..." if self.is_spinning else "SPIN"
        text_surface = self.font_medium.render(spin_text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=spin_rect.center)
        surface.blit(text_surface, text_rect)
        
        # Кнопки ставок
        current_bet = self.game_manager.current_bet
        for button_name, rect in self.buttons.items():
            if button_name.startswith('bet_'):
                amount = int(button_name.split('_')[1])
                button_color = self.colors['button_hover'] if rect.collidepoint(mouse_pos) else self.colors['button']
                
                if amount == current_bet:
                    button_color = (255, 255, 0)  # Выделяем текущую ставку
                
                pygame.draw.rect(surface, button_color, rect)
                pygame.draw.rect(surface, (0, 0, 0), rect, 2)
                
                text_surface = self.font_small.render(f"${amount}", True, (0, 0, 0))
                text_rect = text_surface.get_rect(center=rect.center)
                surface.blit(text_surface, text_rect)
        
        # Кнопка статистики
        stats_rect = self.buttons['stats']
        stats_color = self.colors['button_hover'] if stats_rect.collidepoint(mouse_pos) else self.colors['button']
        pygame.draw.rect(surface, stats_color, stats_rect)
        pygame.draw.rect(surface, (0, 0, 0), stats_rect, 2)
        
        text_surface = self.font_small.render("Stats", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=stats_rect.center)
        surface.blit(text_surface, text_rect)
        
        # Кнопка возврата
        back_rect = self.buttons['back']
        back_color = self.colors['button_hover'] if back_rect.collidepoint(mouse_pos) else self.colors['button']
        pygame.draw.rect(surface, back_color, back_rect)
        pygame.draw.rect(surface, (0, 0, 0), back_rect, 2)
        
        text_surface = self.font_small.render("Back", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=back_rect.center)
        surface.blit(text_surface, text_rect)
    
    def _draw_info(self, surface: pygame.Surface):
        """Нарисовать информацию о балансе и ставке"""
        stats = self.game_manager.get_stats()
        
        # Баланс
        balance_text = f"Balance: ${stats['balance']}"
        balance_surface = self.font_medium.render(balance_text, True, self.colors['text'])
        surface.blit(balance_surface, (20, self.screen_height - 80))
        
        # Текущая ставка
        bet_text = f"Bet: ${stats['current_bet']}"
        bet_surface = self.font_medium.render(bet_text, True, self.colors['text'])
        surface.blit(bet_surface, (20, self.screen_height - 50))
        
        # Статистика
        win_rate_text = f"Win Rate: {stats['win_rate']}%"
        win_rate_surface = self.font_small.render(win_rate_text, True, self.colors['text'])
        surface.blit(win_rate_surface, (20, self.screen_height - 20))
    
    def _draw_win_message(self, surface: pygame.Surface):
        """Нарисовать сообщение о выигрыше"""
        if not self.last_wins:
            return
        
        total_payout = sum(win['payout'] for win in self.last_wins)
        
        # Полупрозрачный фон
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # Сообщение о выигрыше
        win_text = f"WIN! ${total_payout}"
        win_surface = self.font_large.render(win_text, True, self.colors['win'])
        win_rect = win_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        surface.blit(win_surface, win_rect)
        
        # Детали выигрыша
        for i, win in enumerate(self.last_wins):
            detail_text = f"{win['count']}x {win['symbol'].value} = ${win['payout']}"
            detail_surface = self.font_medium.render(detail_text, True, self.colors['text'])
            detail_rect = detail_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50 + i * 30))
            surface.blit(detail_surface, detail_rect)
    
    def _draw_stats(self, surface: pygame.Surface):
        """Нарисовать статистику"""
        stats = self.game_manager.get_stats()
        
        # Статистика справа
        stats_x = self.screen_width - 200
        stats_y = 50
        
        stats_texts = [
            f"Spins: {stats['total_spins']}",
            f"Wins: {stats['total_wins']}",
            f"Biggest Win: ${stats['biggest_win']}",
            f"Current Streak: {stats['current_streak']}",
            f"Longest Streak: {stats['longest_streak']}"
        ]
        
        for i, text in enumerate(stats_texts):
            text_surface = self.font_small.render(text, True, self.colors['text'])
            surface.blit(text_surface, (stats_x, stats_y + i * 25))
