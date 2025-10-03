import os
import sys
import platform
import subprocess
import shutil
import threading
import json
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
try:
    from PIL import Image, ImageTk  # type: ignore
except Exception:
    Image = None  # type: ignore
    ImageTk = None  # type: ignore


class FileManagerApp:

	def __init__(self, master: tk.Tk) -> None:
		self.master = master
		self.master.title("Проводник")
		self.master.geometry("1000x600")

		# Settings
		self.settings_path = os.path.join(os.path.expanduser("~"), ".provodnik_settings.json")
		self._last_entry_count = 0

		# Theming
		self.current_theme = "light"  # light | dark
		self.style = ttk.Style(self.master)
		# Defaults (can be overridden by settings)
		self.show_hidden = False
		self.sort_by = "name"
		self.sort_reverse = False
		self.view_mode = tk.StringVar(value="details")
		self._load_settings_safe()
		self._init_style()

		self.current_path = self._get_initial_path()
		# Icons cache
		self.icons: dict[str, tk.PhotoImage] = {}
		self.path_history: list[str] = [self.current_path]
		self.back_stack: list[str] = []
		self.forward_stack: list[str] = []

		self._build_ui()
		self._populate_listing(self.current_path)
		try:
			self.master.protocol("WM_DELETE_WINDOW", self._on_close)
		except Exception:
			pass

	def _get_initial_path(self) -> str:
		try:
			return os.path.expanduser("~")
		except Exception:
			return os.getcwd()

	def _build_ui(self) -> None:
		toolbar = ttk.Frame(self.master)
		toolbar.pack(fill=tk.X, padx=6, pady=6)

		# Navigation buttons
		self.back_btn = ttk.Button(toolbar, text="←", width=3, command=self._on_back)
		self.back_btn.pack(side=tk.LEFT)
		self.forward_btn = ttk.Button(toolbar, text="→", width=3, command=self._on_forward)
		self.forward_btn.pack(side=tk.LEFT, padx=(4,0))
		up_btn = ttk.Button(toolbar, text="Up", command=self._on_up)
		up_btn.pack(side=tk.LEFT, padx=(6, 0))

		self.path_var = tk.StringVar(value=self.current_path)
		self.path_combo = ttk.Combobox(toolbar, textvariable=self.path_var, state="normal")
		self.path_combo["values"] = tuple(self.path_history)
		self.path_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
		self.path_combo.bind("<Return>", self._on_go)
		self.path_combo.bind("<<ComboboxSelected>>", self._on_go)
		self.path_combo.bind("<KeyRelease>", self._on_path_type)

		go_btn = ttk.Button(toolbar, text="Go", command=self._on_go)
		go_btn.pack(side=tk.LEFT, padx=(6, 0))

		refresh_btn = ttk.Button(toolbar, text="Refresh", command=self._on_refresh)
		refresh_btn.pack(side=tk.LEFT, padx=(6, 0))

		# Quick focus path hotkey
		self.master.bind("<Alt-d>", lambda e: self._focus_path())

		# Theme toggle
		self.theme_btn = ttk.Button(toolbar, text="Dark", command=self._toggle_theme)
		self.theme_btn.pack(side=tk.RIGHT)

		# Windows drive selector
		if platform.system() == "Windows":
			ttk.Label(toolbar, text="  Drive:").pack(side=tk.LEFT, padx=(12,0))
			self.drive_var = tk.StringVar()
			self.drive_combo = ttk.Combobox(toolbar, textvariable=self.drive_var, width=6, state="readonly")
			self.drive_combo.pack(side=tk.LEFT, padx=(4,0))
			self._populate_drives()
			self.drive_combo.bind("<<ComboboxSelected>>", self._on_drive_change)

		# Breadcrumb bar
		self.breadcrumb = ttk.Frame(self.master)
		self.breadcrumb.pack(fill=tk.X, padx=6, pady=(0,6))
		self._rebuild_breadcrumb()


		# File operation buttons
		ops_bar = ttk.Frame(self.master)
		ops_bar.pack(fill=tk.X, padx=6, pady=(0,6))
		new_folder_btn = ttk.Button(ops_bar, text="New Folder", command=self._create_folder)
		new_folder_btn.pack(side=tk.LEFT)
		new_file_btn = ttk.Button(ops_bar, text="New File", command=self._create_file)
		new_file_btn.pack(side=tk.LEFT, padx=(6,0))
		rename_btn = ttk.Button(ops_bar, text="Rename", command=self._rename_selected)
		rename_btn.pack(side=tk.LEFT, padx=(6,0))
		delete_btn = ttk.Button(ops_bar, text="Delete", command=self._delete_selected)
		delete_btn.pack(side=tk.LEFT, padx=(6,0))
		copy_btn = ttk.Button(ops_bar, text="Copy To...", command=self._copy_selected_to)
		copy_btn.pack(side=tk.LEFT, padx=(6,0))
		move_btn = ttk.Button(ops_bar, text="Move To...", command=self._move_selected_to)
		move_btn.pack(side=tk.LEFT, padx=(6,0))
		self.hidden_var = tk.BooleanVar(value=self.show_hidden)
		show_hidden_cb = ttk.Checkbutton(ops_bar, text="Show hidden", variable=self.hidden_var, command=self._toggle_hidden)
		show_hidden_cb.pack(side=tk.RIGHT)

		# Main split: sidebar and content
		main_split = ttk.Panedwindow(self.master, orient=tk.HORIZONTAL)
		main_split.pack(fill=tk.BOTH, expand=True)

		# Sidebar left
		self.sidebar = ttk.Notebook(main_split)
		fav_tab = ttk.Frame(self.sidebar)
		dev_tab = ttk.Frame(self.sidebar)
		tree_tab = ttk.Frame(self.sidebar)
		self.sidebar.add(fav_tab, text="Favorites")
		self.sidebar.add(dev_tab, text="Devices")
		self.sidebar.add(tree_tab, text="Tree")
		main_split.add(self.sidebar, weight=1)

		# Fill Favorites
		self.fav_list = tk.Listbox(fav_tab, activestyle="dotbox")
		self.fav_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
		self._populate_favorites()
		self.fav_list.bind("<<ListboxSelect>>", self._on_favorite_select)

		# Fill Devices
		self.dev_list = tk.Listbox(dev_tab, activestyle="dotbox")
		self.dev_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
		self._populate_devices()
		self.dev_list.bind("<<ListboxSelect>>", self._on_device_select)

		# Filesystem tree
		columns_side = ("dummy",)
		self.fs_tree = ttk.Treeview(tree_tab, columns=columns_side, show="tree")
		self.fs_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
		self.fs_tree.bind("<<TreeviewOpen>>", self._on_fs_tree_open)
		self.fs_tree.bind("<Double-1>", self._on_fs_tree_double)
		self._init_fs_tree()

		# Right content split: results and preview
		right_split = ttk.Panedwindow(main_split, orient=tk.VERTICAL)
		main_split.add(right_split, weight=4)

		# Search bar
		search_bar = ttk.Frame(right_split)
		name_lbl = ttk.Label(search_bar, text="Search:")
		name_lbl.pack(side=tk.LEFT, padx=(6,0))
		self.search_var = tk.StringVar()
		self.search_entry = ttk.Entry(search_bar, textvariable=self.search_var)
		self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4,0))
		self.search_entry.bind("<Return>", self._start_search)
		self.filter_var = tk.StringVar(value="All")
		self.filter_combo = ttk.Combobox(search_bar, textvariable=self.filter_var, state="readonly", width=14,
			values=("All","Images","Documents","Archives","Audio","Video","Code"))
		self.filter_combo.pack(side=tk.LEFT, padx=6)
		self.search_btn = ttk.Button(search_bar, text="Find", command=self._start_search)
		self.search_btn.pack(side=tk.LEFT)
		self.stop_btn = ttk.Button(search_bar, text="Stop", command=self._stop_search)
		self.stop_btn.pack(side=tk.LEFT, padx=(6,0))
		right_split.add(search_bar, weight=0)

		# Tree area with themed scrollbars in right content
		tree_container = ttk.Frame(right_split)
		tree_container.columnconfigure(0, weight=1)
		tree_container.rowconfigure(0, weight=1)

		# View mode controls
		view_bar = ttk.Frame(tree_container)
		view_bar.grid(row=0, column=0, sticky="ew", columnspan=2)
		for label, mode in (("Details","details"),("Icons","icons"),("Tiles","tiles")):
			b = ttk.Radiobutton(view_bar, text=label, value=mode, variable=self.view_mode, command=self._on_view_mode_change)
			b.pack(side=tk.LEFT, padx=(0,6))

		columns = ("type", "size", "modified")
		self.tree = ttk.Treeview(tree_container, columns=columns, show="tree headings", selectmode="extended")
		self.tree.heading("#0", text="Name", command=lambda: self._on_sort("name"))
		self.tree.heading("type", text="Type", command=lambda: self._on_sort("type"))
		self.tree.heading("size", text="Size", command=lambda: self._on_sort("size"))
		self.tree.heading("modified", text="Modified", command=lambda: self._on_sort("modified"))
		self.tree.column("#0", width=420, anchor=tk.W)
		self.tree.column("type", width=120, anchor=tk.W)
		self.tree.column("size", width=100, anchor=tk.E)
		self.tree.column("modified", width=180, anchor=tk.W)
		self.tree.grid(row=1, column=0, sticky="nsew")

		vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
		hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview, style="Horizontal.TScrollbar")
		self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
		vsb.grid(row=1, column=1, sticky="ns")
		hsb.grid(row=2, column=0, sticky="ew")
		right_split.add(tree_container, weight=4)

		# Preview pane
		preview = ttk.Frame(right_split)
		preview.columnconfigure(0, weight=1)
		preview.rowconfigure(0, weight=1)
		self.preview_image = ttk.Label(preview)
		self.preview_image.grid(row=0, column=0, sticky="nw", padx=8, pady=6)
		self.preview_text = tk.Text(preview, height=8, wrap="word")
		self.preview_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,8))
		self.preview_text.configure(state="disabled")
		right_split.add(preview, weight=1)

		self.tree.bind("<Double-1>", self._on_double_click)
		self.tree.bind("<Return>", self._on_enter)
		self.tree.bind("<Button-3>", self._show_context_menu)
		self.tree.bind("<<TreeviewSelect>>", self._on_select_change)
		self.master.bind("<Alt-Left>", lambda e: self._on_back())
		self.master.bind("<Alt-Right>", lambda e: self._on_forward())
		self.master.bind("<F2>", lambda e: self._rename_selected())
		self.master.bind("<Delete>", lambda e: self._delete_selected())
		self.master.bind("<F5>", lambda e: self._on_refresh())
		self.master.bind("<Control-h>", lambda e: self._toggle_hidden_hotkey())
		self.master.bind("<Control-H>", lambda e: self._toggle_hidden_hotkey())
		self.master.bind("<Control-F>", lambda e: self.search_entry.focus_set())
		self.master.bind("<Control-Shift-C>", lambda e: self._copy_path_to_clipboard())

		# Row tags for zebra striping
		self.tree.tag_configure('odd', background=self._alt_row_color())

		status_bar = ttk.Frame(self.master)
		status_bar.pack(fill=tk.X, side=tk.BOTTOM)
		self.status_var = tk.StringVar(value="")
		self.status_label = ttk.Label(status_bar, textvariable=self.status_var, anchor=tk.W)
		self.status_label.pack(fill=tk.X, padx=6, pady=3)

		# Context menu
		self._build_context_menu()

	def _on_close(self) -> None:
		try:
			self._save_settings_safe()
		except Exception:
			pass
		self.master.destroy()

	def _settings_default(self) -> dict:
		return {
			"theme": self.current_theme,
			"geometry": self.master.winfo_geometry(),
			"last_path": self.current_path,
			"view_mode": self.view_mode.get() if isinstance(self.view_mode, tk.StringVar) else "details",
			"show_hidden": bool(self.show_hidden),
			"sort_by": self.sort_by,
			"sort_reverse": self.sort_reverse,
		}

	def _load_settings_safe(self) -> None:
		try:
			if os.path.exists(self.settings_path):
				with open(self.settings_path, "r", encoding="utf-8") as f:
					cfg = json.load(f)
				# Apply theme early
				if isinstance(cfg.get("theme"), str):
					self.current_theme = cfg.get("theme") or self.current_theme
				# Apply geometry early
				if isinstance(cfg.get("geometry"), str):
					try:
						self.master.geometry(cfg["geometry"])  # may raise on invalid
					except Exception:
						pass
				# Apply other settings
				if isinstance(cfg.get("view_mode"), str):
					try:
						self.view_mode.set(cfg["view_mode"])  # type: ignore[attr-defined]
					except Exception:
						pass
				if isinstance(cfg.get("show_hidden"), bool):
					self.show_hidden = cfg["show_hidden"]
				if isinstance(cfg.get("sort_by"), str):
					self.sort_by = cfg["sort_by"]
				if isinstance(cfg.get("sort_reverse"), bool):
					self.sort_reverse = cfg["sort_reverse"]
				if isinstance(cfg.get("last_path"), str) and os.path.isdir(cfg["last_path"]):
					self.current_path = cfg["last_path"]
		except Exception:
			pass

	def _save_settings_safe(self) -> None:
		try:
			cfg = self._settings_default()
			with open(self.settings_path, "w", encoding="utf-8") as f:
				json.dump(cfg, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def _get_selected_names(self) -> list:
		selected = self.tree.selection()
		return [self.tree.item(item_id, "text") for item_id in selected]

	def _create_folder(self) -> None:
		name = simpledialog.askstring("New Folder", "Folder name:", parent=self.master)
		if not name:
			return
			
		new_path = os.path.join(self.current_path, name)
		try:
			os.makedirs(new_path, exist_ok=False)
			self._populate_listing(self.current_path)
		except FileExistsError:
			messagebox.showerror("Create Folder", "A file or folder with that name already exists.")
		except Exception as exc:
			messagebox.showerror("Create Folder", str(exc))

	def _create_file(self) -> None:
		name = simpledialog.askstring("New File", "File name:", parent=self.master)
		if not name:
			return
		new_path = os.path.join(self.current_path, name)
		try:
			if os.path.exists(new_path):
				raise FileExistsError("A file or folder with that name already exists.")
			with open(new_path, "w", encoding="utf-8"):
				pass
			self._populate_listing(self.current_path)
		except Exception as exc:
			messagebox.showerror("Create File", str(exc))

	def _rename_selected(self) -> None:
		names = self._get_selected_names()
		if len(names) != 1:
			messagebox.showinfo("Rename", "Please select exactly one item to rename.")
			return
		old_name = names[0]
		new_name = simpledialog.askstring("Rename", f"New name for '{old_name}':", initialvalue=old_name, parent=self.master)
		if not new_name or new_name == old_name:
			return
		old_path = os.path.join(self.current_path, old_name)
		new_path = os.path.join(self.current_path, new_name)
		try:
			os.replace(old_path, new_path)
			self._populate_listing(self.current_path)
		except Exception as exc:
			messagebox.showerror("Rename", str(exc))

	def _delete_selected(self) -> None:
		names = self._get_selected_names()
		if not names:
			return
		confirm = messagebox.askyesno("Delete", f"Delete {len(names)} item(s)? This cannot be undone.")
		if not confirm:
			return
		errors = []
		for name in names:
			path = os.path.join(self.current_path, name)
			try:
				if os.path.isdir(path) and not os.path.islink(path):
					shutil.rmtree(path)
				else:
					os.remove(path)
			except Exception as exc:
				errors.append(f"{name}: {exc}")
		self._populate_listing(self.current_path)
		if errors:
			messagebox.showerror("Delete", "\n".join(errors))

	def _copy_selected_to(self) -> None:
		dest_dir = self._ask_directory(title="Copy to", initialdir=self.current_path)
		if not dest_dir:
			return
		names = self._get_selected_names()
		if not names:
			return
		errors = []
		for name in names:
			src = os.path.join(self.current_path, name)
			dst = os.path.join(dest_dir, name)
			try:
				if os.path.isdir(src) and not os.path.islink(src):
					if os.path.exists(dst):
						shutil.rmtree(dst)
					shutil.copytree(src, dst)
				else:
					shutil.copy2(src, dst)
			except Exception as exc:
				errors.append(f"{name}: {exc}")
		if errors:
			messagebox.showerror("Copy To", "\n".join(errors))

	def _move_selected_to(self) -> None:
		dest_dir = self._ask_directory(title="Move to", initialdir=self.current_path)
		if not dest_dir:
			return
		names = self._get_selected_names()
		if not names:
			return
		errors = []
		for name in names:
			src = os.path.join(self.current_path, name)
			dst = os.path.join(dest_dir, name)
			try:
				shutil.move(src, dst)
			except Exception as exc:
				errors.append(f"{name}: {exc}")
		self._populate_listing(self.current_path)
		if errors:
			messagebox.showerror("Move To", "\n".join(errors))

	def _on_go(self, event=None) -> None:
		path = self.path_var.get().strip() or self.current_path
		self._change_directory(path)
		self._update_path_history(self.current_path)

	def _on_up(self) -> None:
		parent = os.path.dirname(self.current_path.rstrip(os.sep)) or self.current_path
		if parent and parent != self.current_path:
			self._navigate_to(parent)

	def _on_refresh(self) -> None:
		self._populate_listing(self.current_path)

	def _on_double_click(self, event=None) -> None:
		item_id = self.tree.focus()
		if not item_id:
			return
		item_path = self.tree.item(item_id, "text")
		full_path = os.path.join(self.current_path, item_path)
		if os.path.isdir(full_path):
			self._navigate_to(full_path)
		else:
			self._open_with_system(full_path)
		self._update_preview()

	def _on_enter(self, event=None) -> None:
		self._on_double_click()

	def _change_directory(self, path: str) -> None:
		try:
			if not os.path.exists(path):
				raise FileNotFoundError(f"Path does not exist: {path}")
			if not os.path.isdir(path):
				raise NotADirectoryError(f"Not a directory: {path}")
			self.current_path = os.path.abspath(path)
			self.path_var.set(self.current_path)
			self._rebuild_breadcrumb()
			self._populate_listing(self.current_path)
			self._update_nav_buttons()
			self._update_path_history(self.current_path)
		except Exception as exc:
			messagebox.showerror("Error", str(exc))

	def _navigate_to(self, path: str) -> None:
		# Push current to back, clear forward, then change
		if os.path.abspath(path) == os.path.abspath(self.current_path):
			return
		self.back_stack.append(self.current_path)
		self.forward_stack.clear()
		self._change_directory(path)

	def _on_back(self) -> None:
		if not self.back_stack:
			return
		prev_path = self.back_stack.pop()
		self.forward_stack.append(self.current_path)
		self._change_directory(prev_path)

	def _on_forward(self) -> None:
		if not self.forward_stack:
			return
		next_path = self.forward_stack.pop()
		self.back_stack.append(self.current_path)
		self._change_directory(next_path)

	def _update_nav_buttons(self) -> None:
		try:
			self.back_btn.state(["!disabled"] if self.back_stack else ["disabled"])
			self.forward_btn.state(["!disabled"] if self.forward_stack else ["disabled"])
		except Exception:
			pass

	def _populate_listing(self, path: str) -> None:
		for item in self.tree.get_children():
			self.tree.delete(item)

		try:
			entries = []
			with os.scandir(path) as it:
				for entry in it:
					try:
						info = entry.stat()
						is_hidden = entry.name.startswith('.')
						if not self.show_hidden and is_hidden:
							continue
						entries.append((
							entry.name,
							"Folder" if entry.is_dir() else self._get_file_type(entry.name),
							info.st_size if entry.is_file() else None,
							datetime.fromtimestamp(info.st_mtime)
						))
					except PermissionError:
						continue

			# Sorting
			if self.sort_by == "name":
				entries.sort(key=lambda e: (e[1] != "Folder", e[0].lower()), reverse=self.sort_reverse)
			elif self.sort_by == "type":
				entries.sort(key=lambda e: (e[1] != "Folder", e[1], e[0].lower()), reverse=self.sort_reverse)
			elif self.sort_by == "size":
				entries.sort(key=lambda e: (e[1] != "Folder", (e[2] is None, e[2] or 0), e[0].lower()), reverse=self.sort_reverse)
			elif self.sort_by == "modified":
				entries.sort(key=lambda e: (e[1] != "Folder", e[3], e[0].lower()), reverse=self.sort_reverse)

			for idx, (name, type_name, size_bytes, mtime) in enumerate(entries):
				size_display = self._format_size(size_bytes) if size_bytes is not None else ""
				mtime_display = mtime.strftime("%Y-%m-%d %H:%M") if mtime else ""
				try:
					icon = self._get_icon(name, is_dir=(type_name == "Folder"))
				except Exception:
					icon = None
				if self.view_mode.get() == "details":
					self.tree.insert("", tk.END, text=name, values=(type_name, size_display, mtime_display), image=icon, tags=("odd",) if idx % 2 else ())
				elif self.view_mode.get() == "icons":
					self.tree.insert("", tk.END, text=name, values=("", "", ""), image=icon, tags=("odd",) if idx % 2 else ())
				else:  # tiles
					self.tree.insert("", tk.END, text=f"{name}", values=(type_name, size_display, ""), image=icon, tags=("odd",) if idx % 2 else ())

			self._last_entry_count = len(entries)
			self._set_status(self._status_text(len(entries)))
			self._update_preview()
		except PermissionError:
			self._set_status("Permission denied")
		except FileNotFoundError:
			self._set_status("Directory not found")
		except Exception as exc:
			self._set_status(f"Error: {exc}")

	def _get_file_type(self, name: str) -> str:
		_, ext = os.path.splitext(name)
		return ext[1:].upper() + " File" if ext else "File"

	def _populate_favorites(self) -> None:
		self.fav_list.delete(0, tk.END)
		candidates = [
			(os.path.expanduser("~"), "Home"),
			(os.path.join(os.path.expanduser("~"), "Desktop"), "Desktop"),
			(os.path.join(os.path.expanduser("~"), "Documents"), "Documents"),
			(os.path.join(os.path.expanduser("~"), "Downloads"), "Downloads"),
		]
		for path, label in candidates:
			if os.path.exists(path):
				self.fav_list.insert(tk.END, f"{label}::{path}")

	def _on_favorite_select(self, event=None) -> None:
		try:
			idx = self.fav_list.curselection()
			if not idx:
				return
			item = self.fav_list.get(idx[0])
			path = item.split("::",1)[1]
			self._navigate_to(path)
		except Exception:
			pass

	def _populate_devices(self) -> None:
		self.dev_list.delete(0, tk.END)
		if platform.system() == "Windows":
			for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
				root = f"{letter}:/"
				if os.path.exists(root):
					self.dev_list.insert(tk.END, root)
		else:
			self.dev_list.insert(tk.END, "/")

	def _on_device_select(self, event=None) -> None:
		try:
			idx = self.dev_list.curselection()
			if not idx:
				return
			path = self.dev_list.get(idx[0])
			self._navigate_to(path)
		except Exception:
			pass

	def _init_fs_tree(self) -> None:
		self.fs_tree.delete(*self.fs_tree.get_children())
		if platform.system() == "Windows":
			for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
				root = f"{letter}:/"
				if os.path.exists(root):
					node = self.fs_tree.insert("", tk.END, text=root, open=False, values=(""))
					self.fs_tree.insert(node, tk.END, text="...")
		else:
			node = self.fs_tree.insert("", tk.END, text="/", open=False, values=(""))
			self.fs_tree.insert(node, tk.END, text="...")

	def _on_fs_tree_open(self, event=None) -> None:
		item = self.fs_tree.focus()
		if not item:
			return
		path = self._fs_tree_item_path(item)
		# Populate children lazily
		children = self.fs_tree.get_children(item)
		if len(children) == 1 and self.fs_tree.item(children[0], "text") == "...":
			self.fs_tree.delete(children[0])
			try:
				with os.scandir(path) as it:
					names = [e.name for e in it if e.is_dir(follow_symlinks=False)]
				names.sort(key=lambda s: s.lower())
				for name in names:
					sub = os.path.join(path, name)
					n = self.fs_tree.insert(item, tk.END, text=name, open=False, values=(""))
					# Add placeholder for further expansion
					self.fs_tree.insert(n, tk.END, text="...")
			except Exception:
				pass

	def _on_fs_tree_double(self, event=None) -> None:
		item = self.fs_tree.focus()
		if not item:
			return
		path = self._fs_tree_item_path(item)
		self._navigate_to(path)

	def _fs_tree_item_path(self, item) -> str:
		parts = []
		cur = item
		while cur:
			parts.append(self.fs_tree.item(cur, "text"))
			cur = self.fs_tree.parent(cur)
		full = os.path.join(*reversed(parts))
		if platform.system() == "Windows" and len(full) == 2 and full[1] == ":":
			full += "/"
		return full

	def _start_search(self, event=None) -> None:
		query = self.search_var.get().strip()
		if not query:
			return
		self._stop_search()
		self._search_stop = False
		threading.Thread(target=self._search_worker, args=(self.current_path, query, self.filter_var.get()), daemon=True).start()

	def _stop_search(self) -> None:
		self._search_stop = True

	def _search_worker(self, root: str, query: str, filter_name: str) -> None:
		patterns_img = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")
		patterns_doc = (".txt", ".md", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv")
		patterns_arc = (".zip", ".rar", ".7z", ".tar", ".gz")
		patterns_audio = (".mp3", ".wav", ".flac", ".ogg", ".m4a")
		patterns_video = (".mp4", ".mkv", ".avi", ".mov", ".webm")
		patterns_code = (".py", ".js", ".ts", ".java", ".c", ".cpp", ".cs", ".go", ".rb", ".php", ".rs", ".kt", ".swift")
		try:
			for dirpath, dirnames, filenames in os.walk(root):
				if getattr(self, "_search_stop", False):
					break
				for fname in filenames:
					if getattr(self, "_search_stop", False):
						break
					fp = os.path.join(dirpath, fname)
					name_ok = query.lower() in fname.lower()
					if not name_ok:
						continue
					if filter_name == "Images" and os.path.splitext(fname)[1].lower() not in patterns_img:
						continue
					if filter_name == "Documents" and os.path.splitext(fname)[1].lower() not in patterns_doc:
						continue
					if filter_name == "Archives" and os.path.splitext(fname)[1].lower() not in patterns_arc:
						continue
					if filter_name == "Audio" and os.path.splitext(fname)[1].lower() not in patterns_audio:
						continue
					if filter_name == "Video" and os.path.splitext(fname)[1].lower() not in patterns_video:
						continue
					if filter_name == "Code" and os.path.splitext(fname)[1].lower() not in patterns_code:
						continue
					# Post result to UI thread via after
					self.master.after(0, lambda f=fp: self._add_search_result(f))
		except Exception:
			pass

	def _add_search_result(self, full_path: str) -> None:
		# If search is ongoing, show results in current listing area by navigating to the file's directory and focusing it
		try:
			dirname, fname = os.path.dirname(full_path), os.path.basename(full_path)
			if os.path.abspath(dirname) != os.path.abspath(self.current_path):
				self.current_path = dirname
				self.path_var.set(self.current_path)
				self._rebuild_breadcrumb()
				self._populate_listing(self.current_path)
			# Focus the found item if present
			for iid in self.tree.get_children():
				if self.tree.item(iid, "text") == fname:
					self.tree.see(iid)
					self.tree.selection_set(iid)
					break
		except Exception:
			pass

	def _update_preview(self) -> None:
		try:
			# Clear
			self.preview_image.configure(image="")
			self.preview_text.configure(state="normal")
			self.preview_text.delete("1.0", tk.END)
			self.preview_text.configure(state="disabled")
			# Get selection
			sel = self.tree.selection()
			if not sel:
				return
			name = self.tree.item(sel[0], "text")
			full = os.path.join(self.current_path, name)
			if os.path.isdir(full):
				return
			ext = os.path.splitext(full)[1].lower()
			if ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp"):
				try:
					img = None
					if ext in (".png", ".gif"):
						img = tk.PhotoImage(file=full)
					elif Image and ImageTk:
						pil = Image.open(full)
						pil.thumbnail((400, 300))
						img = ImageTk.PhotoImage(pil)
					if img:
						self.preview_image.configure(image=img)
						self.preview_image.image = img
				except Exception:
					pass
			elif ext in (".txt", ".md", ".py", ".json", ".csv", ".ini", ".log"):
				try:
					with open(full, "r", encoding="utf-8", errors="ignore") as f:
						content = f.read(10000)
				except Exception:
					content = ""
				self.preview_text.configure(state="normal")
				self.preview_text.insert("1.0", content)
				self.preview_text.configure(state="disabled")
		except Exception:
			pass

	def _get_icon(self, name: str, is_dir: bool) -> tk.PhotoImage:
		key = "folder" if is_dir else (os.path.splitext(name)[1].lower() or "file")
		if key in self.icons:
			return self.icons[key]
		# Create 16x16 icon based on theme and type
		p = self._get_palette()
		img = tk.PhotoImage(width=16, height=16)
		# Simple glyphs
		if key == "folder":
			base = "#f59e0b" if self.current_theme == "light" else "#b45309"
			accent = "#fbbf24" if self.current_theme == "light" else "#92400e"
			self._draw_rect(img, 1,5,14,13, base)
			self._draw_rect(img, 1,3,8,6, accent)
		elif key in (".png",".jpg",".jpeg",".gif",".bmp",".svg"):
			self._draw_rect(img, 2,2,13,13, p["border"])
			self._draw_rect(img, 3,3,12,12, p["surface"])
			self._draw_rect(img, 4,8,7,11, "#10b981")
			self._draw_rect(img, 8,5,11,9, "#3b82f6")
		elif key in (".txt",".md",".py",".js",".json",".xml",".html",".css",".csv",".ini",".yml",".yaml"):
			paper = "#e5e7eb" if self.current_theme == "light" else "#374151"
			self._draw_rect(img, 3,2,13,13, p["border"])
			self._draw_rect(img, 4,3,12,12, paper)
			self._draw_rect(img, 5,5,11,6, p["subtext"])
			self._draw_rect(img, 5,7,11,8, p["subtext"])
			self._draw_rect(img, 5,9,11,10, p["subtext"])
		elif key in (".zip",".rar",".7z",".tar",".gz"):
			self._draw_rect(img, 3,3,13,13, "#a78bfa")
			self._draw_rect(img, 7,3,9,13, p["border"])
		else:
			self._draw_rect(img, 3,3,13,13, "#60a5fa" if self.current_theme == "light" else "#2563eb")
		self.icons[key] = img
		return img

	def _draw_rect(self, img: tk.PhotoImage, x1: int, y1: int, x2: int, y2: int, color: str) -> None:
		# Fill rectangle with a single color
		img.put(color, to=(x1, y1, x2, y2))

	def _format_size(self, size: int) -> str:
		if size is None:
			return ""
		for unit in ["B", "KB", "MB", "GB", "TB"]:
			if size < 1024.0 or unit == "TB":
				return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
			size /= 1024.0
		return f"{size:.1f} TB"

	def _set_status(self, text: str) -> None:
		self.status_var.set(text)

	def _status_text(self, count: int) -> str:
		try:
			usage = shutil.disk_usage(self.current_path)
			free_gb = usage.free / (1024**3)
			total_gb = usage.total / (1024**3)
			return f"{count} item(s) • Free {free_gb:.1f} GB of {total_gb:.1f} GB"
		except Exception:
			return f"{count} item(s)"

	def _open_with_system(self, path: str) -> None:
		try:
			if platform.system() == "Windows":
				os.startfile(path)  # type: ignore[attr-defined]
			elif platform.system() == "Darwin":
				subprocess.Popen(["open", path])
			else:
				subprocess.Popen(["xdg-open", path])
		except Exception as exc:
			messagebox.showerror("Open Error", str(exc))

	def _populate_drives(self) -> None:
		try:
			drives = []
			for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
				root = f"{letter}:/"
				if os.path.exists(root):
					drives.append(root)
			self.drive_combo["values"] = drives
			# Preselect current drive
			cur = os.path.splitdrive(self.current_path)[0]
			if cur:
				self.drive_var.set(cur + "/")
		except Exception:
			pass

	def _on_drive_change(self, event=None) -> None:
		val = self.drive_var.get()
		if val:
			self._change_directory(val)

	def _rebuild_breadcrumb(self) -> None:
		for w in self.breadcrumb.winfo_children():
			w.destroy()
		path = os.path.abspath(self.current_path)
		parts = []
		drive, tail = os.path.splitdrive(path)
		if drive:
			parts.append((drive + os.sep, drive + os.sep))
			path_no_drive = tail.lstrip(os.sep)
			accum = drive + os.sep
			for p in path_no_drive.split(os.sep):
				if not p:
					continue
				accum = os.path.join(accum, p)
				parts.append((p, accum))
		else:
			accum = os.sep
			parts.append((os.sep, os.sep))
			for p in path.strip(os.sep).split(os.sep):
				if not p:
					continue
				accum = os.path.join(accum, p)
				parts.append((p, accum))
		for i, (label, full) in enumerate(parts):
			btn = ttk.Button(self.breadcrumb, text=label, command=lambda f=full: self._change_directory(f))
			btn.pack(side=tk.LEFT)
			if i < len(parts) - 1:
				ttk.Label(self.breadcrumb, text=" › ").pack(side=tk.LEFT)

	def _toggle_hidden(self) -> None:
		self.show_hidden = bool(self.hidden_var.get())
		self._populate_listing(self.current_path)

	def _toggle_hidden_hotkey(self) -> None:
		try:
			self.hidden_var.set(not self.hidden_var.get())
			self._toggle_hidden()
		except Exception:
			pass

	def _on_sort(self, key: str) -> None:
		if self.sort_by == key:
			self.sort_reverse = not self.sort_reverse
		else:
			self.sort_by = key
			self.sort_reverse = False
		self._populate_listing(self.current_path)

	def _on_view_mode_change(self) -> None:
		# Adjust columns visibility based on mode
		mode = self.view_mode.get()
		if mode == "details":
			self.tree.configure(show="tree headings")
			self.tree.column("type", width=120)
			self.tree.column("size", width=100)
			self.tree.column("modified", width=180)
		elif mode == "icons":
			self.tree.configure(show="tree")
			self.tree.column("type", width=0)
			self.tree.column("size", width=0)
			self.tree.column("modified", width=0)
			self.style.configure("Treeview", rowheight=40)
		else:
			self.tree.configure(show="tree headings")
			self.tree.column("type", width=140)
			self.tree.column("size", width=120)
			self.tree.column("modified", width=0)
			self.style.configure("Treeview", rowheight=28)
		self._populate_listing(self.current_path)
		self._save_settings_safe()

	def _on_select_change(self, event=None) -> None:
		try:
			self._update_preview()
			self._update_selection_status()
		except Exception:
			pass

	def _update_selection_status(self) -> None:
		try:
			sel = self.tree.selection()
			if not sel:
				self._set_status(self._status_text(self._last_entry_count))
				return
			num = len(sel)
			total_size = 0
			for iid in sel:
				name = self.tree.item(iid, "text")
				full = os.path.join(self.current_path, name)
				try:
					if os.path.isfile(full):
						total_size += os.path.getsize(full)
				except Exception:
					pass
			self._set_status(f"{num} selected • {self._format_size(total_size)}")
		except Exception:
			pass

	def _show_context_menu(self, event) -> None:
		try:
			self.tree.focus(self.tree.identify_row(event.y))
			self.tree.selection_set(self.tree.focus())
		except Exception:
			pass
		self._update_context_menu()
		self.ctx_menu.tk_popup(event.x_root, event.y_root)
		self.ctx_menu.grab_release()

	def _build_context_menu(self) -> None:
		self.ctx_menu = tk.Menu(self.master, tearoff=0)
		self.ctx_menu.add_command(label="Open", command=lambda: self._on_double_click())
		self.ctx_menu.add_command(label="Open in new window", command=self._open_in_new_window)
		self.ctx_menu.add_separator()
		self.ctx_menu.add_command(label="Rename", command=self._rename_selected)
		self.ctx_menu.add_command(label="Delete", command=self._delete_selected)
		self.ctx_menu.add_separator()
		self.ctx_menu.add_command(label="Copy path", command=self._copy_path_to_clipboard)
		self.ctx_menu.add_command(label="Copy name", command=self._copy_name_to_clipboard)
		self.ctx_menu.add_command(label="Reveal in Explorer", command=self._reveal_in_explorer)
		self.ctx_menu.add_command(label="Open Terminal here", command=self._open_terminal_here)
		self.ctx_menu.add_separator()
		self.ctx_menu.add_command(label="New Folder", command=self._create_folder)
		self.ctx_menu.add_command(label="New File", command=self._create_file)
		self.ctx_menu.add_separator()
		self.ctx_menu.add_command(label="Copy To...", command=self._copy_selected_to)
		self.ctx_menu.add_command(label="Move To...", command=self._move_selected_to)
		self.ctx_menu.add_separator()
		self.ctx_menu.add_command(label="Select All", command=self._select_all)
		self.ctx_menu.add_command(label="Properties", command=self._show_properties)

	def _update_context_menu(self) -> None:
		# Enable/disable items based on selection
		sel = self.tree.selection()
		one = len(sel) == 1
		nonempty = len(sel) > 0
		def set_state(label: str, enabled: bool):
			try:
				self.ctx_menu.entryconfig(label, state=tk.NORMAL if enabled else tk.DISABLED)
			except Exception:
				pass
		set_state("Open", one)
		set_state("Open in new window", one)
		set_state("Rename", one)
		set_state("Delete", nonempty)
		set_state("Copy path", one or nonempty)
		set_state("Copy name", one)
		set_state("Reveal in Explorer", one)
		set_state("Open Terminal here", True)
		set_state("Copy To...", nonempty)
		set_state("Move To...", nonempty)

	def _select_all(self) -> None:
		try:
			for iid in self.tree.get_children():
				self.tree.selection_add(iid)
		except Exception:
			pass

	def _copy_path_to_clipboard(self) -> None:
		try:
			selected = self.tree.selection()
			if not selected:
				return
			paths = []
			for iid in selected:
				name = self.tree.item(iid, "text")
				paths.append(os.path.join(self.current_path, name))
			self.master.clipboard_clear()
			self.master.clipboard_append("\n".join(paths))
		except Exception:
			pass

	def _copy_name_to_clipboard(self) -> None:
		try:
			sel = self.tree.selection()
			if not sel:
				return
			names = [self.tree.item(i, "text") for i in sel]
			self.master.clipboard_clear()
			self.master.clipboard_append("\n".join(names))
		except Exception:
			pass

	def _open_terminal_here(self) -> None:
		try:
			path = self.current_path
			if self.tree.selection():
				name = self.tree.item(self.tree.selection()[0], "text")
				cand = os.path.join(self.current_path, name)
				if os.path.isdir(cand):
					path = cand
			if platform.system() == "Windows":
				try:
					subprocess.Popen(["wt.exe", "-d", path])
				except Exception:
					subprocess.Popen(["cmd.exe", "/K", f"cd /d {path}"])
			elif platform.system() == "Darwin":
				subprocess.Popen(["open", "-a", "Terminal", path])
			else:
				subprocess.Popen(["x-terminal-emulator"], cwd=path)
		except Exception:
			pass

	def _reveal_in_explorer(self) -> None:
		try:
			sel = self.tree.selection()
			if not sel:
				return
			name = self.tree.item(sel[0], "text")
			path = os.path.join(self.current_path, name)
			if platform.system() == "Windows":
				subprocess.Popen(["explorer", "/select,", path])
			elif platform.system() == "Darwin":
				subprocess.Popen(["open", "-R", path])
			else:
				dirname = path if os.path.isdir(path) else os.path.dirname(path)
				subprocess.Popen(["xdg-open", dirname])
		except Exception:
			pass

	def _open_in_new_window(self) -> None:
		try:
			path = self.current_path
			if self.tree.selection():
				name = self.tree.item(self.tree.selection()[0], "text")
				candidate = os.path.join(self.current_path, name)
				if os.path.isdir(candidate):
					path = candidate
			subprocess.Popen([sys.executable, sys.argv[0], path])
		except Exception:
			pass

	def _show_properties(self) -> None:
		try:
			sel = self.tree.selection()
			if not sel:
				return
			name = self.tree.item(sel[0], "text")
			full = os.path.join(self.current_path, name)
			st = os.stat(full)
			is_dir = os.path.isdir(full)
			size_text = "—" if is_dir else self._format_size(st.st_size)
			mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
			info = [
				f"Name: {name}",
				f"Path: {full}",
				f"Type: {'Folder' if is_dir else self._get_file_type(name)}",
				f"Size: {size_text}",
				f"Modified: {mtime}",
			]
			messagebox.showinfo("Properties", "\n".join(info))
		except Exception as exc:
			messagebox.showerror("Properties", str(exc))

	def _update_path_history(self, path: str) -> None:
		# Keep unique, most recent first; limit to 25
		try:
			abs_path = os.path.abspath(path)
			if abs_path in self.path_history:
				self.path_history.remove(abs_path)
			self.path_history.insert(0, abs_path)
			self.path_history = self.path_history[:25]
			try:
				self.path_combo["values"] = tuple(self.path_history)
			except Exception:
				pass
		except Exception:
			pass

	def _on_path_type(self, event=None) -> None:
		# Autocomplete directories for current input
		text = self.path_var.get().strip()
		if not text:
			return
		base_dir = text
		try:
			if not os.path.isdir(base_dir):
				base_dir = os.path.dirname(text.rstrip(os.sep)) or os.sep
			if not base_dir or not os.path.isdir(base_dir):
				return
			names: list[str] = []
			prefix = os.path.basename(text.rstrip(os.sep))
			with os.scandir(base_dir) as it:
				for entry in it:
					if entry.is_dir():
						if not prefix or entry.name.lower().startswith(prefix.lower()):
							names.append(os.path.join(base_dir, entry.name))
			names.sort(key=lambda s: s.lower())
			self.path_combo["values"] = tuple(self.path_history + names[:50])
		except Exception:
			pass

	def _focus_path(self) -> None:
		try:
			self.path_combo.focus_set()
			self.path_combo.selection_range(0, tk.END)
		except Exception:
			pass

	def _alt_row_color(self) -> str:
		# Zebra stripe depending on theme
		return self._get_palette()["zebra"]

	def _get_palette(self) -> dict:
		if self.current_theme == "dark":
			return {
				"bg": "#0b1220",
				"surface": "#111827",
				"text": "#e5e7eb",
				"subtext": "#9ca3af",
				"primary": "#60a5fa",
				"accent": "#34d399",
				"border": "#1f2937",
				"hover": "#1f2937",
				"sel_bg": "#1d4ed8",
				"sel_fg": "#e5e7eb",
				"zebra": "#0f1629",
			}
		return {
			"bg": "#f5f7fb",
			"surface": "#ffffff",
			"text": "#111827",
			"subtext": "#4b5563",
			"primary": "#3b82f6",
			"accent": "#22c55e",
			"border": "#e5e7eb",
			"hover": "#f3f4f6",
			"sel_bg": "#dbeafe",
			"sel_fg": "#111827",
			"zebra": "#f9fafb",
		}

	def _init_style(self) -> None:
		self._apply_theme()

	def _apply_theme(self) -> None:
		p = self._get_palette()
		try:
			self.master.configure(bg=p["bg"])  # window background
		except Exception:
			pass
		# General widgets
		self.style.configure("TFrame", background=p["bg"])
		self.style.configure("TLabelframe", background=p["bg"], bordercolor=p["border"])
		self.style.configure("TLabel", background=p["bg"], foreground=p["text"])
		self.style.configure("TCheckbutton", background=p["bg"], foreground=p["text"])
		self.style.configure("TEntry", fieldbackground=p["surface"], foreground=p["text"], bordercolor=p["border"])
		self.style.configure("TCombobox", fieldbackground=p["surface"], foreground=p["text"], bordercolor=p["border"])
		self.style.configure("TButton", background=p["surface"], foreground=p["text"], bordercolor=p["border"], focusthickness=3, focuscolor=p["primary"])
		self.style.map("TButton",
			background=[("active", p["hover"])],
			foreground=[("disabled", p["subtext"])])
		# Panes and tabs
		self.style.configure("TPanedwindow", background=p["bg"])
		self.style.configure("TNotebook", background=p["bg"], bordercolor=p["border"])
		self.style.configure("TNotebook.Tab", background=p["surface"], foreground=p["text"], bordercolor=p["border"])
		self.style.map("TNotebook.Tab",
			background=[("selected", p["hover"])],
			foreground=[("disabled", p["subtext"])])
		# Treeview styling
		self.style.configure(
			"Treeview",
			background=p["surface"],
			fieldbackground=p["surface"],
			foreground=p["text"],
			bordercolor=p["border"],
			rowheight=24,
		)
		self.style.configure(
			"Treeview.Heading",
			background=p["bg"],
			foreground=p["text"],
			bordercolor=p["border"],
		)
		self.style.map(
			"Treeview",
			background=[("selected", p["sel_bg"])],
			foreground=[("selected", p["sel_fg"])],
		)
		# Scrollbar styling
		self.style.configure("Vertical.TScrollbar", background=p["surface"], troughcolor=p["bg"], bordercolor=p["border"])
		self.style.configure("Horizontal.TScrollbar", background=p["surface"], troughcolor=p["bg"], bordercolor=p["border"])
		# Update zebra color if tree exists
		try:
			self.tree.tag_configure('odd', background=self._alt_row_color())
		except Exception:
			pass
		# Regenerate icons for new palette
		try:
			self.icons.clear()
			self._populate_listing(self.current_path)
		except Exception:
			pass
		# Apply theme to classic widgets (Listbox/Text/labels)
		try:
			if hasattr(self, "fav_list"):
				self.fav_list.configure(bg=p["bg"], fg=p["text"], highlightthickness=0,
					selectbackground=p["sel_bg"], selectforeground=p["sel_fg"])
			if hasattr(self, "dev_list"):
				self.dev_list.configure(bg=p["bg"], fg=p["text"], highlightthickness=0,
					selectbackground=p["sel_bg"], selectforeground=p["sel_fg"])
			if hasattr(self, "preview_text"):
				self.preview_text.configure(bg=p["surface"], fg=p["text"], insertbackground=p["text"], highlightthickness=0)
			if hasattr(self, "preview_image"):
				self.preview_image.configure(background=p["bg"])
		except Exception:
			pass

	def _toggle_theme(self) -> None:
		self.current_theme = "dark" if self.current_theme == "light" else "light"
		self.theme_btn.config(text="Light" if self.current_theme == "dark" else "Dark")
		self._apply_theme()
		# Force redraw of current listing to refresh zebra striping
		self._populate_listing(self.current_path)
		self._save_settings_safe()

	def _ask_directory(self, title: str, initialdir: str | None = None) -> str | None:
		current_dir = os.path.abspath(initialdir or self.current_path)

		dialog = tk.Toplevel(self.master)
		dialog.title(title)
		dialog.geometry("700x450")
		dialog.transient(self.master)
		dialog.grab_set()

		# Path controls
		path_frame = ttk.Frame(dialog)
		path_frame.pack(fill=tk.X, padx=8, pady=8)
		path_var = tk.StringVar(value=current_dir)
		path_entry = ttk.Entry(path_frame, textvariable=path_var)
		path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
		
		def on_go_event(event=None):
			new_path = path_var.get().strip()
			if os.path.isdir(new_path):
				populate(new_path)
			else:
				messagebox.showerror(title, "Not a directory")

		go_btn = ttk.Button(path_frame, text="Go", command=on_go_event)
		go_btn.pack(side=tk.LEFT, padx=(6,0))
		up_btn = ttk.Button(path_frame, text="Up", command=lambda: populate(os.path.dirname(path_var.get().rstrip(os.sep))))
		up_btn.pack(side=tk.LEFT, padx=(6,0))

		# Folder list
		columns = ("modified",)
		tree = ttk.Treeview(dialog, columns=columns, show="tree headings", selectmode="browse")
		tree.heading("#0", text="Folder")
		tree.heading("modified", text="Modified")
		tree.column("#0", width=420, anchor=tk.W)
		tree.column("modified", width=200, anchor=tk.W)
		tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))

		def populate(path: str):
			nonlocal current_dir
			if not os.path.isdir(path):
				return
			current_dir = os.path.abspath(path)
			path_var.set(current_dir)
			for iid in tree.get_children():
				tree.delete(iid)
			try:
				entries: list[tuple[str, datetime]] = []
				with os.scandir(current_dir) as it:
					for entry in it:
						if entry.is_dir(follow_symlinks=False):
							try:
								st = entry.stat()
								entries.append((entry.name, datetime.fromtimestamp(st.st_mtime)))
							except PermissionError:
								continue
				entries.sort(key=lambda e: e[0].lower())
				for name, mtime in entries:
					tree.insert("", tk.END, text=name, values=(mtime.strftime("%Y-%m-%d %H:%M"),))
			except Exception:
				pass

		def on_double_click(event=None):
			item = tree.focus()
			if not item:
				return
			name = tree.item(item, "text")
			populate(os.path.join(current_dir, name))

		tree.bind("<Double-1>", on_double_click)

		# Action buttons
		buttons = ttk.Frame(dialog)
		buttons.pack(fill=tk.X, padx=8, pady=(0,8))
		result: dict[str, str | None] = {"path": None}

		def on_select():
			item = tree.focus()
			if item:
				folder = os.path.join(current_dir, tree.item(item, "text"))
				if os.path.isdir(folder):
					result["path"] = folder
					dialog.destroy()
					return
			# If nothing selected, choose current_dir
			result["path"] = current_dir
			dialog.destroy()

		select_btn = ttk.Button(buttons, text="Select", command=on_select)
		select_btn.pack(side=tk.RIGHT)
		cancel_btn = ttk.Button(buttons, text="Cancel", command=lambda: (result.update({"path": None}), dialog.destroy()))
		cancel_btn.pack(side=tk.RIGHT, padx=(0,6))

		populate(current_dir)
		dialog.wait_window()
		return result["path"]


def main() -> None:
	root = tk.Tk()
	style = ttk.Style(root)
	try:
		style.theme_use("clam")
	except Exception:
		pass
	app = FileManagerApp(root)
	root.mainloop()


if __name__ == "__main__":
	main()


