# Console Calculator (Python)

Simple, modular console calculator supporting basic and extended operations, input validation, history, and tests. Built for Python 3.8+ with an option to extend to GUI (Tkinter).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m calculator  # or: python run.py
```

### GUI mode (Tkinter)

```bash
python -m calculator --gui  # or: python run.py --gui
```

Tips:
- Enter to calculate
- Ctrl+C to copy result
- Esc to exit

### Clear history

- CLI: choose `c` and confirm.
- GUI: press "Очистить историю" and confirm.

## Features

- Basic: add, subtract, multiply, divide
- Extra: power, percent, sqrt, logarithm
- Input validation and helpful error messages
- Division-by-zero protection
- Repeat calculations without restarting
- Optional: history persistence to a file
  - Clear history from CLI (option `c`) or GUI (button)
  - GUI conveniences: copy result (Ctrl+C), history window with refresh/clear

## Project structure

```
calculator/
  __init__.py
  __main__.py
  cli.py
  operations.py
  history.py
tests/
  test_operations.py
README.md
requirements.txt
```

## Run tests

```bash
python -m pytest -q
```

## Extending to GUI

- Wrap calls from `calculator.operations` and `calculator.cli` into Tkinter widgets.
- Keep business logic in `operations.py` to reuse across UI layers.

## License

MIT


