import pygame

from src.game.game import Game


def main() -> None:
	pygame.init()
	try:
		game = Game()
		game.run()
	finally:
		pygame.quit()


if __name__ == "__main__":
	main()
