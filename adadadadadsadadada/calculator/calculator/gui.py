from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from . import operations
from .history import HistoryManager
from .utils import format_result


class CalculatorGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Калькулятор")
        self.geometry("420x360")
        self.resizable(False, False)

        self.history = HistoryManager()

        self.var_x = tk.StringVar()
        self.var_y = tk.StringVar()
        self.var_base = tk.StringVar()
        self.var_result = tk.StringVar()
        self.var_op = tk.StringVar(value="+")

        self._build()

    def _build(self) -> None:
        padding = {"padx": 8, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="x").grid(row=0, column=0, sticky=tk.W, **padding)
        ttk.Entry(frm, textvariable=self.var_x, width=18).grid(row=0, column=1, **padding)

        ttk.Label(frm, text="y").grid(row=1, column=0, sticky=tk.W, **padding)
        ttk.Entry(frm, textvariable=self.var_y, width=18).grid(row=1, column=1, **padding)

        ttk.Label(frm, text="Основание (для log)").grid(row=2, column=0, sticky=tk.W, **padding)
        ttk.Entry(frm, textvariable=self.var_base, width=18).grid(row=2, column=1, **padding)

        ttk.Label(frm, text="Операция").grid(row=3, column=0, sticky=tk.W, **padding)
        ops = ["+", "-", "*", "/", "^", "%", "sqrt", "log"]
        cmb = ttk.Combobox(frm, textvariable=self.var_op, values=ops, width=15, state="readonly")
        cmb.grid(row=3, column=1, **padding)
        cmb.bind("<<ComboboxSelected>>", lambda e: self._update_fields())

        ttk.Button(frm, text="Рассчитать", command=self.on_calculate).grid(row=4, column=0, **padding)
        ttk.Button(frm, text="История", command=self.on_show_history_window).grid(row=4, column=1, **padding)

        ttk.Label(frm, text="Результат").grid(row=5, column=0, sticky=tk.W, **padding)
        res_entry = ttk.Entry(frm, textvariable=self.var_result, width=28, state="readonly")
        res_entry.grid(row=5, column=1, **padding)
        ttk.Button(frm, text="Копировать", command=self.on_copy_result).grid(row=5, column=2, **padding)

        # Hotkeys
        self.bind("<Return>", lambda e: self.on_calculate())
        self.bind("<Control-c>", lambda e: self.on_copy_result())
        self.bind("<Escape>", lambda e: self.quit())

        self._update_fields()

    def parse_float(self, value: str) -> Optional[float]:
        value = value.strip()
        if value == "":
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def on_calculate(self) -> None:
        op = self.var_op.get()
        x = self.parse_float(self.var_x.get())
        y = self.parse_float(self.var_y.get())

        try:
            if op == "sqrt":
                if x is None:
                    raise ValueError("Введите x")
                result = operations.sqrt(x)
                expr = f"sqrt({x})"
            elif op == "%":
                if x is None or y is None:
                    raise ValueError("Введите x и p (в поле y)")
                result = operations.percent(x, y)
                expr = f"{y}% от {x}"
            elif op == "log":
                if x is None:
                    raise ValueError("Введите x")
                base_str = self.var_base.get().strip()
                if base_str == "":
                    result = operations.log(x)
                    expr = f"log_e({x})"
                else:
                    b = self.parse_float(base_str)
                    if b is None:
                        raise ValueError("Некорректное основание логарифма")
                    result = operations.log(x, b)
                    expr = f"log_{b}({x})"
            else:
                if x is None or y is None:
                    raise ValueError("Введите x и y")
                if op == "+":
                    result = operations.add(x, y)
                elif op == "-":
                    result = operations.subtract(x, y)
                elif op == "*":
                    result = operations.multiply(x, y)
                elif op == "/":
                    result = operations.divide(x, y)
                elif op == "^":
                    result = operations.power(x, y)
                else:
                    raise ValueError("Неизвестная операция")
                expr = f"{x} {op} {y}"

            self.var_result.set(format_result(result))
            self.history.append(expr, result)
        except Exception as ex:
            messagebox.showerror("Ошибка", str(ex))

    def on_show_history_window(self) -> None:
        win = tk.Toplevel(self)
        win.title("История")
        win.geometry("520x360")
        win.resizable(False, False)

        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True)

        text = tk.Text(frame, wrap="none", height=16, width=64)
        text.grid(row=0, column=0, columnspan=3, padx=8, pady=8, sticky="nsew")

        def refresh() -> None:
            rows = self.history.read_last(200)
            text.delete("1.0", tk.END)
            if not rows:
                text.insert(tk.END, "История пуста\n")
                return
            for t, e, r in rows:
                text.insert(tk.END, f"{t} | {e} = {r}\n")

        def clear() -> None:
            if messagebox.askyesno("Подтверждение", "Очистить историю?"):
                self.history.clear()
                refresh()

        ttk.Button(frame, text="Обновить", command=refresh).grid(row=1, column=0, padx=8, pady=8)
        ttk.Button(frame, text="Очистить", command=clear).grid(row=1, column=1, padx=8, pady=8)
        ttk.Button(frame, text="Закрыть", command=win.destroy).grid(row=1, column=2, padx=8, pady=8)

        refresh()

    def on_copy_result(self) -> None:
        value = self.var_result.get()
        if not value:
            return
        self.clipboard_clear()
        self.clipboard_append(value)
        self.update()  # now it stays on the clipboard after the window is closed

    def _update_fields(self) -> None:
        op = self.var_op.get()
        # Enable/disable y and base fields depending on operation
        # x always enabled
        y_widgets = [w for w in self.children.values() if isinstance(w, ttk.Entry)]
        # Simplified control using state on known variables
        # Enable all by default
        # For simplicity, rely on labels as guidance; we won't fully disable
        if op == "sqrt":
            self.var_y.set("")
        # base is only for log; leave value otherwise


def launch_gui() -> None:
    app = CalculatorGUI()
    app.mainloop()


