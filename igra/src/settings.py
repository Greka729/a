WIDTH = 960
HEIGHT = 540
FPS = 60
TITLE = "SkyRun"
BG_COLOR = (20, 24, 28)

# Player
PLAYER_SPEED = 220.0
PLAYER_JUMP_VELOCITY = -560.0
GRAVITY = 1200.0

# Colors
COLOR_PLAYER = (80, 200, 255)
COLOR_PLATFORM = (70, 160, 90)
COLOR_TEXT = (240, 240, 240)
COLOR_COLLECTIBLE = (255, 210, 0)
COLOR_PORTAL = (180, 100, 255)
COLOR_ENEMY = (220, 70, 70)

# Level 1 layout (legacy constants kept for compatibility)
LEVEL_PLATFORMS = [
	(0, HEIGHT - 40, WIDTH, 40),
	(120, 420, 180, 20),
	(360, 360, 160, 20),
	(620, 320, 180, 20),
	(820, 260, 100, 20),
	(40, 300, 120, 20),
]

COLLECTIBLES = [
	(150, 380, 18, 18),
	(400, 320, 18, 18),
	(650, 280, 18, 18),
]

ENEMIES = [
	# (x, y, w, h, patrol_min_x, patrol_max_x, speed)
	(360, 332, 26, 28, 360, 520, 90.0),
	(620, 292, 26, 28, 620, 800, 110.0),
]

SPAWN_POINT = (40, HEIGHT - 80)
PORTAL_RECT = (WIDTH - 60, 200, 30, 50)

# Multi-level definition
LEVELS = [
	{
		"platforms": LEVEL_PLATFORMS,
		"collectibles": COLLECTIBLES,
		"enemies": ENEMIES,
		"spawn": SPAWN_POINT,
		"portal": PORTAL_RECT,
	},
	{
		# Tuned Level 2: diagonal ascent left->right, some longer patrols
		"platforms": [
			(0, HEIGHT - 40, WIDTH, 40),
			(120, 470, 140, 20),
			(300, 430, 140, 20),
			(480, 390, 140, 20),
			(660, 350, 140, 20),
			(820, 310, 110, 20),
			(220, 280, 140, 20),
			(420, 240, 120, 20),
			(620, 200, 120, 20),
		],
		"collectibles": [
			(125, 440, 18, 18),
			(305, 400, 18, 18),
			(485, 360, 18, 18),
			(665, 320, 18, 18),
			(225, 250, 18, 18),
			(625, 170, 18, 18),
		],
		"enemies": [
			# ground patrol
			(140, HEIGHT - 68, 26, 28, 120, 360, 105.0),
			# mid platforms
			(300, 402, 26, 28, 300, 440, 130.0),
			(660, 322, 26, 28, 660, 800, 145.0),
			# upper platform guardian
			(420, 212, 26, 28, 420, 540, 120.0),
		],
		"spawn": (40, HEIGHT - 80),
		"portal": (WIDTH - 80, 150, 34, 54),
	},
]
