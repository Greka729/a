import pygame
from dataclasses import dataclass
from typing import List, Dict

from src import settings


@dataclass
class Player:
	rect: pygame.Rect
	velocity_x: float = 0.0
	velocity_y: float = 0.0
	on_ground: bool = False

	def handle_input(self, dt: float, controls: Dict[str, int]) -> bool:
		keys = pygame.key.get_pressed()
		move = 0.0
		left = controls.get("left", pygame.K_a)
		right = controls.get("right", pygame.K_d)
		jump_key = controls.get("jump", pygame.K_SPACE)
		if keys[left]:
			move -= 1.0
		if keys[right]:
			move += 1.0
		self.velocity_x = move * settings.PLAYER_SPEED

		jumped = False
		if keys[jump_key] and self.on_ground:
			self.velocity_y = settings.PLAYER_JUMP_VELOCITY
			self.on_ground = False
			jumped = True
		return jumped

	def apply_gravity(self, dt: float) -> None:
		self.velocity_y += settings.GRAVITY * dt

	def move_and_collide(self, dt: float, platforms: List[pygame.Rect]) -> None:
		# Horizontal
		self.rect.x += int(self.velocity_x * dt)
		for platform in platforms:
			if self.rect.colliderect(platform):
				if self.velocity_x > 0:
					self.rect.right = platform.left
				elif self.velocity_x < 0:
					self.rect.left = platform.right

		# Vertical
		self.rect.y += int(self.velocity_y * dt)
		self.on_ground = False
		for platform in platforms:
			if self.rect.colliderect(platform):
				if self.velocity_y > 0:
					self.rect.bottom = platform.top
					self.velocity_y = 0.0
					self.on_ground = True
				elif self.velocity_y < 0:
					self.rect.top = platform.bottom
					self.velocity_y = 0.0

	def update(self, dt: float, platforms: List[pygame.Rect], controls: Dict[str, int]) -> bool:
		jumped = self.handle_input(dt, controls)
		self.apply_gravity(dt)
		self.move_and_collide(dt, platforms)
		return jumped

	def draw(self, surface: pygame.Surface) -> None:
		pygame.draw.rect(surface, (80, 200, 255), self.rect)
