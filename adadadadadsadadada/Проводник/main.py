import os
import sys
import platform
import subprocess
import shutil
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


class FileManagerApp:

	def __init__(self, master: tk.Tk) -> None:
		self.master = master
		self.master.title("Python File Manager")
		self.master.geometry("1000x600")

		self.current_path = self._get_initial_path()
		self.show_hidden = False
		self.sort_by = "name"  # name | type | size | modified
		self.sort_reverse = False

		self._build_ui()
		self._populate_listing(self.current_path)

	def _get_initial_path(self) -> str:
		try:
			return os.path.expanduser("~")
		except Exception:
			return os.getcwd()

	def _build_ui(self) -> None:
		toolbar = ttk.Frame(self.master)
		toolbar.pack(fill=tk.X, padx=6, pady=6)

		self.path_var = tk.StringVar(value=self.current_path)
		self.path_entry = ttk.Entry(toolbar, textvariable=self.path_var)
		self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
		self.path_entry.bind("<Return>", self._on_go)

		go_btn = ttk.Button(toolbar, text="Go", command=self._on_go)
		go_btn.pack(side=tk.LEFT, padx=(6, 0))

		up_btn = ttk.Button(toolbar, text="Up", command=self._on_up)
		up_btn.pack(side=tk.LEFT, padx=(6, 0))

		refresh_btn = ttk.Button(toolbar, text="Refresh", command=self._on_refresh)
		refresh_btn.pack(side=tk.LEFT, padx=(6, 0))

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

		columns = ("type", "size", "modified")
		self.tree = ttk.Treeview(self.master, columns=columns, show="tree headings", selectmode="extended")
		self.tree.heading("#0", text="Name", command=lambda: self._on_sort("name"))
		self.tree.heading("type", text="Type", command=lambda: self._on_sort("type"))
		self.tree.heading("size", text="Size", command=lambda: self._on_sort("size"))
		self.tree.heading("modified", text="Modified", command=lambda: self._on_sort("modified"))
		self.tree.column("#0", width=420, anchor=tk.W)
		self.tree.column("type", width=120, anchor=tk.W)
		self.tree.column("size", width=100, anchor=tk.E)
		self.tree.column("modified", width=180, anchor=tk.W)
		self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0,6))

		self.tree.bind("<Double-1>", self._on_double_click)
		self.tree.bind("<Return>", self._on_enter)
		self.tree.bind("<Button-3>", self._show_context_menu)
		self.master.bind("<F2>", lambda e: self._rename_selected())
		self.master.bind("<Delete>", lambda e: self._delete_selected())
		self.master.bind("<F5>", lambda e: self._on_refresh())

		# Row tags for zebra striping
		self.tree.tag_configure('odd', background=self._alt_row_color())

		status_bar = ttk.Frame(self.master)
		status_bar.pack(fill=tk.X, side=tk.BOTTOM)
		self.status_var = tk.StringVar(value="")
		self.status_label = ttk.Label(status_bar, textvariable=self.status_var, anchor=tk.W)
		self.status_label.pack(fill=tk.X, padx=6, pady=3)

		# Context menu
		self.ctx_menu = tk.Menu(self.master, tearoff=0)
		self.ctx_menu.add_command(label="Open", command=lambda: self._on_double_click())
		self.ctx_menu.add_command(label="Rename", command=self._rename_selected)
		self.ctx_menu.add_command(label="Delete", command=self._delete_selected)
		self.ctx_menu.add_separator()
		self.ctx_menu.add_command(label="New Folder", command=self._create_folder)
		self.ctx_menu.add_command(label="New File", command=self._create_file)
		self.ctx_menu.add_separator()
		self.ctx_menu.add_command(label="Copy To...", command=self._copy_selected_to)
		self.ctx_menu.add_command(label="Move To...", command=self._move_selected_to)

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

	def _on_up(self) -> None:
		parent = os.path.dirname(self.current_path.rstrip(os.sep)) or self.current_path
		if parent and parent != self.current_path:
			self._change_directory(parent)

	def _on_refresh(self) -> None:
		self._populate_listing(self.current_path)

	def _on_double_click(self, event=None) -> None:
		item_id = self.tree.focus()
		if not item_id:
			return
		item_path = self.tree.item(item_id, "text")
		full_path = os.path.join(self.current_path, item_path)
		if os.path.isdir(full_path):
			self._change_directory(full_path)
		else:
			self._open_with_system(full_path)

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
		except Exception as exc:
			messagebox.showerror("Error", str(exc))

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
				self.tree.insert("", tk.END, text=name, values=(type_name, size_display, mtime_display), tags=("odd",) if idx % 2 else ())

			self._set_status(self._status_text(len(entries)))
		except PermissionError:
			self._set_status("Permission denied")
		except FileNotFoundError:
			self._set_status("Directory not found")
		except Exception as exc:
			self._set_status(f"Error: {exc}")

	def _get_file_type(self, name: str) -> str:
		_, ext = os.path.splitext(name)
		return ext[1:].upper() + " File" if ext else "File"

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

	def _on_sort(self, key: str) -> None:
		if self.sort_by == key:
			self.sort_reverse = not self.sort_reverse
		else:
			self.sort_by = key
			self.sort_reverse = False
		self._populate_listing(self.current_path)

	def _show_context_menu(self, event) -> None:
		try:
			self.tree.focus(self.tree.identify_row(event.y))
			self.tree.selection_set(self.tree.focus())
		except Exception:
			pass
		self.ctx_menu.tk_popup(event.x_root, event.y_root)
		self.ctx_menu.grab_release()

	def _alt_row_color(self) -> str:
		# Light zebra stripe depending on theme
		return "#f6f6f6"

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


