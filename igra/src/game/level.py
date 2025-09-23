import pygame
from typing import List

from src import settings
from src.game.enemy import Enemy


class Level:
	def __init__(self, index: int = 0) -> None:
		self.index = index % max(1, len(settings.LEVELS))
		cfg = settings.LEVELS[self.index]
		self.platforms: List[pygame.Rect] = [
			pygame.Rect(x, y, w, h) for (x, y, w, h) in cfg["platforms"]
		]
		self.collectibles: List[pygame.Rect] = [
			pygame.Rect(x, y, w, h) for (x, y, w, h) in cfg["collectibles"]
		]
		self.portal: pygame.Rect = pygame.Rect(*cfg["portal"])
		self.enemies: List[Enemy] = [
			Enemy(pygame.Rect(x, y, w, h), min_x, max_x, speed)
			for (x, y, w, h, min_x, max_x, speed) in cfg["enemies"]
		]
		self.spawn = cfg["spawn"]

	def update(self, dt: float) -> None:
		for e in self.enemies:
			e.update(dt)

	def draw(self, surface: pygame.Surface) -> None:
		for p in self.platforms:
			pygame.draw.rect(surface, settings.COLOR_PLATFORM, p)
		for c in self.collectibles:
			pygame.draw.rect(surface, settings.COLOR_COLLECTIBLE, c)
		# Portal color depends on lock state
		portal_color = settings.COLOR_PORTAL if self.is_portal_active() else (120, 120, 140)
		pygame.draw.rect(surface, portal_color, self.portal, border_radius=6)
		for e in self.enemies:
			e.draw(surface)

	def remaining_collectibles(self) -> int:
		return len(self.collectibles)

	def is_portal_active(self) -> bool:
		return self.remaining_collectibles() == 0

	def try_collect(self, player_rect: pygame.Rect) -> int:
		collected = 0
		remaining: List[pygame.Rect] = []
		for c in self.collectibles:
			if player_rect.colliderect(c):
				collected += 1
			else:
				remaining.append(c)
		self.collectibles = remaining
		return collected

	def reached_portal(self, player_rect: pygame.Rect) -> bool:
		return self.is_portal_active() and player_rect.colliderect(self.portal)

	def hit_enemy(self, player_rect: pygame.Rect) -> bool:
		return any(player_rect.colliderect(e.rect) for e in self.enemies)
