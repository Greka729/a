import pygame
from typing import Optional, Dict

from src import settings
from src.game.player import Player
from src.game.level import Level
from src.game.save import load_progress, save_progress, load_settings, save_settings, load_controls, save_controls
from src.game.sound import SoundManager


class Game:
	def __init__(self) -> None:
		pygame.display.set_caption(settings.TITLE)
		self.screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
		self.clock = pygame.time.Clock()
		self.running = True
		self.paused = False
		self.state = "menu"  # "menu" | "play" | "settings" | "controls"

		self.level_index = 0
		self.level = Level(self.level_index)
		spawn_x, spawn_y = self.level.spawn
		self.player = Player(pygame.Rect(spawn_x, spawn_y, 28, 36))
		self.score = 0

		# Progress
		progress = load_progress()
		self.best_score = int(progress.get("best_score", 0))

		# Sound
		self.sound = SoundManager()
		self.sound.load()
		loaded_audio = load_settings()
		self.sound.muted = bool(loaded_audio.get("muted", False))
		self.sound.set_master_volume(float(loaded_audio.get("volume", 0.6)))

		# Controls
		self.controls: Dict[str, int] = load_controls()

		self.font = pygame.font.SysFont("consolas", 20)
		self.menu_font = pygame.font.SysFont("consolas", 28)
		self.settings_cursor = 0
		self.controls_cursor = 0
		self.controls_waiting = False

	def toggle_pause(self) -> None:
		if self.state != "play":
			return
		self.paused = not self.paused

	def handle_events(self) -> None:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.on_quit()
			elif event.type == pygame.KEYDOWN:
				if self.state == "menu":
					if event.key in (pygame.K_RETURN, pygame.K_SPACE):
						self.start_game()
					elif event.key == pygame.K_s:
						self.state = "settings"
					elif event.key == pygame.K_c:
						self.state = "controls"
					elif event.key == pygame.K_ESCAPE:
						self.on_quit()
				elif self.state == "settings":
					if event.key == pygame.K_ESCAPE:
						self.state = "menu"
					elif event.key in (pygame.K_UP, pygame.K_DOWN):
						self.settings_cursor = 1 - self.settings_cursor
					elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
						if self.settings_cursor == 0:
							self.sound.toggle_mute()
							self.save_current_settings()
						else:
							step = -0.1 if event.key == pygame.K_LEFT else 0.1
							if event.key in (pygame.K_RETURN, pygame.K_SPACE):
								step = 0.1
							self.sound.set_master_volume(self.sound.master_volume + step)
							self.save_current_settings()
				elif self.state == "controls":
					if event.key == pygame.K_ESCAPE and not self.controls_waiting:
						self.state = "menu"
					elif not self.controls_waiting and event.key in (pygame.K_UP, pygame.K_DOWN):
						self.controls_cursor = (self.controls_cursor + (1 if event.key == pygame.K_DOWN else -1)) % 4
					elif not self.controls_waiting and event.key in (pygame.K_RETURN, pygame.K_SPACE):
						self.controls_waiting = True
					elif self.controls_waiting:
						keyname = ["left", "right", "jump", "pause"][self.controls_cursor]
						self.controls[keyname] = event.key
						save_controls(self.controls)
						self.controls_waiting = False
				elif self.state == "play":
					if event.key == pygame.K_ESCAPE:
						self.toggle_pause()
					elif event.key == pygame.K_m:
						self.sound.toggle_mute()
						self.save_current_settings()

	def save_current_settings(self) -> None:
		save_settings(self.sound.muted, self.sound.master_volume)

	def on_quit(self) -> None:
		self.best_score = max(self.best_score, self.score)
		save_progress({"best_score": self.best_score})
		self.save_current_settings()
		self.sound.stop_music()
		self.running = False

	def start_game(self) -> None:
		self.state = "play"
		self.paused = False
		self.score = 0
		self.level_index = 0
		self.level = Level(self.level_index)
		spawn_x, spawn_y = self.level.spawn
		self.player = Player(pygame.Rect(spawn_x, spawn_y, 28, 36))
		self.sound.start_music()

	def reset_player(self) -> None:
		spawn_x, spawn_y = self.level.spawn
		self.player.rect.topleft = (spawn_x, spawn_y)
		self.player.velocity_y = 0.0

	def next_level(self) -> None:
		self.level_index = (self.level_index + 1) % max(1, len(settings.LEVELS))
		self.level = Level(self.level_index)
		self.reset_player()

	def update(self, dt: float) -> None:
		if self.state != "play":
			return
		if self.paused:
			return
		jumped = self.player.update(dt, self.level.platforms, self.controls)
		if jumped:
			self.sound.play_jump()
		self.level.update(dt)
		gained = self.level.try_collect(self.player.rect)
		if gained:
			self.sound.play_collect()
			self.score += gained

		if self.player.rect.top > settings.HEIGHT:
			self.reset_player()

		if self.level.hit_enemy(self.player.rect):
			self.sound.play_hit()
			self.reset_player()

		if self.level.reached_portal(self.player.rect):
			self.best_score = max(self.best_score, self.score)
			save_progress({"best_score": self.best_score})
			self.sound.play_portal()
			self.next_level()

	def draw_hud(self) -> None:
		score_surf = self.font.render(f"Score: {self.score}", True, settings.COLOR_TEXT)
		best_surf = self.font.render(f"Best: {self.best_score}", True, settings.COLOR_TEXT)
		lvl_surf = self.font.render(f"Level: {self.level_index + 1}", True, settings.COLOR_TEXT)
		rem = self.level.remaining_collectibles()
		rem_surf = self.font.render(f"Crystals left: {rem}", True, settings.COLOR_TEXT)
		fps_surf = self.font.render(f"FPS: {int(self.clock.get_fps())}", True, settings.COLOR_TEXT)
		self.screen.blit(score_surf, (10, 8))
		self.screen.blit(best_surf, (10, 30))
		self.screen.blit(lvl_surf, (10, 52))
		self.screen.blit(rem_surf, (10, 74))
		self.screen.blit(self.font.render("M: mute", True, settings.COLOR_TEXT), (10, 96))
		if self.paused:
			p_surf = self.font.render("PAUSED - Press ESC", True, settings.COLOR_TEXT)
			self.screen.blit(p_surf, (settings.WIDTH//2 - p_surf.get_width()//2, settings.HEIGHT//2 - 10))

	def draw_menu(self) -> None:
		self.screen.fill(settings.BG_COLOR)
		title = self.menu_font.render("SkyRun", True, settings.COLOR_TEXT)
		start = self.font.render("Press Enter to Start", True, settings.COLOR_TEXT)
		exit_ = self.font.render("Esc to Quit", True, settings.COLOR_TEXT)
		best = self.font.render(f"Best: {self.best_score}", True, settings.COLOR_TEXT)
		settings_hint = self.font.render("S: Settings", True, settings.COLOR_TEXT)
		controls_hint = self.font.render("C: Controls", True, settings.COLOR_TEXT)
		self.screen.blit(title, (settings.WIDTH//2 - title.get_width()//2, 130))
		self.screen.blit(best, (settings.WIDTH//2 - best.get_width()//2, 180))
		self.screen.blit(start, (settings.WIDTH//2 - start.get_width()//2, 230))
		self.screen.blit(settings_hint, (settings.WIDTH//2 - settings_hint.get_width()//2, 270))
		self.screen.blit(controls_hint, (settings.WIDTH//2 - controls_hint.get_width()//2, 300))
		self.screen.blit(exit_, (settings.WIDTH//2 - exit_.get_width()//2, 340))
		pygame.display.flip()

	def draw_controls(self) -> None:
		self.screen.fill(settings.BG_COLOR)
		title = self.menu_font.render("Controls", True, settings.COLOR_TEXT)
		self.screen.blit(title, (settings.WIDTH//2 - title.get_width()//2, 120))
		labels = ["Left", "Right", "Jump", "Pause"]
		keys = [pygame.key.name(self.controls["left"]), pygame.key.name(self.controls["right"]), pygame.key.name(self.controls["jump"]), pygame.key.name(self.controls["pause"])]
		for i, (label, key) in enumerate(zip(labels, keys)):
			line = self.font.render(f"{label}: {key}", True, settings.COLOR_TEXT)
			y = 200 + i*34
			self.screen.blit(line, (settings.WIDTH//2 - line.get_width()//2, y))
			if i == self.controls_cursor:
				pygame.draw.rect(self.screen, settings.COLOR_TEXT, (settings.WIDTH//2 - line.get_width()//2 - 14, y - 2, 8, 8))
		status = "Press a key..." if self.controls_waiting else "Enter: Rebind, Esc: Back"
		status_surf = self.font.render(status, True, settings.COLOR_TEXT)
		self.screen.blit(status_surf, (settings.WIDTH//2 - status_surf.get_width()//2, 360))
		pygame.display.flip()

	def draw_settings(self) -> None:
		self.screen.fill(settings.BG_COLOR)
		title = self.menu_font.render("Settings", True, settings.COLOR_TEXT)
		mute_label = "+ Mute" if not self.sound.muted else "- Mute"
		vol_pct = int(self.sound.master_volume * 100)
		vol_label = f"Volume: {vol_pct}%"
		mute_surf = self.font.render(mute_label, True, settings.COLOR_TEXT)
		vol_surf = self.font.render(vol_label, True, settings.COLOR_TEXT)
		back = self.font.render("Esc: Back", True, settings.COLOR_TEXT)

		self.screen.blit(title, (settings.WIDTH//2 - title.get_width()//2, 140))
		self.screen.blit(mute_surf, (settings.WIDTH//2 - mute_surf.get_width()//2, 220))
		self.screen.blit(vol_surf, (settings.WIDTH//2 - vol_surf.get_width()//2, 260))
		self.screen.blit(back, (settings.WIDTH//2 - back.get_width()//2, 320))

		cursor_y = 224 if self.settings_cursor == 0 else 264
		pygame.draw.polygon(self.screen, settings.COLOR_TEXT, [
			(settings.WIDTH//2 - 120, cursor_y),
			(settings.WIDTH//2 - 100, cursor_y - 8),
			(settings.WIDTH//2 - 100, cursor_y + 8),
		])
		pygame.display.flip()

	def draw_play(self) -> None:
		self.screen.fill(settings.BG_COLOR)
		self.level.draw(self.screen)
		self.player.draw(self.screen)
		self.draw_hud()
		pygame.display.flip()

	def draw(self) -> None:
		if self.state == "menu":
			self.draw_menu()
		elif self.state == "settings":
			self.draw_settings()
		elif self.state == "controls":
			self.draw_controls()
		else:
			self.draw_play()

	def run(self) -> None:
		while self.running:
			dt = self.clock.tick(settings.FPS) / 1000.0
			self.handle_events()
			self.update(dt)
			self.draw()
