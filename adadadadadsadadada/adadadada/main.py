import os
import sys
import random
import time
import pygame


# -----------------------------
# Configuration and constants
# -----------------------------
WINDOW_TITLE = "Tetris (Pygame)"

# Playfield size (width x height in cells)
GRID_WIDTH = 10
GRID_HEIGHT = 20

# Cell and UI sizing
CELL_SIZE = 32
BORDER = 2
PANEL_WIDTH = 7  # in cells, for next/score

SCREEN_WIDTH = (GRID_WIDTH + PANEL_WIDTH) * CELL_SIZE + BORDER * 3
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE + BORDER * 2

FPS = 60

# Colors
COLOR_BG = (16, 18, 24)
COLOR_GRID = (30, 34, 42)
COLOR_GHOST = (90, 90, 100)
COLOR_TEXT = (230, 230, 230)

TETROMINO_COLORS = {
    'I': (0, 199, 199),
    'O': (199, 199, 0),
    'T': (153, 0, 199),
    'S': (0, 199, 0),
    'Z': (199, 0, 0),
    'J': (0, 0, 199),
    'L': (199, 99, 0),
    # Bomb bonus
    'B': (230, 90, 0),
}


# -----------------------------
# Tetromino definitions (SRS-like)
# Each rotation is a list of (x, y) for the 4 blocks
# Origin is the piece position; coordinates are relative
# -----------------------------
SHAPES = {
    'I': [
        [( -1, 0), (0, 0), (1, 0), (2, 0)],
        [( 1, -1), (1, 0), (1, 1), (1, 2)],
        [( -1, 1), (0, 1), (1, 1), (2, 1)],
        [( 0, -1), (0, 0), (0, 1), (0, 2)],
    ],
    'O': [
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
    ],
    'T': [
        [(0, 0), (-1, 0), (1, 0), (0, 1)],
        [(0, 0), (0, -1), (0, 1), (1, 0)],
        [(0, 0), (-1, 0), (1, 0), (0, -1)],
        [(0, 0), (0, -1), (0, 1), (-1, 0)],
    ],
    'S': [
        [(0, 0), (1, 0), (0, 1), (-1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, -1)],
        [(0, 0), (1, 0), (0, -1), (-1, -1)],
        [(0, 0), (-1, 0), (-1, 1), (0, -1)],
    ],
    'Z': [
        [(0, 0), (-1, 0), (0, 1), (1, 1)],
        [(0, 0), (0, -1), (1, 0), (1, 1)],
        [(0, 0), (-1, -1), (0, -1), (1, 0)],
        [(0, 0), (-1, 0), (-1, -1), (0, 1)],
    ],
    'J': [
        [(0, 0), (-1, 0), (1, 0), (-1, 1)],
        [(0, 0), (0, -1), (0, 1), (1, 1)],
        [(0, 0), (-1, 0), (1, 0), (1, -1)],
        [(0, 0), (-1, -1), (0, -1), (0, 1)],
    ],
    'L': [
        [(0, 0), (-1, 0), (1, 0), (1, 1)],
        [(0, 0), (0, -1), (0, 1), (1, -1)],
        [(0, 0), (-1, 0), (1, 0), (-1, -1)],
        [(0, 0), (-1, 1), (0, -1), (0, 1)],
    ],
    # Bomb: single-cell piece, behaves like a bonus
    'B': [
        [(0, 0)],
        [(0, 0)],
        [(0, 0)],
        [(0, 0)],
    ],
}

# Super Rotation System (SRS) basic wall kicks
# Each entry: (from_rot, to_rot): list of (dx, dy)
SRS_KICKS = {
    'JLSTZ': {
        (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
        (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
        (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
        (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
        (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
        (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
        (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
        (0, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    },
    'I': {
        (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
        (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
        (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
        (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
        (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
        (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
        (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
        (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    },
    'O': {}
}


class Tetromino:
    def __init__(self, name: str, x: int, y: int):
        self.name = name
        self.rotations = SHAPES[name]
        self.rotation = 0
        self.x = x
        self.y = y
        self.color = TETROMINO_COLORS[name]

    def get_cells(self, rotation: int | None = None, offset: tuple[int, int] | None = None):
        if rotation is None:
            rotation = self.rotation
        if offset is None:
            offset = (0, 0)
        dx, dy = offset
        return [(self.x + dx + cx, self.y + dy + cy) for (cx, cy) in self.rotations[rotation]]

    def rotate_with_kicks(self, board, direction: int) -> bool:
        # direction: +1 cw, -1 ccw
        old_rot = self.rotation
        new_rot = (self.rotation + direction) % 4
        group = 'I' if self.name == 'I' else ('O' if self.name == 'O' else 'JLSTZ')
        kicks = SRS_KICKS.get(group, {}).get((old_rot, new_rot), [(0, 0)])
        for (kx, ky) in kicks:
            if board.is_valid_cells(self.get_cells(rotation=new_rot, offset=(kx, ky))):
                self.rotation = new_rot
                self.x += kx
                self.y += ky
                return True
        return False


class Board:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid: list[list[tuple[int, int, int] | None]] = [
            [None for _ in range(width)] for _ in range(height)
        ]

    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def cell_free(self, x: int, y: int) -> bool:
        if not self.inside(x, y):
            return False
        return self.grid[y][x] is None

    def is_valid_cells(self, cells: list[tuple[int, int]]) -> bool:
        for (x, y) in cells:
            if x < 0 or x >= self.width or y >= self.height:
                return False
            if y >= 0 and self.grid[y][x] is not None:
                return False
        return True

    def lock_tetromino(self, t: Tetromino):
        for (x, y) in t.get_cells():
            if 0 <= y < self.height:
                self.grid[y][x] = t.color

    def explode(self, center_x: int, center_y: int, radius: int = 1) -> int:
        # Clears a square of size (2*radius+1) around center; returns cleared cell count
        cleared = 0
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                x = center_x + dx
                y = center_y + dy
                if self.inside(x, y) and self.grid[y][x] is not None:
                    self.grid[y][x] = None
                    cleared += 1
        return cleared

    def clear_full_lines(self) -> int:
        new_grid = [row for row in self.grid if any(cell is None for cell in row)]
        cleared = self.height - len(new_grid)
        for _ in range(cleared):
            new_grid.insert(0, [None for _ in range(self.width)])
        self.grid = new_grid
        return cleared


class SevenBag:
    def __init__(self):
        self.bag: list[str] = []

    def next(self) -> str:
        if not self.bag:
            # Occasionally include a bomb bonus 'B' in the bag
            self.bag = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']
            # 1 in 3 chance to add a bomb to this bag refill
            if random.random() < 0.33:
                self.bag.append('B')
            random.shuffle(self.bag)
        return self.bag.pop()


class Game:
    def __init__(self):
        pygame.init()
        # Gentle key repeat for smoother held movement
        pygame.key.set_repeat(180, 45)
        pygame.display.set_caption(WINDOW_TITLE)
        self.fullscreen = False
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.SysFont("consolas", 18)
        self.font_big = pygame.font.SysFont("consolas", 28, bold=True)

        self.board = Board(GRID_WIDTH, GRID_HEIGHT)
        self.bag = SevenBag()
        self.current: Tetromino | None = None
        self.next_piece: str = self.bag.next()

        self.drop_interval_ms = 800  # gravity in ms; reduced as level grows
        self.soft_drop_interval_ms = 50
        self.last_drop_time = 0
        self.soft_dropping = False

        self.score = 0
        self.level = 0
        self.lines_cleared = 0

        self.game_over = False
        self.paused = False

        # Audio
        self.audio = AudioManager()

        self.spawn_new_piece()

    def spawn_new_piece(self):
        name = self.next_piece
        self.next_piece = self.bag.next()
        spawn_x = GRID_WIDTH // 2
        spawn_y = -2  # above visible area to allow rotation
        self.current = Tetromino(name, spawn_x, spawn_y)
        # Nudge spawn for I and O to better center
        if name == 'I':
            self.current.y = -1
        if not self.board.is_valid_cells(self.current.get_cells()):
            self.game_over = True
            self.audio.play("gameover")

    def increase_level_if_needed(self):
        target_level = self.lines_cleared // 10
        if target_level != self.level:
            self.level = target_level
            # Gravity scaling: cap to a reasonable minimum
            self.drop_interval_ms = max(80, int(800 * (0.85 ** self.level)))

    def add_score_for_lines(self, lines: int):
        if lines == 0:
            return
        base = {1: 100, 2: 300, 3: 500, 4: 800}.get(lines, 0)
        self.score += base * (self.level + 1)

    def hard_drop(self):
        if not self.current:
            return
        distance = 0
        while self.board.is_valid_cells(self.current.get_cells(offset=(0, 1))):
            self.current.y += 1
            distance += 1
        # Optional: award small points per cell for hard drop
        self.score += distance * 2
        self.lock_and_continue()

    def move(self, dx: int):
        if not self.current:
            return
        if self.board.is_valid_cells(self.current.get_cells(offset=(dx, 0))):
            self.current.x += dx

    def rotate(self, direction: int):
        if not self.current:
            return False
        return self.current.rotate_with_kicks(self.board, direction)

    def soft_drop(self, enable: bool):
        self.soft_dropping = enable

    def gravity_tick(self):
        if not self.current:
            return
        interval = self.soft_drop_interval_ms if self.soft_dropping else self.drop_interval_ms
        now = pygame.time.get_ticks()
        if now - self.last_drop_time >= interval:
            self.last_drop_time = now
            if self.board.is_valid_cells(self.current.get_cells(offset=(0, 1))):
                self.current.y += 1
                if self.soft_dropping:
                    self.score += 1  # soft drop point per cell
            else:
                self.lock_and_continue()

    def lock_and_continue(self):
        if not self.current:
            return
        # Проверка: часть фигуры выше видимой области
        topped_out = any(cy < 0 for (_, cy) in self.current.get_cells())

        # Special handling for bomb bonus
        if self.current.name == 'B':
            # Determine the impact center: bottom-most cell of the bomb's current position
            # Since B is 1x1, its cell is the center
            [(cx, cy)] = self.current.get_cells()
            # Adjust to in-bounds row if above
            if cy < 0:
                cy = 0
            self.board.explode(cx, cy, radius=1)
            # Play explosion-specific sound; fallback to clear if not available
            self.audio.play("explosion")
            cleared = self.board.clear_full_lines()
        else:
            self.board.lock_tetromino(self.current)
            self.audio.play("lock")
            cleared = self.board.clear_full_lines()
        if cleared > 0:
            self.audio.play("clear")
        self.lines_cleared += cleared
        self.add_score_for_lines(cleared)
        self.increase_level_if_needed()

        if topped_out:
            self.game_over = True
            self.audio.play("gameover")
            return

        self.spawn_new_piece()

    def toggle_pause(self):
        if not self.game_over:
            self.paused = not self.paused

    def toggle_fullscreen(self):
        try:
            current_flags = self.screen.get_flags() if self.screen else 0
            is_full = bool(current_flags & pygame.FULLSCREEN)
            if is_full:
                # Return to windowed mode at designed size
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                self.fullscreen = False
            else:
                # Enter fullscreen. Try SCALED first, then fallback to plain FULLSCREEN.
                info = pygame.display.Info()
                desktop_size = (info.current_w, info.current_h)
                try:
                    self.screen = pygame.display.set_mode(desktop_size, pygame.FULLSCREEN | pygame.SCALED)
                    self.fullscreen = True
                except Exception:
                    try:
                        self.screen = pygame.display.set_mode(desktop_size, pygame.FULLSCREEN)
                        self.fullscreen = True
                    except Exception:
                        # Last resort: try (0,0) with FULLSCREEN
                        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        self.fullscreen = True
        except Exception:
            pass

    def restart(self):
        self.__init__()

    def piece_shadow_y(self) -> int:
        if not self.current:
            return 0
        ghost = Tetromino(self.current.name, self.current.x, self.current.y)
        ghost.rotation = self.current.rotation
        while self.board.is_valid_cells(ghost.get_cells(offset=(0, 1))):
            ghost.y += 1
        return ghost.y

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                if event.key == pygame.K_p:
                    self.toggle_pause()
                if event.key == pygame.K_m:
                    self.audio.toggle_music()
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.restart()
                    continue
                if self.paused:
                    continue
                if event.key == pygame.K_LEFT:
                    self.move(-1)
                    self.audio.play("move")
                elif event.key == pygame.K_RIGHT:
                    self.move(1)
                    self.audio.play("move")
                elif event.key == pygame.K_UP:
                    if self.rotate(1):
                        self.audio.play("rotate")
                elif event.key == pygame.K_DOWN:
                    self.soft_drop(True)
                elif event.key == pygame.K_SPACE:
                    self.hard_drop()
                    self.audio.play("drop")
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    self.soft_drop(False)

    def draw_cell(self, x: int, y: int, color: tuple[int, int, int]):
        px = BORDER + x * CELL_SIZE
        py = BORDER + y * CELL_SIZE
        rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, COLOR_GRID, rect, 2)

    def render_board(self):
        # Background
        self.screen.fill(COLOR_BG)
        # Playfield background
        playfield_rect = pygame.Rect(
            BORDER, BORDER, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE
        )
        pygame.draw.rect(self.screen, (24, 27, 35), playfield_rect)

        # Grid cells
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.board.grid[y][x] is not None:
                    self.draw_cell(x, y, self.board.grid[y][x])

        # Current piece shadow
        if self.current:
            shadow_y = self.piece_shadow_y()
            for (cx, cy) in self.current.get_cells():
                sy = cy + (shadow_y - self.current.y)
                if sy >= 0:
                    self.draw_cell(cx, sy, COLOR_GHOST)

        # Current piece
        if self.current:
            for (cx, cy) in self.current.get_cells():
                if cy >= 0:
                    self.draw_cell(cx, cy, self.current.color)

        # Side panel
        panel_x = BORDER * 2 + GRID_WIDTH * CELL_SIZE
        panel_rect = pygame.Rect(
            panel_x, BORDER, PANEL_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE
        )
        pygame.draw.rect(self.screen, (24, 27, 35), panel_rect)

        # Text HUD
        def blit_text(text, x, y, big=False):
            surf = (self.font_big if big else self.font_small).render(text, True, COLOR_TEXT)
            self.screen.blit(surf, (x, y))

        blit_text("NEXT", panel_x + 12, BORDER + 12, big=True)
        self.render_next_piece(panel_x + 12, BORDER + 48)

        blit_text(f"Score: {self.score}", panel_x + 12, BORDER + 160)
        blit_text(f"Level: {self.level}", panel_x + 12, BORDER + 184)
        blit_text(f"Lines: {self.lines_cleared}", panel_x + 12, BORDER + 208)

        if self.paused and not self.game_over:
            self.render_center_message("PAUSED (P to resume)")
        if self.game_over:
            self.render_center_message("GAME OVER - R to restart")

    def render_next_piece(self, x: int, y: int):
        name = self.next_piece
        rotations = SHAPES[name][0]
        color = TETROMINO_COLORS[name]
        # Center next piece in a 4x4 box
        minx = min(cx for (cx, _) in rotations)
        maxx = max(cx for (cx, _) in rotations)
        miny = min(cy for (_, cy) in rotations)
        maxy = max(cy for (_, cy) in rotations)
        width = maxx - minx + 1
        height = maxy - miny + 1
        offset_x = x + (CELL_SIZE * 4 - width * CELL_SIZE) // 2
        offset_y = y + (CELL_SIZE * 4 - height * CELL_SIZE) // 2
        for (cx, cy) in rotations:
            px = offset_x + (cx - minx) * CELL_SIZE
            py = offset_y + (cy - miny) * CELL_SIZE
            rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, COLOR_GRID, rect, 2)

    def render_center_message(self, message: str):
        overlay = pygame.Surface((GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (BORDER, BORDER))
        surf = self.font_big.render(message, True, (255, 255, 255))
        rect = surf.get_rect(center=(BORDER + GRID_WIDTH * CELL_SIZE // 2, BORDER + GRID_HEIGHT * CELL_SIZE // 2))
        self.screen.blit(surf, rect)

    def run(self):
        while True:
            self.clock.tick(FPS)
            self.handle_events()
            if not self.paused and not self.game_over:
                self.gravity_tick()
            self.render_board()
            pygame.display.flip()


class AudioManager:
    def __init__(self):
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music_loaded = False
        self.music_paused = False
        try:
            pygame.mixer.init()
            self.enabled = True
        except Exception:
            self.enabled = False
            return

        assets = os.path.join(os.path.dirname(__file__), "assets")
        self._load_sound(assets, "move.wav", key="move", volume=0.25)
        self._load_sound(assets, "rotate.wav", key="rotate", volume=0.3)
        self._load_sound(assets, "lock.wav", key="lock", volume=0.35)
        self._load_sound(assets, "clear.wav", key="clear", volume=0.5)
        self._load_sound(assets, "drop.wav", key="drop", volume=0.4)
        self._load_sound(assets, "gameover.wav", key="gameover", volume=0.6)
        # Explosion sound for bomb bonus
        self._load_sound(assets, "explosion.wav", key="explosion", volume=0.6)

        music_path = os.path.join(assets, "music.ogg")
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.25)
                pygame.mixer.music.play(-1)
                self.music_loaded = True
                self.music_paused = False
            except Exception:
                pass

    def _load_sound(self, folder: str, filename: str, key: str, volume: float = 0.4):
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            try:
                s = pygame.mixer.Sound(path)
                s.set_volume(volume)
                self.sounds[key] = s
            except Exception:
                pass

    def play(self, key: str):
        if not self.enabled:
            return
        s = self.sounds.get(key)
        if s is not None:
            try:
                s.play()
            except Exception:
                pass

    def toggle_music(self):
        if not self.enabled or not self.music_loaded:
            return
        try:
            if self.music_paused:
                pygame.mixer.music.unpause()
                self.music_paused = False
            else:
                pygame.mixer.music.pause()
                self.music_paused = True
        except Exception:
            pass


def main():
    Game().run()


if __name__ == "__main__":
    main()


