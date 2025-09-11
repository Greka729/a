import logging
import sys

_DEF_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s"


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=_DEF_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


