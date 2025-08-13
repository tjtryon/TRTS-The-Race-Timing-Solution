#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
race_timing_gui.py – TRTS GUI Updated for TRMS Integration
Author: TJ Tryon
Date: August 12, 2025
Project: The Race Timing Solution for Cross Country and Road Races (TRTS)
Version: 1.1.0 (GUI) — Themed libadwaita & TRMS Integration

🎉 MAJOR RELEASE (GUI): A polished, libadwaita-themed interface that mirrors the TRMS Launcher:
• Consistent look & feel (colors, spacing, typography) with pixel-level polish
• Two-line, right-aligned header status: “Running Standalone / Integrated With TRMS” + database line
• First-run Admin Setup (bcrypt-secured) shown before the main window when config.db is missing
• Bottom console pane for logs with “Copy” support 🧾
• Themed dialogs for file picking, instructions, environment, results, and errors
• Smart window sizing so result/Instruction dialogs are only as wide/tall as needed
• Wayland-first, but X11-compatible; graceful GTK fallback if libadwaita isn’t available

🔌 Intelligent TRMS/TRDS integration:
• Auto-detects Standalone vs Integrated by scanning the TRMS directory structure
• Integrated paths:
    - config.db → TRDS/config/config.db
    - CSV imports → TRDS/databases/imports/
    - SQLite databases → TRDS/databases/sqlite3/
    - MariaDB (future) → TRDS/databases/mysql/
• Standalone paths default to ./data/ with automatic creation

🗄️ Database & naming:
• Active backend: SQLite3 (MariaDB/TRDS option is shown but disabled for now)
• Triathlon framework included (UI present; disabled until implementation)
• Standardized filenames: YYYYMMDD-<race#>-<type>-<Race_Name>.db
  (e.g., 20251007-01-rr-City_5K.db, 20251007-02-cc-County_Championship.db, 20251007-03-tri-Lakes_Tri.db)

🏁 Race features (GUI):
• Create new race databases (Cross Country, Road Race; Triathlon UI “coming soon”)
• Load existing databases and import runner CSVs (with themed pickers)
• Live timing window with big clock, bib entry, and incremental result recording
• Results viewers:
    - Individual results (auto-disabled until results exist)
    - Cross Country team scoring
    - Road Race age-group breakdowns
• Environment dialog (About → Environment) shows versions, session type, and integration paths

Key updates for TRMS integration (GUI):
- Intelligent detection: Standalone vs Integrated deployments
- Standardized, themed dialogs; bottom console with Copy
- Admin bootstrap flow before main window (when config.db is missing)
- Database type selector with MariaDB disabled (logic to be added later)
- Backward-compatible SQLite schema; safe directories for both modes

🎽 This GUI helps you time Cross Country and Road Races—cleanly, quickly, and in style. 🏃‍♀️🏃‍♂️
"""


import os, csv, sqlite3, datetime, platform
from pathlib import Path

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib, Gdk

print("DEBUG: module import OK")

# Optional libadwaita (can force-off via env var TRTS_FORCE_GTK=1)
try:
    gi.require_version("Adw", "1")
    from gi.repository import Adw
    USE_ADW = True
except Exception:
    Adw = None
    USE_ADW = False

if os.environ.get("TRTS_FORCE_GTK"):
    USE_ADW = False
    Adw = None

# ===== Root discovery (TRMS/TRDS integration) =====
def find_trms_root(start: Path | None = None) -> Path:
    if start is None:
        try:
            start = Path(__file__).resolve().parent
        except Exception:
            start = Path.cwd()

    def has_child_prefix(p: Path, prefix: str) -> bool:
        pref = prefix.lower()
        try:
            for child in p.iterdir():
                if child.is_dir() and child.name.lower().startswith(pref):
                    return True
        except Exception:
            pass
        return False

    cur = start
    for _ in range(10):
        name = cur.name.lower()
        if name.startswith("trts"):
            parent = cur.parent
            if has_child_prefix(parent, "trds"):
                return parent
        if cur.parent == cur:
            break
        cur = cur.parent

    cur = start
    for _ in range(10):
        if has_child_prefix(cur, "trds") or has_child_prefix(cur, "trts") or has_child_prefix(cur, "trms"):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent

    cur = start
    for _ in range(10):
        if (cur / "data").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent

    cwd = Path.cwd()
    (cwd / "data").mkdir(parents=True, exist_ok=True)
    return cwd

TRMS_ROOT = find_trms_root()

def detect_integration(trms_root: Path) -> dict:
    trds_dir = None
    try:
        for child in trms_root.iterdir():
            if child.is_dir() and child.name.lower().startswith("trds"):
                trds_dir = child
                break
    except Exception:
        trds_dir = None

    if not trds_dir:
        base = trms_root / "data"
        base.mkdir(parents=True, exist_ok=True)
        return {
            "integrated": False,
            "status_label": "Running Standalone",
            "config_db": base / "config.db",
            "imports_dir": base,
            "sqlite3_dir": base,
            "mysql_dir": None,
            "trds_root": None,
        }

    return {
        "integrated": True,
        "status_label": "Integrated With TRMS",
        "config_db": trds_dir / "config" / "config.db",
        "imports_dir": trds_dir / "databases" / "imports",
        "sqlite3_dir": trds_dir / "databases" / "sqlite3",
        "mysql_dir": trds_dir / "databases" / "mysql",
        "trds_root": trds_dir,
    }

INTEGRATION = detect_integration(TRMS_ROOT)
CONFIG_DB: Path = INTEGRATION["config_db"]
DB_SAVE_DIR: Path = INTEGRATION["sqlite3_dir"]
IMPORTS_DIR: Path = INTEGRATION["imports_dir"]
MYSQL_DIR: Path | None = INTEGRATION["mysql_dir"]

try:
    import bcrypt
except Exception:
    bcrypt = None

BaseApp = Adw.Application if USE_ADW else Gtk.Application

class RaceTimingApp(BaseApp):
    def __init__(self):
        super().__init__(application_id="org.midwest.RaceTimingGUI",
                         flags=Gio.ApplicationFlags.NON_UNIQUE)
        if USE_ADW:
            try: Adw.init()
            except Exception: pass

        self.main_window = None
        self.toast_overlay = None

        self.conn: sqlite3.Connection | None = None
        self.db_path: str | None = None
        self.race_type: str = ""

        self.status_duoline_label: Gtk.Label | None = None
        self.console_buffer: Gtk.TextBuffer | None = None
        self._win_keepalive = []

        self._setup_theme()
        self._register_icon_paths()

        act = Gio.SimpleAction.new("show_env", None)
        act.connect("activate", self.on_show_env)
        self.add_action(act)

    # ----- Styling
    def _setup_theme(self):
        css = Gtk.CssProvider()
        css_data = """
        * { font-family: "Garamond", "EB Garamond", "Times New Roman", serif; font-size: 15px; }
        .app-card { padding: 18px; margin: 6px; border-radius: 12px; background: alpha(@accent_bg_color, 0.08); }
        .title-1 { font-size: 22pt; font-weight: bold; margin: 6px; }
        .console-output { font-family: monospace; font-size: 10pt; padding: 8px; background: #101014; color: #e6e6e6; border-radius: 6px; }
        .dim-label { opacity: 0.85; }
        .results-text { font-family: "Space Mono", "Courier New", "Consolas", "Monaco", monospace; font-size: 11pt; }
        """
        try:
            css.load_from_data(css_data.encode())
            Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception as e:
            print("CSS load failed:", e)

    def _register_icon_paths(self):
        try:
            theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
            for p in [TRMS_ROOT/"icons", TRMS_ROOT/"icons"/"hicolor", Path(__file__).resolve().parent/"icons"]:
                if p.exists():
                    theme.add_search_path(str(p))
        except Exception as e:
            print("Icon path register skipped:", e)

    # ----- Helpers
    def _attach_child_to_window(self, win, widget):
        if hasattr(win, "set_content"): win.set_content(widget)
        else: win.set_child(widget)

    def _remember_window(self, win):
        try:
            self._win_keepalive.append(win)
            def _on_close(*args):
                try: self._win_keepalive.remove(win)
                except ValueError: pass
                return False
            try: win.connect("close-request", _on_close)
            except Exception: pass
        except Exception: pass

    def set_window_title(self, suffix: str | None):
        base = "⏱️ TRTS: The Race Timing Solution"
        if self.main_window:
            self.main_window.set_title(base if not suffix else f"{base} — {suffix}")

    def set_duoline_status(self, db_line: str):
        if self.status_duoline_label:
            self.status_duoline_label.set_label(f"{INTEGRATION['status_label']}\n{db_line}")

    def append_console(self, text: str):
        print(text, end="")
        if self.console_buffer:
            end = self.console_buffer.get_end_iter()
            self.console_buffer.insert(end, text)

    # ----- Lifecycle
    def do_startup(self):
        print("DEBUG: do_startup (about to chain to base)")
        try:
            if USE_ADW: Adw.Application.do_startup(self)
            else: Gtk.Application.do_startup(self)
            print("DEBUG: do_startup chained to base OK")
        except Exception as e:
            print("DEBUG: do_startup chain-up failed:", e)

    def do_activate(self):
        print("DEBUG: do_activate start")
        try:
            self.hold(); print("DEBUG: application hold() called")
        except Exception as e:
            print("DEBUG: hold() not available:", e)

        if not CONFIG_DB.exists():
            print("DEBUG: config.db missing at", CONFIG_DB)
            self.show_admin_setup_first_run()
            return

        print("DEBUG: building main window")
        self.build_main_window()
        if USE_ADW:
            self.main_window.set_application(self)
        self.main_window.present()
        try:
            self.main_window.connect("close-request", lambda *a: (self.release(), False))
            print("DEBUG: connected main_window close→release")
        except Exception as e:
            print("DEBUG: connect(close-request) failed:", e)
        self.set_window_title(None)
        self.append_console(f"TRTS GUI ready on {platform.platform()}\n")

    # ----- UI builders
    def build_main_window(self):
        if USE_ADW:
            self.main_window = Adw.ApplicationWindow(title="⏱️ TRTS: The Race Timing Solution")
            self.main_window.set_default_size(1000, 720)
            self.toast_overlay = Adw.ToastOverlay()
            self.main_window.set_content(self.toast_overlay)

            view = Adw.ToolbarView(); self.toast_overlay.set_child(view)
            header = Adw.HeaderBar(); view.add_top_bar(header)

            menu = Gio.Menu(); sec = Gio.Menu()
            sec.append("Environment…", "app.show_env"); menu.append_section(None, sec)
            mbtn = Gtk.MenuButton(icon_name="open-menu-symbolic"); mbtn.set_menu_model(menu); header.pack_end(mbtn)

            scrolled = Gtk.ScrolledWindow(hexpand=True, vexpand=True); view.set_content(scrolled)
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
            content.set_margin_top(8); content.set_margin_bottom(16); content.set_margin_start(16); content.set_margin_end(16)
            scrolled.set_child(content)

            self._add_title_section(content)
            self._add_controls_section(content)
            self._add_console_section(content)
        else:
            self.main_window = Gtk.ApplicationWindow(title="⏱️ TRTS: The Race Timing Solution")
            self.main_window.set_default_size(1000, 720)
            scrolled = Gtk.ScrolledWindow(hexpand=True, vexpand=True); self.main_window.set_child(scrolled)
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                              margin_top=8, margin_bottom=16, margin_start=16, margin_end=16)
            scrolled.set_child(content)
            self._add_title_section(content)
            self._add_controls_section(content)
            self._add_console_section(content)

    def _add_title_section(self, parent: Gtk.Widget):
        if USE_ADW:
            card = Adw.PreferencesGroup(); card.add_css_class("app-card"); parent.append(card)
        else:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); parent.append(card)

        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); v.set_halign(Gtk.Align.CENTER)
        title = Gtk.Label(); title.set_markup("<span weight='bold' size='x-large'>⏱️ TRTS: The Race Timing Solution (GUI)</span>"); title.add_css_class("title-1")
        subtitle = Gtk.Label(label="Professional Race Timing and Results · A TRMS: The Race Management Solution Suite Component"); subtitle.add_css_class("dim-label")
        v.append(title); v.append(subtitle)

        if USE_ADW:
            row = Adw.ActionRow(); row.set_child(v); card.add(row)
        else:
            card.append(v)

        if USE_ADW:
            status_row = Adw.ActionRow()
            self.status_duoline_label = Gtk.Label(label=f"{INTEGRATION['status_label']}\nNo database loaded")
            self.status_duoline_label.set_wrap(False); self.status_duoline_label.set_xalign(1.0)
            self.status_duoline_label.set_halign(Gtk.Align.END); self.status_duoline_label.set_justify(Gtk.Justification.RIGHT)
            status_row.add_suffix(self.status_duoline_label); card.add(status_row)
        else:
            self.status_duoline_label = Gtk.Label(label=f"{INTEGRATION['status_label']}\nNo database loaded")
            self.status_duoline_label.set_xalign(1.0); card.append(self.status_duoline_label)

    def _add_controls_section(self, parent: Gtk.Widget):
        if USE_ADW:
            grp = Adw.PreferencesGroup(); grp.add_css_class("app-card")
            grp.set_title("Race Controls")
            grp.set_description("Now Cross Country and Road Races · Coming Soon Triathlon and Split Timing")
            parent.append(grp)
            container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            row = Adw.ActionRow(); row.set_child(container); grp.add(row)
        else:
            grp = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8); parent.append(grp); container = grp

        for label, cb in [
            ("Create New Database", self.create_new_database),
            ("Load Existing Database", self.load_existing_database),
            ("Load Runners from CSV", self.load_csv_to_database),
            ("View All Runners", self.view_all_runners),
            ("Start the Race", self.start_race),
            ("Show Individual Results", self.show_individual_results),
        ]:
            b = Gtk.Button(label=label)
            if label == "Show Individual Results":
                self.individual_results_button = b
                b.set_sensitive(False)
            b.connect("clicked", cb)
            container.append(b)

        self.dynamic_results_button = Gtk.Button(label="Show Results (Load database first)")
        self.dynamic_results_button.set_sensitive(False)
        self.dynamic_results_button.connect("clicked", self.show_dynamic_results)
        container.append(self.dynamic_results_button)

        for label, cb in [("Instructions", self.show_instructions), ("Exit", lambda _b: self.quit())]:
            b = Gtk.Button(label=label); b.connect("clicked", cb); container.append(b)

    def _add_console_section(self, parent: Gtk.Widget):
        if USE_ADW:
            grp = Adw.PreferencesGroup(); grp.add_css_class("app-card"); grp.set_title("Console"); parent.append(grp)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); row = Adw.ActionRow(); row.set_child(box); grp.add(row)
        else:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); parent.append(box)

        sw = Gtk.ScrolledWindow(vexpand=False, hexpand=True); sw.set_min_content_height(140)
        tv = Gtk.TextView(); tv.set_editable(False); tv.set_monospace(True); tv.add_css_class("console-output")
        self.console_buffer = tv.get_buffer(); self.console_buffer.set_text("TRTS console ready…\n")
        sw.set_child(tv); box.append(sw)

        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8); hb.set_halign(Gtk.Align.END)
        copy_btn = Gtk.Button(label="Copy Console")
        def do_copy(_b):
            start = self.console_buffer.get_start_iter(); end = self.console_buffer.get_end_iter()
            txt = self.console_buffer.get_text(start, end, True); Gdk.Display.get_default().get_clipboard().set_text(txt)
        copy_btn.connect("clicked", do_copy); hb.append(copy_btn); box.append(hb)

    # ----- First-run Admin Setup
    def show_admin_setup_first_run(self):
        DB_SAVE_DIR.mkdir(parents=True, exist_ok=True)
        if INTEGRATION["integrated"]:
            INTEGRATION["imports_dir"].mkdir(parents=True, exist_ok=True)

        win = (Adw.ApplicationWindow if USE_ADW else Gtk.ApplicationWindow)(title="Admin Setup", application=self)
        self._remember_window(win); win.set_default_size(460, 300)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=16, margin_bottom=16, margin_start=16, margin_end=16)
        self._attach_child_to_window(win, box)

        head = Gtk.Label(); head.set_markup("<b>First-time setup</b>\nCreate admin credentials for race management")
        head.set_justify(Gtk.Justification.CENTER); box.append(head)

        user_row = Gtk.Entry(); user_row.set_placeholder_text("Admin Username")
        pw_row = Gtk.Entry(); pw_row.set_visibility(False); pw_row.set_placeholder_text("Admin Password")
        box.append(user_row); box.append(pw_row)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10); actions.set_halign(Gtk.Align.END)
        cancel_btn = Gtk.Button(label="Cancel"); save_btn = Gtk.Button(label="Save")
        actions.append(cancel_btn); actions.append(save_btn); box.append(actions)

        def on_cancel(_b): win.destroy(); self.quit()
        def on_save(_b):
            username = user_row.get_text().strip(); password = pw_row.get_text().strip()
            if not username or not password:
                self.show_error_window("Please enter both username and password."); return
            if bcrypt is None:
                self.show_error_window("bcrypt is not installed. Please `pip install bcrypt`."); return
            try:
                CONFIG_DB.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(str(CONFIG_DB)); c = conn.cursor()
                c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash BLOB NOT NULL)")
                pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
                c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pw_hash))
                conn.commit(); conn.close()
                self.append_console(f"Config DB created at {CONFIG_DB}\n")
            except Exception as e:
                self.show_error_window(f"Error creating config.db: {e}"); return
            win.destroy()
            self.build_main_window()
            if USE_ADW: self.main_window.set_application(self)
            self.main_window.present()
            self.set_window_title(None)
            self.set_duoline_status("No database loaded")

        cancel_btn.connect("clicked", on_cancel); save_btn.connect("clicked", on_save)
        win.present()

    # ----- Common dialogs/helpers
    def open_themed_file_picker(self, title: str, patterns: list[str], start_dir: Path, on_accept=None):
        win = (Adw.ApplicationWindow if USE_ADW else Gtk.ApplicationWindow)(title=title, application=self)
        self._remember_window(win); win.set_resizable(False)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=16, margin_bottom=16, margin_start=16, margin_end=16)
        self._attach_child_to_window(win, box)

        chooser = Gtk.FileChooserWidget(action=Gtk.FileChooserAction.OPEN)
        f = Gtk.FileFilter(); f.set_name("Matching files")
        for pat in patterns: f.add_pattern(pat)
        chooser.add_filter(f)
        try: chooser.set_current_folder(Gio.File.new_for_path(str(start_dir)))
        except Exception: pass
        box.append(chooser)

        act = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10); act.set_halign(Gtk.Align.END)
        cancel_btn = Gtk.Button(label="Cancel"); open_btn = Gtk.Button(label="Open")
        act.append(cancel_btn); act.append(open_btn); box.append(act)

        cancel_btn.connect("clicked", lambda _b: win.destroy())
        def do_open(_b):
            file = chooser.get_file()
            if not file:
                self.show_error_window("Please select a file."); return
            if on_accept:
                try: on_accept(file.get_path()); win.destroy()
                except Exception as e: self.show_error_window(f"Error opening file: {e}")
        open_btn.connect("clicked", do_open)
        win.present()

    def show_text_window(self, title: str, content: str, copy_enabled: bool=False, width_chars: int=None, wrap_mode: str="word", monospace: bool=True, base_size=(520, 420)):
        CHAR_PX = 8; padding_px = 80
        width_px = (width_chars * CHAR_PX + padding_px) if width_chars else base_size[0]

        # Determine compact layout (short messages like "CSV Import")
        lines = content.count("\n") + 1
        is_compact = (title == "CSV Import") or (lines <= 4 and (width_chars or 0) <= 45)

        win = (Adw.ApplicationWindow if USE_ADW else Gtk.ApplicationWindow)(title=title, application=self)
        self._remember_window(win)
        # Height: tight for compact messages, otherwise caller-provided base_size
        compact_height = 140 if lines <= 2 else 160
        win.set_default_size(int(width_px), (compact_height if is_compact else base_size[1]))

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=16, margin_bottom=16, margin_start=16, margin_end=16)
        self._attach_child_to_window(win, box)

        sc = Gtk.ScrolledWindow(hexpand=True, vexpand=not is_compact)
        tv = Gtk.TextView(); tv.set_editable(False); tv.set_monospace(monospace)
        tv.set_wrap_mode(Gtk.WrapMode.NONE if wrap_mode=="none" else Gtk.WrapMode.WORD); tv.add_css_class("results-text")
        buf = tv.get_buffer(); buf.set_text(content); sc.set_child(tv); box.append(sc)

        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8); hb.set_halign(Gtk.Align.END)
        if copy_enabled:
            cp = Gtk.Button(label="Copy")
            def do_copy(_b):
                start = buf.get_start_iter(); end = buf.get_end_iter()
                txt = buf.get_text(start, end, True); Gdk.Display.get_default().get_clipboard().set_text(txt)
            cp.connect("clicked", do_copy); hb.append(cp)
        close = Gtk.Button(label="Close"); close.connect("clicked", lambda _b: win.destroy()); hb.append(close)
        box.append(hb); win.present()

    def show_error_window(self, msg: str):
        width = max(40, len(msg) + 10)
        self.show_text_window("Error", msg, copy_enabled=True, width_chars=width, wrap_mode="word", monospace=True)

    # ----- DB actions (create/load/import) — same as v2
    def create_new_database(self, _b):
        win = (Adw.ApplicationWindow if USE_ADW else Gtk.ApplicationWindow)(title="Select Race Type", application=self)
        self._remember_window(win); win.set_resizable(False)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=16, margin_bottom=16, margin_start=16, margin_end=16)
        self._attach_child_to_window(win, box)

        box.append(Gtk.Label(label="Select race type"))
        cc = Gtk.Button(label="Cross Country"); rr = Gtk.Button(label="Road Race")
        tri = Gtk.Button(label="Triathlon (coming soon)"); tri.set_sensitive(False)
        for b in (cc, rr, tri): box.append(b)

        def pick(k): self.race_type = k; win.destroy(); GLib.idle_add(self.create_database_details)
        cc.connect("clicked", lambda *_: pick("cross_country"))
        rr.connect("clicked", lambda *_: pick("road_race"))
        win.present()

    def create_database_details(self):
        win = (Adw.ApplicationWindow if USE_ADW else Gtk.ApplicationWindow)(title="Create New Race Database", application=self)
        self._remember_window(win); win.set_resizable(False)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=16, margin_bottom=16, margin_start=16, margin_end=16)
        self._attach_child_to_window(win, box)

        blurb = Gtk.Label(label=f"Creating: {self.race_type.replace('_',' ').title()} Race"); box.append(blurb)
        race_num = Gtk.Entry(); race_num.set_placeholder_text("Race Number (e.g., 01)")
        race_name = Gtk.Entry(); race_name.set_placeholder_text("Race Name (e.g., County_Meet)")
        box.append(race_num); box.append(race_name)

        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10); hb.set_halign(Gtk.Align.END)
        cancel = Gtk.Button(label="Cancel"); create = Gtk.Button(label="Create")
        hb.append(cancel); hb.append(create); box.append(hb)

        def cancel_it(_): win.destroy()

        def normalize_race_name(name: str) -> str:
            nice = name.replace('_', ' ').strip()
            nice = ' '.join(w.capitalize() for w in nice.split())
            nice = nice.replace(' ', '_')
            keep = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
            return ''.join(ch for ch in nice if ch in keep) or "Race"

        def build_db_filename(race_type: str, num: str, rname: str) -> str:
            suffix_map = {"cross_country":"cc", "road_race":"rr", "tri":"tri"}
            suffix = suffix_map.get(race_type, "race")
            today = datetime.datetime.now().strftime('%Y%m%d')
            return f"{today}-{num}-{suffix}-{normalize_race_name(rname)}.db"

        def do_create(_):
            num = race_num.get_text().strip().zfill(2)
            name = race_name.get_text().strip()
            if not num or num == "00" or not name:
                self.show_error_window("Please enter both a valid race number and race name."); return
            DB_SAVE_DIR.mkdir(parents=True, exist_ok=True)
            db_name = build_db_filename(self.race_type, num, name)
            self.db_path = str((DB_SAVE_DIR / db_name).resolve())

            try:
                self.conn = sqlite3.connect(self.db_path)
                c = self.conn.cursor()
                c.execute("CREATE TABLE IF NOT EXISTS race_type (type TEXT)")
                c.execute("DELETE FROM race_type"); c.execute("INSERT INTO race_type (type) VALUES (?)", (self.race_type,))
                if self.race_type == "cross_country":
                    c.execute("""CREATE TABLE IF NOT EXISTS runners (
                                    bib INTEGER PRIMARY KEY,
                                    name TEXT, team TEXT, age INTEGER, grade TEXT, rfid TEXT)""")
                else:
                    c.execute("""CREATE TABLE IF NOT EXISTS runners (
                                    bib INTEGER PRIMARY KEY,
                                    name TEXT, dob TEXT, age INTEGER, rfid TEXT)""")
                c.execute("""CREATE TABLE IF NOT EXISTS results (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                bib INTEGER, finish_time REAL, race_date TEXT)""")
                self.conn.commit()
                disp = os.path.basename(self.db_path)
                self.set_duoline_status(f"Loaded: {disp} [{self.race_type}]")
                self.set_window_title(f"{disp} [{self.race_type}]")
                self.append_console(f"Database created: {self.db_path}\n")
                win.destroy()
                self.update_button_states()
            except sqlite3.Error as e:
                self.show_error_window(f"Database error: {e}")

        cancel.connect("clicked", cancel_it)
        create.connect("clicked", do_create)
        win.present()

    def load_existing_database(self, _b):
        def accept(path: str): self.load_database(path)
        self.open_themed_file_picker("Load Existing Database", ["*.db"], DB_SAVE_DIR, on_accept=accept)

    def load_database(self, db_path: str):
        try:
            if self.conn: self.conn.close()
            self.db_path = db_path; self.conn = sqlite3.connect(self.db_path)
            try:
                row = self.conn.execute("SELECT type FROM race_type").fetchone()
                self.race_type = row[0] if row else "unknown"
            except Exception:
                self.race_type = "unknown"
            disp = os.path.basename(self.db_path)
            self.set_duoline_status(f"Loaded: {disp} [{self.race_type}]")
            self.set_window_title(f"{disp} [{self.race_type}]")
            self.append_console(f"Loaded database: {self.db_path}\n")
            self.update_button_states()
        except sqlite3.Error as e:
            self.show_error_window(f"Database error: {e}")

    def load_csv_to_database(self, _b):
        if not self.conn:
            self.show_error_window("No database loaded. Create or load a database first."); return
        def accept(path: str): self.process_csv_file(path)
        start_dir = IMPORTS_DIR if INTEGRATION["integrated"] else (TRMS_ROOT/"data")
        self.open_themed_file_picker("Select Runner CSV File", ["*.csv"], start_dir, on_accept=accept)

    def process_csv_file(self, file_path: str):
        try:
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f); rows = list(reader)
            rows_processed = 0
            if self.race_type == "cross_country":
                expected = ['bib', 'name', 'team', 'age', 'grade', 'rfid']
                if reader.fieldnames != expected:
                    self.show_error_window(f"CSV must have columns: {expected}"); return
                for r in rows:
                    self.conn.execute("""INSERT OR REPLACE INTO runners (bib, name, team, age, grade, rfid)
                                         VALUES (?, ?, ?, ?, ?, ?)""",
                                      (r['bib'], r['name'], r['team'], r['age'], r['grade'], r['rfid']))
                    rows_processed += 1
            else:
                expected = ['bib', 'name', 'dob', 'rfid']
                if reader.fieldnames != expected:
                    self.show_error_window(f"CSV must have columns: {expected}"); return
                for r in rows:
                    try:
                        birth = datetime.datetime.strptime(r['dob'], "%Y-%m-%d")
                        age = int((datetime.datetime.now() - birth).days // 365.25)
                    except Exception:
                        age = None
                    self.conn.execute("""INSERT OR REPLACE INTO runners (bib, name, dob, age, rfid)
                                         VALUES (?, ?, ?, ?, ?)""",
                                      (r['bib'], r['name'], r['dob'], age, r['rfid']))
                    rows_processed += 1
            self.conn.commit()
            self.append_console(f"Imported {rows_processed} runners from {file_path}\n")
            self.update_button_states()
            self.show_text_window("CSV Import", f"Successfully imported {rows_processed} runners.", copy_enabled=True, width_chars=40, wrap_mode="word", monospace=True, base_size=(420, 180))
        except Exception as e:
            self.show_error_window(f"Error processing CSV file: {e}")

    # ----- Results
    def show_dynamic_results(self, _b=None):
        if self.race_type == "cross_country": self.show_team_results()
        elif self.race_type == "road_race": self.show_age_group_results()
        else: self.show_error_window("Race type not known. Load a valid race database.")

    def view_all_runners(self, _b=None):
        if not self.conn:
            self.show_text_window("All Runners", "No database loaded.", copy_enabled=True, width_chars=40, wrap_mode="none", monospace=True); return
        try:
            if self.race_type == "cross_country":
                rows = self.conn.execute("SELECT bib, name, team, age, grade FROM runners ORDER BY bib").fetchall()
                header_cols = f"{'BIB':<8}{'NAME':<25}{'TEAM':<20}{'AGE':<5}{'GRADE'}"
            else:
                rows = self.conn.execute("SELECT bib, name, dob, age FROM runners ORDER BY bib").fetchall()
                header_cols = f"{'BIB':<8}{'NAME':<30}{'DOB':<12}{'AGE'}"
        except sqlite3.Error as e:
            self.show_error_window(f"Database error: {e}"); return

        if not rows:
            self.show_text_window("All Runners", "No runners loaded. Please load a CSV file.", copy_enabled=True, width_chars=40, wrap_mode="none", monospace=True); return

        title_line = "ALL REGISTERED RUNNERS"
        header_len = max(len(title_line), len(header_cols)) + 10
        output = f"{title_line}\n{'='*header_len}\n{header_cols}\n{'-'*len(header_cols)}\n"
        if self.race_type == "cross_country":
            for bib, name, team, age, grade in rows:
                output += f"{bib:<8}{(name or '')[:24]:<25}{(team or '')[:19]:<20}{str(age or ''):<5}{grade or ''}\n"
        else:
            for bib, name, dob, age in rows:
                output += f"{bib:<8}{(name or '')[:29]:<30}{(dob or ''):<12}{str(age or '')}\n"
        self.show_text_window("All Runners", output, copy_enabled=True, width_chars=header_len, wrap_mode="none", monospace=True)

    def show_individual_results(self, _b=None):
        if not self.conn:
            self.show_text_window("Individual Results", "No database loaded.", copy_enabled=True, width_chars=40, wrap_mode="none", monospace=True); return
        try:
            rows = self.conn.execute("""
                SELECT results.bib, COALESCE(runners.name,'UNKNOWN'), results.finish_time
                FROM results LEFT JOIN runners ON results.bib = runners.bib
                WHERE results.finish_time IS NOT NULL
                ORDER BY results.finish_time ASC
            """).fetchall()
        except sqlite3.Error as e:
            self.show_error_window(f"Database error: {e}"); return
        if not rows:
            self.show_text_window("Individual Results", "No race results found.", copy_enabled=True, width_chars=40, wrap_mode="none", monospace=True); return

        title_line = "INDIVIDUAL RACE RESULTS"
        table_header = f"{'POS':<5}{'BIB':<8}{'NAME':<25}{'TIME':<12}"
        header_len = max(len(title_line), len(table_header)) + 10
        output = f"{title_line}\n{'='*header_len}\n{table_header}\n{'-'*len(table_header)}\n"
        for pos, (bib, name, t) in enumerate(rows, 1):
            output += f"{pos:<5}{bib:<8}{(name or 'UNKNOWN')[:24]:<25}{self.format_time(t):<12}\n"
        self.show_text_window("Individual Results", output, copy_enabled=True, width_chars=header_len, wrap_mode="none", monospace=True)

    def show_team_results(self, _b=None):
        if not self.conn:
            self.show_text_window("Team Results", "No database loaded.", copy_enabled=True, width_chars=40, wrap_mode="none", monospace=True); return
        if self.race_type != "cross_country":
            self.show_error_window("Team results are only available for cross country races."); return
        try:
            rows = self.conn.execute("""
                SELECT COALESCE(runners.team,'UNKNOWN'), results.bib, runners.name, results.finish_time
                FROM results LEFT JOIN runners ON results.bib = runners.bib
                WHERE results.finish_time IS NOT NULL
                ORDER BY results.finish_time ASC
            """).fetchall()
        except sqlite3.Error as e:
            self.show_error_window(f"Database error: {e}"); return
        if not rows:
            self.show_text_window("Team Results", "No race results found.", copy_enabled=True, width_chars=40, wrap_mode="none", monospace=True); return

        title_line = "CROSS COUNTRY TEAM RESULTS"
        header_len = len(title_line) + 10
        output = f"{title_line}\n{'='*header_len}\n\n"
        teams = {}
        for place, (team, bib, name, t) in enumerate(rows, 1):
            teams.setdefault(team, []).append((place, bib, name, t))

        scores = []
        for team, runners in teams.items():
            if len(runners) >= 5:
                top5 = runners[:5]
                displacers = runners[5:7]
                score = sum(p for (p, _, _, _) in top5)
                tb = [p for (p, _, _, _) in displacers] + [float('inf'), float('inf')]
                scores.append((team, score, top5, displacers, tb[0], tb[1]))
        scores.sort(key=lambda x: (x[1], x[4], x[5]))

        for rank, (team, score, top5, displacers, _, _) in enumerate(scores, 1):
            output += f"Rank {rank} - Team: {team}\nTeam Score = {score}\nTop 5:\n"
            for place, bib, name, t in top5:
                output += f"  Place {place}, Bib {bib}, {name}, {self.format_time(t)}\n"
            if displacers:
                output += "Displacers:\n"
                for place, bib, name, t in displacers:
                    output += f"  Place {place}, Bib {bib}, {name}, {self.format_time(t)}\n"
            output += "\n"

        self.show_text_window("Team Results", output, copy_enabled=True, width_chars=header_len, wrap_mode="none", monospace=True)

    def show_age_group_results(self, _b=None):
        if not self.conn:
            self.show_text_window("Age Group Results", "No database loaded.", copy_enabled=True, width_chars=40, wrap_mode="none", monospace=True); return
        if self.race_type != "road_race":
            self.show_error_window("Age group results are only available for road races."); return
        try:
            rows = self.conn.execute("""
                SELECT runners.age, runners.bib, runners.name, results.finish_time
                FROM results LEFT JOIN runners ON results.bib = runners.bib
                WHERE results.finish_time IS NOT NULL
                ORDER BY results.finish_time ASC
            """).fetchall()
        except sqlite3.Error as e:
            self.show_error_window(f"Database error: {e}"); return
        if not rows:
            self.show_text_window("Age Group Results", "No race results found.", copy_enabled=True, width_chars=40, wrap_mode="none", monospace=True); return

        title_line = "ROAD RACE AGE GROUP RESULTS"
        table_header = f"{'PLACE':<8}{'BIB':<8}{'NAME':<25}{'TIME'}"
        header_len = max(len(title_line), len(table_header)) + 10
        output = f"{title_line}\n{'='*header_len}\n\n"

        age_groups = [(1,15),(16,20),(21,25),(26,30),(31,35),(36,40),(41,45),(46,50),(51,55),(56,60),(61,65),(66,70),(71,200)]
        results_by_group = {f"{low}-{high}": [] for (low, high) in age_groups}
        overall_place = 0
        for (age, bib, name, t) in rows:
            overall_place += 1
            try:
                age_i = int(age)
            except Exception:
                continue
            for (low, high) in age_groups:
                if low <= age_i <= high:
                    results_by_group[f"{low}-{high}"].append((overall_place, bib, name, t))
                    break

        for group, lst in results_by_group.items():
            if not lst: continue
            output += f"Age Group {group}\n{table_header}\n{'-'*len(table_header)}\n"
            for i, (place, bib, name, t) in enumerate(lst, 1):
                output += f"{i:<8}{bib:<8}{(name or 'UNKNOWN')[:24]:<25}{self.format_time(t)}\n"
            output += "\n"

        self.show_text_window("Age Group Results", output, copy_enabled=True, width_chars=header_len, wrap_mode="none", monospace=True)

    def show_instructions(self, _b=None):
        choose_line = "   • Choose race type: Cross Country, Road Race, or Triathlon (coming soon)"
        header_len = len(choose_line) + 10
        txt = f"""THE RACE TIMING SOLUTION (TRTS) - GUI VERSION
{'='*header_len}

GETTING STARTED:
1. Create New Database
{choose_line}
   • Enter race number and name
   • Database saved under: {DB_SAVE_DIR}

2. Load Runner Data
   • Click "Load Runners from CSV"
   • Cross Country CSV: bib, name, team, age, grade, rfid
   • Road Race CSV: bib, name, dob, rfid

RACE TIMING:
3. Start Race
   • Click "Start the Race" to open timing window
   • Enter bib numbers as runners finish
   • Type 'exit' to stop timing

RESULTS:
4. View Results
   • Individual Results: all runners by finish time
   • Team Results: cross country team scoring
   • Age Group Results: road race age divisions

NOTES:
• SQLite3 is the active backend; MariaDB/TRDS is visible but disabled
• File pickers and dialogs match the theme
• Menu (☰) → Environment… shows system details
"""
        self.show_text_window("Instructions", txt, copy_enabled=True, width_chars=header_len, wrap_mode="word", monospace=True)

    def on_show_env(self, *_a):
        self.show_environment_info()

    def show_environment_info(self):
        try:
            gtk_ver = f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
        except Exception:
            gtk_ver = "unknown"
        adw_ver = "unavailable"
        if USE_ADW:
            try:
                adw_ver = f"{Adw.get_major_version()}.{Adw.get_minor_version()}.{Adw.get_micro_version()}"
            except Exception:
                pass
        sess = os.environ.get("XDG_SESSION_TYPE", "unknown")
        wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
        x11_display = os.environ.get("DISPLAY", "")
        py_ver = platform.python_version()
        plat = platform.platform()

        lines = [
            f"Python:            {py_ver}",
            f"Platform:          {plat}",
            f"GTK:               {gtk_ver}",
            f"libadwaita:        {adw_ver}",
            "",
            f"Session:           {sess}",
            f"WAYLAND_DISPLAY:   {wayland_display or '—'}",
            f"DISPLAY:           {x11_display or '—'}",
            "",
            f"Integration:       {INTEGRATION['status_label']}",
            f"TRMS root:         {TRMS_ROOT}",
            f"TRDS root:         {INTEGRATION['trds_root'] or '—'}",
            f"SQLite dir:        {DB_SAVE_DIR}",
            f"Imports dir:       {IMPORTS_DIR}",
            f"MySQL dir:         {MYSQL_DIR or '—'}",
        ]
        longest = max(len("ENVIRONMENT"), *(len(s) for s in lines))
        header = "=" * (longest + 10)
        content = "ENVIRONMENT\n" + header + "\n" + "\n".join(lines) + "\n"
        self.show_text_window("Environment", content, copy_enabled=True, width_chars=(longest+10), wrap_mode="none", monospace=True)

    def start_race(self, _b=None):
        if not self.conn:
            self.show_error_window("No database loaded. Create or load a database first."); return
        race_start_time = datetime.datetime.now()
        race_date = race_start_time.strftime('%Y-%m-%d')
        self.open_race_timing_window(race_start_time, race_date)

    def open_race_timing_window(self, start_time, race_date):
        win = (Adw.ApplicationWindow if USE_ADW else Gtk.ApplicationWindow)(title="Race Timing — IN PROGRESS", application=self)
        self._remember_window(win); win.set_default_size(780, 560)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=16, margin_bottom=16, margin_start=16, margin_end=16)
        self._attach_child_to_window(win, box)

        timer_label = Gtk.Label(); timer_label.set_markup("<span size='24000' weight='bold'>00:00:00</span>")
        box.append(timer_label)
        start_label = Gtk.Label(label=f"Race started: {start_time.strftime('%H:%M:%S')}"); box.append(start_label)
        box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        instructions = Gtk.Label()
        instructions.set_markup("<b>Instructions:</b>\n• Enter bib number and press Enter to record finish\n• Type 'exit' and press Enter to stop timing")
        instructions.set_justify(Gtk.Justification.LEFT); box.append(instructions)

        bib_entry = Gtk.Entry(placeholder_text="Enter bib number or 'exit'"); box.append(bib_entry)

        sc = Gtk.ScrolledWindow(hexpand=True, vexpand=not is_compact)
        tv = Gtk.TextView(); tv.set_editable(False); tv.set_wrap_mode(Gtk.WrapMode.WORD)
        buf = tv.get_buffer(); buf.set_text("Finish times will appear here...\n")
        sc.set_child(tv); box.append(sc)

        finish_count = 0
        def update_timer():
            elapsed = datetime.datetime.now() - start_time
            s = int(elapsed.total_seconds()); h = s//3600; m=(s%3600)//60; sec=s%60
            timer_label.set_markup(f"<span size='24000' weight='bold'>{h:02d}:{m:02d}:{sec:02d}</span>"); return True
        timer_id = GLib.timeout_add(1000, update_timer)

        def on_enter(entry):
            nonlocal finish_count
            t = entry.get_text().strip(); entry.set_text("")
            if t.lower() == "exit":
                GLib.source_remove(timer_id); win.destroy(); self.update_button_states(); return
            try: bib = int(t)
            except ValueError: bib = 0
            elapsed_seconds = (datetime.datetime.now() - start_time).total_seconds()
            finish_count += 1
            try:
                self.conn.execute('INSERT INTO results (bib, finish_time, race_date) VALUES (?, ?, ?)', (bib, elapsed_seconds, race_date))
                self.conn.commit()
                line = f"{finish_count:3d}. Bib {bib:3d} - {self.format_time(elapsed_seconds)}\n"
                end = buf.get_end_iter(); buf.insert(end, line); tv.scroll_mark_onscreen(buf.get_insert())
            except sqlite3.Error as e:
                self.append_console(f"DB error (timing insert): {e}\n")

        bib_entry.connect("activate", on_enter)
        win.connect("close-request", lambda *a: (GLib.source_remove(timer_id), self.update_button_states(), False))
        win.present(); bib_entry.grab_focus()

    def update_button_states(self):
        has_db = self.conn is not None
        has_results = False
        if has_db:
            try:
                result_count = self.conn.execute("SELECT COUNT(*) FROM results WHERE finish_time IS NOT NULL").fetchone()[0]
                has_results = result_count > 0
            except sqlite3.Error:
                pass
        if self.dynamic_results_button:
            if self.race_type == "cross_country":
                self.dynamic_results_button.set_label("Show Team Results")
                self.dynamic_results_button.set_sensitive(has_results)
            elif self.race_type == "road_race":
                self.dynamic_results_button.set_label("Show Age Group Results")
                self.dynamic_results_button.set_sensitive(has_results)
            else:
                self.dynamic_results_button.set_label("Show Results (Load database first)")
                self.dynamic_results_button.set_sensitive(False)
        # Toggle Individual Results button sensitivity based on presence of results
        if getattr(self, "individual_results_button", None):
            self.individual_results_button.set_sensitive(has_results)

    def format_time(self, total_seconds):
        if total_seconds is None: return "00:00.000"
        minutes, seconds = divmod(total_seconds, 60)
        return f"{int(minutes):02d}:{seconds:06.3f}"

def main():
    print('DEBUG: entering main()')
    app = RaceTimingApp()
    try:
        app.connect('activate', lambda *a: print('DEBUG: GApplication activate signal'))
    except Exception as e:
        print('DEBUG: connect(activate) failed:', e)
    rc = app.run(None)
    print('DEBUG: app.run() returned', rc)

print(f"DEBUG: __name__ = {__name__}")
if __name__ == "__main__":
    print("DEBUG: __main__ guard matched")
    main()
elif os.environ.get("TRTS_AUTO_START") == "1":
    print("DEBUG: TRTS_AUTO_START=1 -> starting anyway")
    main()
