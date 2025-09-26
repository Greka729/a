import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from wikipedia.exceptions import WikipediaException

from wikipedia_client import WikipediaClient
from cache import LRUCache


class WikipediaGUI(tk.Tk):
    def __init__(self, client: WikipediaClient, cache: LRUCache):
        super().__init__()
        self.title("Wikipedia Viewer")
        self.geometry("900x700")
        self.client = client
        self.cache = cache
        self.current_url: Optional[str] = None
        self._build_widgets()

    def _build_widgets(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text="Language:").pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value=self.client.language_code)
        self.lang_entry = ttk.Entry(top, textvariable=self.lang_var, width=6)
        self.lang_entry.pack(side=tk.LEFT, padx=(4, 12))

        self.btn_lang = ttk.Button(top, text="Set", command=self.on_set_language)
        self.btn_lang.pack(side=tk.LEFT)

        self.btn_random = ttk.Button(top, text="Random", command=self.on_random)
        self.btn_random.pack(side=tk.LEFT, padx=(12, 0))

        ttk.Label(top, text="Search:").pack(side=tk.LEFT, padx=(12, 0))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(top, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=(4, 4))
        self.btn_search = ttk.Button(top, text="Go", command=self.on_search)
        self.btn_search.pack(side=tk.LEFT)

        middle = ttk.Frame(self)
        middle.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        left = ttk.Frame(middle)
        left.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left, text="Results / Cache").pack(anchor=tk.W)
        self.listbox = tk.Listbox(left, width=40)
        self.listbox.pack(fill=tk.Y, expand=False)
        self.listbox.bind("<<ListboxSelect>>", self.on_list_select)

        right = ttk.Frame(middle)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        self.title_var = tk.StringVar(value="Title")
        self.lbl_title = ttk.Label(right, textvariable=self.title_var, font=("Segoe UI", 14, "bold"))
        self.lbl_title.pack(anchor=tk.W)

        self.url_var = tk.StringVar(value="URL")
        self.lbl_url = ttk.Label(right, textvariable=self.url_var, foreground="#1a73e8")
        self.lbl_url.pack(anchor=tk.W, pady=(0, 6))

        self.txt = tk.Text(right, wrap=tk.WORD)
        self.txt.pack(fill=tk.BOTH, expand=True)

        bottom = ttk.Frame(self)
        bottom.pack(fill=tk.X, padx=8, pady=(0, 8))

        ttk.Label(bottom, text="Max chars:").pack(side=tk.LEFT)
        self.max_chars_var = tk.StringVar()
        ttk.Entry(bottom, textvariable=self.max_chars_var, width=8).pack(side=tk.LEFT, padx=(4, 12))

        ttk.Label(bottom, text="Max paragraphs:").pack(side=tk.LEFT)
        self.max_pars_var = tk.StringVar()
        ttk.Entry(bottom, textvariable=self.max_pars_var, width=8).pack(side=tk.LEFT, padx=(4, 12))

        self.btn_cache = ttk.Button(bottom, text="Show Cache", command=self.on_show_cache)
        self.btn_cache.pack(side=tk.RIGHT)

        self.btn_open = ttk.Button(bottom, text="Open in Browser", command=self.on_open_browser)
        self.btn_open.pack(side=tk.RIGHT, padx=(8, 0))

    def on_set_language(self) -> None:
        code = self.lang_var.get().strip()
        if not code:
            return
        try:
            self.client.set_language(code)
            messagebox.showinfo("Language", f"Language set to {code}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set language: {e}")

    def on_random(self) -> None:
        self._run_async(self._load_random)

    def _load_random(self) -> None:
        try:
            page = self.client.get_random_page()
            self.cache.put(page.title, (page.summary, page.url, page.content or ""))
            self._display_page(page.title, page.url, page.summary, page.content)
        except WikipediaException as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected: {e}")

    def on_search(self) -> None:
        query = self.search_var.get().strip()
        if not query:
            return
        self._run_async(self._load_search, query)

    def _load_search(self, query: str) -> None:
        try:
            results = self.client.search(query, max_results=20)
            self._set_results(results)
        except WikipediaException as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected: {e}")

    def _set_results(self, titles: list[str]) -> None:
        self.listbox.delete(0, tk.END)
        for t in titles:
            self.listbox.insert(tk.END, t)

    def on_list_select(self, _event=None) -> None:
        sel = self.listbox.curselection()
        if not sel:
            return
        title = self.listbox.get(sel[0])
        self._run_async(self._load_page_by_title, title)

    def _load_page_by_title(self, title: str) -> None:
        try:
            page = self.client.get_page(title)
            self.cache.put(page.title, (page.summary, page.url, page.content or ""))
            self._display_page(page.title, page.url, page.summary, page.content)
        except WikipediaException as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected: {e}")

    def on_show_cache(self) -> None:
        titles = self.cache.keys()
        self._set_results(titles)

    def _display_page(self, title: str, url: str, summary: Optional[str], content: Optional[str]) -> None:
        self.title_var.set(title or "")
        self.url_var.set(url or "")
        self.current_url = url or None
        self.txt.delete("1.0", tk.END)

        if summary:
            self.txt.insert(tk.END, "Summary:\n")
            self.txt.insert(tk.END, summary + "\n\n")
        if content:
            max_chars = self._parse_int(self.max_chars_var.get())
            max_pars = self._parse_int(self.max_pars_var.get())
            limited = WikipediaClient.limit_text(content, max_chars=max_chars, max_paragraphs=max_pars)
            self.txt.insert(tk.END, limited)

    def on_open_browser(self) -> None:
        if self.current_url:
            try:
                webbrowser.open(self.current_url)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open browser: {e}")

    def _parse_int(self, s: str) -> Optional[int]:
        try:
            s = s.strip()
            return int(s) if s else None
        except Exception:
            return None

    def _run_async(self, fn, *args):
        def runner():
            fn(*args)
        threading.Thread(target=runner, daemon=True).start()


