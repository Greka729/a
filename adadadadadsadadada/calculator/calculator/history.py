from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import List, Tuple


class HistoryManager:
    """CSV-based history storage for calculator expressions and results."""

    def __init__(self, filepath: str | None = None) -> None:
        if filepath is None:
            filepath = os.path.join(os.path.dirname(__file__), "calc_history.csv")
        self.filepath = filepath

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        # Create file with header if missing
        if not os.path.exists(self.filepath):
            with open(self.filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "expression", "result"])  # header

    def append(self, expression: str, result: float) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filepath, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, expression, str(result)])

    def read_last(self, limit: int = 10) -> List[Tuple[str, str, str]]:
        if not os.path.exists(self.filepath):
            return []
        with open(self.filepath, mode="r", newline="", encoding="utf-8") as f:
            reader = list(csv.reader(f))
        if not reader:
            return []
        # skip header if present
        rows = reader[1:] if reader and reader[0] and reader[0][0] == "timestamp" else reader
        tail = rows[-limit:]
        result: List[Tuple[str, str, str]] = []
        for row in tail:
            if len(row) >= 3:
                result.append((row[0], row[1], row[2]))
        return result

    def clear(self) -> None:
        """Clear history file and re-create header."""
        with open(self.filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "expression", "result"])  # header


