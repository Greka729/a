"""
Модуль для создания звуков слот-машины
Создает простые звуки программно, если файлы звуков недоступны
"""

import pygame
try:
    import numpy as np
except ImportError:
    # Если numpy недоступен, создаем простую альтернативу
    class np:
        @staticmethod
        def random():
            import random
            class Random:
                @staticmethod
                def normal(mean, std, size):
                    return [random.gauss(mean, std) for _ in range(size)]
            return Random()
        
        @staticmethod
        def linspace(start, stop, num):
            step = (stop - start) / (num - 1)
            return [start + i * step for i in range(num)]
        
        @staticmethod
        def sin(x):
            import math
            if isinstance(x, list):
                return [math.sin(val) for val in x]
            return math.sin(x)
        
        @staticmethod
        def exp(x):
            import math
            if isinstance(x, list):
                return [math.exp(val) for val in x]
            return math.exp(x)
        
        @staticmethod
        def pi():
            import math
            return math.pi
        
        @staticmethod
        def array(data):
            return data
        
        @staticmethod
        def int16(data):
            return [int(x) for x in data]

import io
from typing import Dict, Optional


class SlotSoundGenerator:
    """Генератор звуков для слот-машины"""
    
    def __init__(self):
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.sample_rate = 22050
        # Если микшер не инициализирован, не генерируем звуки
        if not pygame.mixer.get_init():
            return
        self._generate_sounds()
    
    def _generate_sounds(self):
        """Создать звуки программно"""
        try:
            # Звук вращения барабанов
            self.sounds['spin'] = self._create_spin_sound()
            
            # Звук выигрыша
            self.sounds['win'] = self._create_win_sound()
            
            # Звук проигрыша
            self.sounds['lose'] = self._create_lose_sound()
            
            # Звук нажатия кнопки
            self.sounds['click'] = self._create_click_sound()
            
        except Exception as e:
            print(f"Ошибка создания звуков: {e}")
            self.sounds = {}
    
    def _create_spin_sound(self) -> pygame.mixer.Sound:
        """Создать звук вращения барабанов"""
        duration = 0.5  # секунды
        samples = int(self.sample_rate * duration)
        
        # Создаем шум с затуханием
        noise = np.random.normal(0, 0.1, samples)
        
        # Добавляем затухание
        envelope = np.linspace(1, 0, samples)
        noise *= envelope
        
        # Добавляем низкочастотный тон
        frequency = 200
        t = np.linspace(0, duration, samples)
        tone = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Комбинируем шум и тон
        sound_data = (noise + tone).astype(np.float32)
        
        # Конвертируем в формат pygame
        sound_array = (sound_data * 32767).astype(np.int16)
        sound_surface = pygame.sndarray.make_sound(sound_array)
        
        return sound_surface
    
    def _create_win_sound(self) -> pygame.mixer.Sound:
        """Создать звук выигрыша"""
        duration = 1.0
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Создаем восходящую мелодию
        frequencies = [523, 659, 784, 1047]  # C5, E5, G5, C6
        sound_data = np.zeros(samples)
        
        for i, freq in enumerate(frequencies):
            start_sample = int(i * samples / len(frequencies))
            end_sample = int((i + 1) * samples / len(frequencies))
            segment_samples = end_sample - start_sample
            segment_t = np.linspace(0, segment_samples / self.sample_rate, segment_samples)
            
            # Создаем тон с затуханием
            tone = 0.5 * np.sin(2 * np.pi * freq * segment_t)
            envelope = np.linspace(1, 0.3, segment_samples)
            tone *= envelope
            
            sound_data[start_sample:end_sample] = tone
        
        # Конвертируем в формат pygame
        sound_array = (sound_data * 32767).astype(np.int16)
        sound_surface = pygame.sndarray.make_sound(sound_array)
        
        return sound_surface
    
    def _create_lose_sound(self) -> pygame.mixer.Sound:
        """Создать звук проигрыша"""
        duration = 0.3
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Создаем нисходящий тон
        frequency = 400
        sound_data = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Добавляем затухание
        envelope = np.linspace(1, 0, samples)
        sound_data *= envelope
        
        # Конвертируем в формат pygame
        sound_array = (sound_data * 32767).astype(np.int16)
        sound_surface = pygame.sndarray.make_sound(sound_array)
        
        return sound_surface
    
    def _create_click_sound(self) -> pygame.mixer.Sound:
        """Создать звук нажатия кнопки"""
        duration = 0.1
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Создаем короткий высокочастотный тон
        frequency = 1000
        sound_data = 0.2 * np.sin(2 * np.pi * frequency * t)
        
        # Добавляем быстрое затухание
        envelope = np.exp(-t * 20)
        sound_data *= envelope
        
        # Конвертируем в формат pygame
        sound_array = (sound_data * 32767).astype(np.int16)
        sound_surface = pygame.sndarray.make_sound(sound_array)
        
        return sound_surface
    
    def play_sound(self, sound_name: str):
        """Воспроизвести звук"""
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"Ошибка воспроизведения звука {sound_name}: {e}")
    
    def get_available_sounds(self) -> list:
        """Получить список доступных звуков"""
        return list(self.sounds.keys())


class SlotSoundManager:
    """Менеджер звуков для слот-машины"""
    
    def __init__(self):
        self.sound_generator: Optional[SlotSoundGenerator] = None
        self.sound_enabled = False
        self.volume = 0.5
        
        # Пытаемся инициализировать микшер. Если не удалось, тихо отключаем звук
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sound_enabled = True
        except Exception as e:
            # Например: WASAPI endpoint not found. В таком случае продолжаем без звука
            print(f"Звук отключен: {e}")
            self.sound_enabled = False
        
        # Создаем генератор звуков только если звук включен
        if self.sound_enabled and pygame.mixer.get_init():
            try:
                self.sound_generator = SlotSoundGenerator()
                pygame.mixer.music.set_volume(self.volume)
            except Exception as e:
                print(f"Звук отключен (ошибка генератора): {e}")
                self.sound_generator = None
                self.sound_enabled = False
    
    def play_spin_sound(self):
        """Воспроизвести звук вращения"""
        if self.sound_enabled and self.sound_generator:
            self.sound_generator.play_sound('spin')
    
    def play_win_sound(self):
        """Воспроизвести звук выигрыша"""
        if self.sound_enabled and self.sound_generator:
            self.sound_generator.play_sound('win')
    
    def play_lose_sound(self):
        """Воспроизвести звук проигрыша"""
        if self.sound_enabled and self.sound_generator:
            self.sound_generator.play_sound('lose')
    
    def play_click_sound(self):
        """Воспроизвести звук нажатия"""
        if self.sound_enabled and self.sound_generator:
            self.sound_generator.play_sound('click')
    
    def toggle_sound(self):
        """Переключить звук"""
        self.sound_enabled = not self.sound_enabled
    
    def set_volume(self, volume: float):
        """Установить громкость (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.volume)
    
    def is_sound_enabled(self) -> bool:
        """Проверить, включен ли звук"""
        return self.sound_enabled
