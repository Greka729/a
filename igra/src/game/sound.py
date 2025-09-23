import os
import pygame
from typing import Optional


class SoundManager:
	def __init__(self) -> None:
		self.muted: bool = False
		self.master_volume: float = 0.6  # 0.0..1.0
		self.sfx_jump: Optional[pygame.mixer.Sound] = None
		self.sfx_collect: Optional[pygame.mixer.Sound] = None
		self.sfx_hit: Optional[pygame.mixer.Sound] = None
		self.sfx_portal: Optional[pygame.mixer.Sound] = None
		self.music_path: Optional[str] = None

	def _apply_volumes(self) -> None:
		vol = 0.0 if self.muted else self.master_volume
		try:
			pygame.mixer.music.set_volume(min(1.0, max(0.0, vol * 0.8)))
		except Exception:
			pass
		for snd in (self.sfx_jump, self.sfx_collect, self.sfx_hit, self.sfx_portal):
			try:
				if snd:
					snd.set_volume(min(1.0, max(0.0, vol)))
			except Exception:
				pass

	def set_master_volume(self, volume: float) -> None:
		self.master_volume = float(max(0.0, min(1.0, volume)))
		self._apply_volumes()

	def _safe_load_sound(self, path: str) -> Optional[pygame.mixer.Sound]:
		try:
			if os.path.exists(path):
				snd = pygame.mixer.Sound(path)
				snd.set_volume(self.master_volume)
				return snd
		except Exception:
			return None
		return None

	def load(self) -> None:
		try:
			if not pygame.mixer.get_init():
				pygame.mixer.init()
		except Exception:
			return
		base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds")
		self.sfx_jump = self._safe_load_sound(os.path.join(base, "jump.wav"))
		self.sfx_collect = self._safe_load_sound(os.path.join(base, "collect.wav"))
		self.sfx_hit = self._safe_load_sound(os.path.join(base, "hit.wav"))
		self.sfx_portal = self._safe_load_sound(os.path.join(base, "portal.wav"))
		music_path = os.path.join(base, "music.ogg")
		self.music_path = music_path if os.path.exists(music_path) else None
		self._apply_volumes()

	def toggle_mute(self) -> None:
		self.muted = not self.muted
		self._apply_volumes()

	def start_music(self) -> None:
		if self.music_path:
			try:
				pygame.mixer.music.load(self.music_path)
				self._apply_volumes()
				pygame.mixer.music.play(-1)
			except Exception:
				pass

	def stop_music(self) -> None:
		try:
			pygame.mixer.music.stop()
		except Exception:
			pass

	def play_jump(self) -> None:
		if self.muted or not self.sfx_jump:
			return
		try:
			self.sfx_jump.play()
		except Exception:
			pass

	def play_collect(self) -> None:
		if self.muted or not self.sfx_collect:
			return
		try:
			self.sfx_collect.play()
		except Exception:
			pass

	def play_hit(self) -> None:
		if self.muted or not self.sfx_hit:
			return
		try:
			self.sfx_hit.play()
		except Exception:
			pass

	def play_portal(self) -> None:
		if self.muted or not self.sfx_portal:
			return
		try:
			self.sfx_portal.play()
		except Exception:
			pass
