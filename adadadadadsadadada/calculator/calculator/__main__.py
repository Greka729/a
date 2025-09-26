import sys
from .cli import run_cli
from .gui import launch_gui


def main() -> None:
    if "--gui" in sys.argv:
        launch_gui()
    else:
        run_cli()


if __name__ == "__main__":
    main()


