import pygame
from dataclasses import dataclass

from src import settings


@dataclass
class Enemy:
	rect: pygame.Rect
	min_x: int
	max_x: int
	speed: float
	_direction: int = 1

	def update(self, dt: float) -> None:
		self.rect.x += int(self.speed * self._direction * dt)
		if self.rect.left <= self.min_x:
			self.rect.left = self.min_x
			self._direction = 1
		elif self.rect.right >= self.max_x:
			self.rect.right = self.max_x
			self._direction = -1

	def draw(self, surface: pygame.Surface) -> None:
		pygame.draw.rect(surface, settings.COLOR_ENEMY, self.rect)
