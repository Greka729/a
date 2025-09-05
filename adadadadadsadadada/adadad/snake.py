import os
import sys
import random
from dataclasses import dataclass

import pygame


# ----------------------------
# Configuration
# ----------------------------
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
CELL_SIZE = 20

GRID_COLS = WINDOW_WIDTH // CELL_SIZE
GRID_ROWS = WINDOW_HEIGHT // CELL_SIZE

BACKGROUND_COLOR = (18, 18, 18)
GRID_COLOR = (30, 30, 30)
SNAKE_HEAD_COLOR = (0, 200, 0)
SNAKE_BODY_COLOR = (0, 140, 0)
FOOD_COLOR = (220, 30, 30)
TEXT_COLOR = (240, 240, 240)
HIGHLIGHT_COLOR = (255, 215, 0)

FONT_NAME = "consolas"


@dataclass
class Point:
    x: int
    y: int


class Sounds:
    def __init__(self) -> None:
        self.enabled = False
        self.eat = None
        self.game_over = None

        try:
            pygame.mixer.init()
            self.enabled = True
            self._load_assets()
        except Exception:
            self.enabled = False

    def _load_assets(self) -> None:
        base = os.path.join(os.path.dirname(__file__), "assets")
        eat_path = os.path.join(base, "eat.wav")
        game_over_path = os.path.join(base, "game_over.wav")
        try:
            if os.path.exists(eat_path):
                self.eat = pygame.mixer.Sound(eat_path)
            if os.path.exists(game_over_path):
                self.game_over = pygame.mixer.Sound(game_over_path)
        except Exception:
            # If loading fails, disable sounds silently
            self.enabled = False

    def play_eat(self) -> None:
        if self.enabled and self.eat is not None:
            try:
                self.eat.play()
            except Exception:
                pass

    def play_game_over(self) -> None:
        if self.enabled and self.game_over is not None:
            try:
                self.game_over.play()
            except Exception:
                pass


class SnakeGame:
    def __init__(self) -> None:
        pygame.init()
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Snake - Pygame")
        self.clock = pygame.time.Clock()

        self.font_small = pygame.font.SysFont(FONT_NAME, 22)
        self.font_medium = pygame.font.SysFont(FONT_NAME, 28)
        self.font_large = pygame.font.SysFont(FONT_NAME, 40)

        self.sounds = Sounds()

        self.state = "MENU"  # MENU, PLAYING, GAME_OVER
        self.score = 0
        self.high_score = self._load_high_score()

        self.direction = Point(1, 0)
        self.next_direction = Point(1, 0)
        self.snake: list[Point] = []
        self.food = Point(0, 0)

        self.difficulty = "Normal"  # Slow, Normal, Fast
        self.fps_map = {"Slow": 10, "Normal": 15, "Fast": 22}
        self.fps = self.fps_map[self.difficulty]

        self._reset_game()

    # ----------------------------
    # Persistence
    # ----------------------------
    def _high_score_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), "highscore.txt")

    def _load_high_score(self) -> int:
        try:
            with open(self._high_score_path(), "r", encoding="utf-8") as f:
                return int(f.read().strip() or 0)
        except Exception:
            return 0

    def _save_high_score(self) -> None:
        try:
            with open(self._high_score_path(), "w", encoding="utf-8") as f:
                f.write(str(self.high_score))
        except Exception:
            pass

    # ----------------------------
    # Game lifecycle
    # ----------------------------
    def _reset_game(self) -> None:
        mid_x = GRID_COLS // 2
        mid_y = GRID_ROWS // 2
        self.snake = [Point(mid_x, mid_y), Point(mid_x - 1, mid_y), Point(mid_x - 2, mid_y)]
        self.direction = Point(1, 0)
        self.next_direction = Point(1, 0)
        self.score = 0
        self._spawn_food()

    def _spawn_food(self) -> None:
        occupied = {(p.x, p.y) for p in self.snake}
        free_cells_count = GRID_COLS * GRID_ROWS - len(occupied)
        if free_cells_count <= 0:
            # No space; player wins effectively
            return
        while True:
            x = random.randint(0, GRID_COLS - 1)
            y = random.randint(0, GRID_ROWS - 1)
            if (x, y) not in occupied:
                self.food = Point(x, y)
                return

    # ----------------------------
    # Input handling
    # ----------------------------
    def _handle_menu_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.difficulty = "Slow"
                self.fps = self.fps_map[self.difficulty]
            elif event.key == pygame.K_2:
                self.difficulty = "Normal"
                self.fps = self.fps_map[self.difficulty]
            elif event.key == pygame.K_3:
                self.difficulty = "Fast"
                self.fps = self.fps_map[self.difficulty]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.state = "PLAYING"

    def _handle_play_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)
            if event.key in (pygame.K_UP, pygame.K_w):
                self._queue_direction_change(Point(0, -1))
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._queue_direction_change(Point(0, 1))
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._queue_direction_change(Point(-1, 0))
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._queue_direction_change(Point(1, 0))

    def _handle_game_over_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_r, pygame.K_KP_ENTER):
                self._reset_game()
                self.state = "MENU"
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)

    def _queue_direction_change(self, new_dir: Point) -> None:
        # Prevent reversing directly into the snake's neck
        if (new_dir.x == -self.direction.x and new_dir.y == -self.direction.y):
            return
        self.next_direction = new_dir

    # ----------------------------
    # Update
    # ----------------------------
    def _update(self) -> None:
        # Apply direction chosen since last frame
        self.direction = Point(self.next_direction.x, self.next_direction.y)

        new_head = Point(self.snake[0].x + self.direction.x, self.snake[0].y + self.direction.y)

        # Collisions with walls
        if not (0 <= new_head.x < GRID_COLS and 0 <= new_head.y < GRID_ROWS):
            self._on_game_over()
            return

        # Collisions with self
        if any(segment.x == new_head.x and segment.y == new_head.y for segment in self.snake):
            self._on_game_over()
            return

        # Move snake
        self.snake.insert(0, new_head)

        # Check for food
        if new_head.x == self.food.x and new_head.y == self.food.y:
            self.score += 1
            if self.sounds:
                self.sounds.play_eat()
            self._spawn_food()
        else:
            # Remove tail segment to simulate movement
            self.snake.pop()

    def _on_game_over(self) -> None:
        if self.sounds:
            self.sounds.play_game_over()
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()
        self.state = "GAME_OVER"

    # ----------------------------
    # Rendering
    # ----------------------------
    def _draw_grid(self) -> None:
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(self.window, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(self.window, GRID_COLOR, (0, y), (WINDOW_WIDTH, y), 1)

    def _draw_text(self, text: str, font: pygame.font.Font, color: tuple[int, int, int], center: tuple[int, int]) -> None:
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=center)
        self.window.blit(surf, rect)

    def _render_menu(self) -> None:
        self.window.fill(BACKGROUND_COLOR)
        self._draw_grid()
        self._draw_text("SNAKE", self.font_large, HIGHLIGHT_COLOR, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80))
        self._draw_text("Choose difficulty: 1) Slow   2) Normal   3) Fast", self.font_medium, TEXT_COLOR, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        self._draw_text(f"Selected: {self.difficulty}", self.font_medium, TEXT_COLOR, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        self._draw_text("Press Enter to start", self.font_medium, TEXT_COLOR, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 70))
        self._draw_text(f"High score: {self.high_score}", self.font_small, TEXT_COLOR, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 110))

    def _render_hud(self) -> None:
        score_text = self.font_small.render(f"Score: {self.score}", True, TEXT_COLOR)
        hs_text = self.font_small.render(f"High: {self.high_score}", True, TEXT_COLOR)
        self.window.blit(score_text, (10, 6))
        self.window.blit(hs_text, (WINDOW_WIDTH - hs_text.get_width() - 10, 6))

    def _render_play(self) -> None:
        self.window.fill(BACKGROUND_COLOR)
        self._draw_grid()

        # Draw food
        pygame.draw.rect(
            self.window,
            FOOD_COLOR,
            (self.food.x * CELL_SIZE + 1, self.food.y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2),
            border_radius=3,
        )

        # Draw snake
        for index, segment in enumerate(self.snake):
            color = SNAKE_HEAD_COLOR if index == 0 else SNAKE_BODY_COLOR
            pygame.draw.rect(
                self.window,
                color,
                (segment.x * CELL_SIZE + 1, segment.y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2),
                border_radius=4,
            )

        self._render_hud()

    def _render_game_over(self) -> None:
        self.window.fill(BACKGROUND_COLOR)
        self._draw_grid()
        self._draw_text("GAME OVER", self.font_large, HIGHLIGHT_COLOR, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
        self._draw_text(f"Score: {self.score}", self.font_medium, TEXT_COLOR, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self._draw_text(f"High score: {self.high_score}", self.font_medium, TEXT_COLOR, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40))
        self._draw_text("Press Enter or R to restart, Esc to quit", self.font_small, TEXT_COLOR, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 90))

    # ----------------------------
    # Main loop
    # ----------------------------
    def run(self) -> None:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)

                if self.state == "MENU":
                    self._handle_menu_input(event)
                elif self.state == "PLAYING":
                    self._handle_play_input(event)
                elif self.state == "GAME_OVER":
                    self._handle_game_over_input(event)

            if self.state == "PLAYING":
                self._update()

            if self.state == "MENU":
                self._render_menu()
            elif self.state == "PLAYING":
                self._render_play()
            elif self.state == "GAME_OVER":
                self._render_game_over()

            pygame.display.flip()
            self.clock.tick(self.fps)


if __name__ == "__main__":
    SnakeGame().run()


