import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

import crypto_core as core


def resource_path(rel):
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, rel)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), rel)


BG_DARK = "#1a1a1a"
BG_PANEL = "#222222"
ACCENT = "#FFD700"
FG_TEXT = "#E0E0E0"
FG_MUTED = "#777777"
FONT = "Consolas"
PROGRAM_NAME = "ShutFiles"


def register_windows_context_menu():
    if os.name != "nt":
        return False
    try:
        import winreg
        if getattr(sys, "frozen", False):
            command = f'"{sys.executable}" "%1"'
        else:
            command = f'"{sys.executable}" "{os.path.abspath(__file__)}" "%1"'

        base_path = r"*\shell\ShutFiles"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, base_path) as key:
            winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ,
                              "Заблокировать/Разблокировать в SF")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, sys.executable)

        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, base_path + r"\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        return True
    except Exception as e:
        print(f"[SF] Не удалось записать в реестр: {e}")
        return False


class ShutFilesApp(tk.Tk):
    def __init__(self, initial_file=None):
        super().__init__()
        self.title("ShutFiles — SF")
        try:
            self.iconbitmap(resource_path("assets/sf.ico"))
        except Exception:
            pass
        self.geometry("980x620")
        self.configure(bg=BG_DARK)
        self.minsize(820, 520)

        self.selected_file = None
        self._build_ui()
        self._refresh_listbox()

        if initial_file and os.path.isfile(initial_file):
            self._apply_selected_file(initial_file)

    def _build_ui(self):
        header = tk.Frame(self, bg=BG_DARK, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="▌ SHUTFILES  /  DATA-PROTECTION",
                 bg=BG_DARK, fg=ACCENT, font=(FONT, 15, "bold")).pack(
            side="left", padx=18, pady=10)
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

        container = tk.Frame(self, bg=BG_DARK)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        container.grid_columnconfigure(0, weight=1, uniform="half")
        container.grid_columnconfigure(1, weight=1, uniform="half")
        container.grid_rowconfigure(0, weight=1)

        self._build_left(container)
        self._build_right(container)

        self.status_var = tk.StringVar(value="ГОТОВ")
        tk.Label(self, textvariable=self.status_var, bg=BG_DARK, fg=FG_MUTED,
                 font=(FONT, 9), anchor="w").pack(fill="x", padx=14, pady=(0, 6))

    def _build_left(self, parent):
        left = tk.Frame(parent, bg=BG_PANEL, highlightbackground=ACCENT,
                        highlightthickness=2)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.grid_columnconfigure(0, weight=1)

        tk.Label(left, text="// УПРАВЛЕНИЕ", bg=BG_PANEL, fg=ACCENT,
                 font=(FONT, 12, "bold")).grid(row=0, column=0, sticky="w",
                                               padx=14, pady=(14, 8))

        tk.Label(left, text="ВЫБРАННЫЙ ФАЙЛ:", bg=BG_PANEL, fg=FG_MUTED,
                 font=(FONT, 9)).grid(row=1, column=0, sticky="w", padx=14)

        self.path_var = tk.StringVar()
        self.path_entry = tk.Entry(left, textvariable=self.path_var,
                                   state="readonly", readonlybackground="#0f0f0f",
                                   fg=ACCENT, insertbackground=ACCENT,
                                   font=(FONT, 10), relief="flat",
                                   highlightbackground=ACCENT, highlightthickness=1)
        self.path_entry.grid(row=2, column=0, sticky="ew", padx=14, pady=(2, 10),
                             ipady=6)

        self.browse_btn = tk.Button(left, text="ОБЗОР ФАЙЛА", command=self._on_browse,
                                    bg="#2c2c2c", fg=ACCENT, activebackground=ACCENT,
                                    activeforeground=BG_DARK, font=(FONT, 10, "bold"),
                                    relief="flat", cursor="hand2", pady=8,
                                    highlightbackground=ACCENT, highlightthickness=1)
        self.browse_btn.grid(row=3, column=0, sticky="ew", padx=14)

        tk.Label(left, text="ПАРОЛЬ (пусто = блок без пароля):", bg=BG_PANEL,
                 fg=FG_MUTED, font=(FONT, 9)).grid(row=4, column=0, sticky="w",
                                                   padx=14, pady=(18, 2))
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(left, textvariable=self.password_var,
                                       show="*", state="disabled",
                                       disabledbackground="#101010",
                                       disabledforeground=FG_MUTED,
                                       bg="#0f0f0f", fg=ACCENT, insertbackground=ACCENT,
                                       font=(FONT, 11), relief="flat",
                                       highlightbackground=ACCENT, highlightthickness=1)
        self.password_entry.grid(row=5, column=0, sticky="ew", padx=14, pady=(2, 12),
                                 ipady=6)

        self.lock_btn = tk.Button(left, text="ЗАБЛОКИРОВАТЬ", state="disabled",
                                  command=self._on_lock, bg="#2c2c2c", fg=FG_MUTED,
                                  disabledforeground=FG_MUTED, activebackground=ACCENT,
                                  activeforeground=BG_DARK, font=(FONT, 11, "bold"),
                                  relief="flat", cursor="hand2", pady=10,
                                  highlightbackground=ACCENT, highlightthickness=1)
        self.lock_btn.grid(row=6, column=0, sticky="ew", padx=14)

        tk.Label(left, text=("Подсказка: имя и расширение файла не меняются,\n"
                             "но содержимое портится (ОС скажет «файл повреждён»)."),
                 bg=BG_PANEL, fg=FG_MUTED, font=(FONT, 8), justify="left").grid(
            row=7, column=0, sticky="w", padx=14, pady=(16, 14))

    def _build_right(self, parent):
        right = tk.Frame(parent, bg=BG_PANEL, highlightbackground=ACCENT,
                         highlightthickness=2)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        tk.Label(right, text="// ЗАБЛОКИРОВАННЫЕ ФАЙЛЫ", bg=BG_PANEL, fg=ACCENT,
                 font=(FONT, 12, "bold")).grid(row=0, column=0, sticky="w",
                                               padx=14, pady=(14, 8))

        list_frame = tk.Frame(right, bg=BG_PANEL)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(list_frame, bg="#0f0f0f", fg=FG_TEXT,
                                  selectbackground=ACCENT, selectforeground=BG_DARK,
                                  font=(FONT, 10), relief="flat",
                                  highlightbackground=ACCENT, highlightthickness=1,
                                  activestyle="none")
        self.listbox.grid(row=0, column=0, sticky="nsew")

        scroll = tk.Scrollbar(list_frame, orient="vertical",
                              command=self.listbox.yview,
                              bg=BG_PANEL, troughcolor=BG_DARK,
                              activebackground=ACCENT)
        scroll.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scroll.set)

        self.listbox.bind("<Button-3>", self._on_right_click)

        self.context_menu = tk.Menu(self, tearoff=0, bg=BG_PANEL, fg=ACCENT,
                                    activebackground=ACCENT, activeforeground=BG_DARK,
                                    font=(FONT, 10))
        self.context_menu.add_command(label="Разблокировать", command=self._on_unlock)

    def _set_status(self, text):
        self.status_var.set(text.upper())

    def _activate_controls(self, enable):
        if enable:
            self.password_entry.configure(state="normal")
            self.lock_btn.configure(state="normal", fg=ACCENT, bg="#3a3a00")
        else:
            self.password_entry.configure(state="disabled")
            self.lock_btn.configure(state="disabled", fg=FG_MUTED, bg="#2c2c2c")

    def _apply_selected_file(self, path):
        self.selected_file = os.path.abspath(path)
        self.path_var.set(self.selected_file)
        self.password_var.set("")
        self._activate_controls(True)
        self.password_entry.focus_set()
        self._set_status(f"Выбран файл: {os.path.basename(self.selected_file)}")

    def _refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for entry in core.load_database():
            path = entry.get("path", "")
            kind = entry.get("type", "password")
            tag = "«БЕЗ ПАРОЛЯ»" if kind == "no_password" else "«ПАРОЛЬ»"
            self.listbox.insert(tk.END, f"  {os.path.basename(path)}   {tag}")
            self.listbox.itemconfigure(tk.END, foreground=FG_TEXT)

    def _on_browse(self):
        path = filedialog.askopenfilename(title="Выберите файл для блокировки")
        if not path:
            return
        self._apply_selected_file(path)

    def _on_lock(self):
        if not self.selected_file:
            return
        password = self.password_var.get()
        lock_type = "no_password" if password == "" else "password"

        ok = core.crypt_file(self.selected_file, password)
        if not ok:
            messagebox.showerror(PROGRAM_NAME, "Не удалось зашифровать файл.\n"
                                                "Возможно, он открыт в другой программе.")
            return

        core.add_entry(self.selected_file, lock_type)
        self._set_status(f"Заблокирован: {os.path.basename(self.selected_file)}")

        self.path_var.set("")
        self.password_var.set("")
        self.selected_file = None
        self._activate_controls(False)
        self._refresh_listbox()

    def _on_right_click(self, event):
        index = self.listbox.nearest(event.y)
        if index < 0:
            return
        bbox = self.listbox.bbox(index)
        if bbox is None:
            return
        if not (bbox[1] <= event.y <= bbox[1] + bbox[3]):
            return
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _on_unlock(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        index = sel[0]
        db = core.load_database()
        if index >= len(db):
            return
        entry = db[index]
        path = entry.get("path", "")
        kind = entry.get("type", "password")

        if not os.path.isfile(path):
            messagebox.showwarning(PROGRAM_NAME,
                                   f"Файл не найден:\n{path}\n\nЗапись будет удалена из базы.")
            core.remove_entry(path)
            self._refresh_listbox()
            return

        if kind == "no_password":
            if core.crypt_file(path, ""):
                core.remove_entry(path)
                self._refresh_listbox()
                self._set_status(f"Разблокирован: {os.path.basename(path)}")
            else:
                messagebox.showerror(PROGRAM_NAME, "Не удалось разблокировать файл.")
        else:
            self._ask_password_and_unlock(path)

    def _ask_password_and_unlock(self, path):
        dlg = tk.Toplevel(self)
        dlg.title("Введите пароль")
        dlg.configure(bg=BG_PANEL)
        dlg.geometry("360x170")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text=f"Пароль для:\n{os.path.basename(path)}",
                 bg=BG_PANEL, fg=ACCENT, font=(FONT, 10, "bold"),
                 justify="left").pack(anchor="w", padx=14, pady=(14, 6))

        pw_var = tk.StringVar()
        entry = tk.Entry(dlg, textvariable=pw_var, show="*", bg="#0f0f0f",
                         fg=ACCENT, insertbackground=ACCENT, relief="flat",
                         highlightbackground=ACCENT, highlightthickness=1,
                         font=(FONT, 11))
        entry.pack(fill="x", padx=14, pady=(0, 10), ipady=5)
        entry.focus_set()

        def do_unlock():
            pwd = pw_var.get()
            if pwd == "":
                messagebox.showwarning(PROGRAM_NAME, "Введите пароль.", parent=dlg)
                return
            if core.crypt_file(path, pwd):
                core.remove_entry(path)
                self._refresh_listbox()
                self._set_status(f"Разблокирован: {os.path.basename(path)}")
                dlg.destroy()
            else:
                messagebox.showerror(PROGRAM_NAME, "Не удалось расшифровать файл.",
                                     parent=dlg)

        def do_cancel():
            dlg.destroy()

        btn_frame = tk.Frame(dlg, bg=BG_PANEL)
        btn_frame.pack(fill="x", padx=14, pady=(0, 14))
        tk.Button(btn_frame, text="РАЗБЛОКИРОВАТЬ", command=do_unlock,
                  bg="#3a3a00", fg=ACCENT, activebackground=ACCENT,
                  activeforeground=BG_DARK, font=(FONT, 10, "bold"),
                  relief="flat", cursor="hand2", pady=6,
                  highlightbackground=ACCENT, highlightthickness=1).pack(
            side="left", expand=True, fill="x", padx=(0, 5))
        tk.Button(btn_frame, text="ОТМЕНА", command=do_cancel,
                  bg="#2c2c2c", fg=FG_TEXT, activebackground=ACCENT,
                  activeforeground=BG_DARK, font=(FONT, 10),
                  relief="flat", cursor="hand2", pady=6,
                  highlightbackground=ACCENT, highlightthickness=1).pack(
            side="left", expand=True, fill="x", padx=(5, 0))

        entry.bind("<Return>", lambda _e: do_unlock())
        dlg.bind("<Escape>", lambda _e: do_cancel())


def main():
    initial_file = None
    if len(sys.argv) > 1:
        candidate = sys.argv[1]
        if os.path.isfile(candidate):
            initial_file = candidate

    register_windows_context_menu()

    app = ShutFilesApp(initial_file=initial_file)
    app.mainloop()


if __name__ == "__main__":
    main()
