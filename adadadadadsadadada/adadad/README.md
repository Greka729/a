Snake Game (Pygame)

Requirements
- Python 3.8+
- Pygame (installed via requirements.txt)

Setup
```bash
pip install -r requirements.txt
```

Run
```bash
python snake.py
```

Controls
- Arrow Keys: Move snake
- 1 / 2 / 3: Choose difficulty (on start menu)
- Enter: Start game (from menu) / Restart (on game over)
- R: Restart (on game over)
- Esc: Quit

Features
- Classic snake movement on a grid (800x600, cell 20x20)
- Food spawns on free cells
- Growth and score on eating
- Collision with walls or self -> game over
- Smooth animation with FPS control
- Difficulty levels (Slow/Normal/Fast)
- Optional sounds (place files in assets/):
  - assets/eat.wav
  - assets/game_over.wav
- High score persistence in highscore.txt

Notes
- Sounds are optional; the game runs without them.
- To reset high score, delete highscore.txt.

