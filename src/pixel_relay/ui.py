"""Tkinter configuration and control interface."""

from __future__ import annotations

import queue
import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from .config import DEFAULT_CONFIG, load_saved_config, save_config
from .monitor import DashboardMonitor

class PixelRelayApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pixel Relay by JECaballeroR")
        self.geometry("920x860")
        self.minsize(840, 740)
        self.configure(bg="#000000")

        self.saved_config = load_saved_config()
        self.log_queue: queue.Queue = queue.Queue()
        self.config_queue: queue.Queue = queue.Queue()
        self.command_queue: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread: threading.Thread | None = None
        self.monitor: DashboardMonitor | None = None

        self.variables: dict[str, tk.Variable] = {}

        self._configure_dark_style()
        self._build_ui()
        self.after(150, self._process_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_dark_style(self):
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            ".",
            background="#000000",
            foreground="#ffffff",
            fieldbackground="#111111",
            bordercolor="#333333",
            lightcolor="#333333",
            darkcolor="#000000",
            troughcolor="#111111",
            font=("Segoe UI", 10),
        )
        style.configure(
            "TFrame",
            background="#000000",
        )
        style.configure(
            "TLabel",
            background="#000000",
            foreground="#ffffff",
        )
        style.configure(
            "TCheckbutton",
            background="#000000",
            foreground="#ffffff",
        )
        style.map(
            "TCheckbutton",
            background=[("active", "#000000")],
            foreground=[("active", "#ffffff")],
        )
        style.configure(
            "TNotebook",
            background="#000000",
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background="#161616",
            foreground="#d6d6d6",
            padding=(12, 7),
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", "#1388e9"),
                ("active", "#252525"),
            ],
            foreground=[("selected", "#ffffff")],
        )
        style.configure(
            "TEntry",
            fieldbackground="#111111",
            foreground="#ffffff",
            insertcolor="#ffffff",
        )
        style.configure(
            "TButton",
            background="#161616",
            foreground="#ffffff",
            padding=(12, 7),
        )
        style.map(
            "TButton",
            background=[
                ("active", "#252525"),
                ("pressed", "#1388e9"),
            ],
        )

    def _var(self, name: str, kind: str = "str"):
        value = self.saved_config.get(name, DEFAULT_CONFIG[name])

        if kind == "bool":
            variable = tk.BooleanVar(value=bool(value))
        elif kind == "int":
            variable = tk.IntVar(value=int(value))
        elif kind == "float":
            variable = tk.DoubleVar(value=float(value))
        else:
            variable = tk.StringVar(value=str(value))

        self.variables[name] = variable
        return variable

    def _add_entry(
        self,
        parent,
        row: int,
        label: str,
        name: str,
        kind: str = "str",
        width: int = 30,
    ):
        ttk.Label(parent, text=label).grid(
            row=row,
            column=0,
            sticky="w",
            padx=8,
            pady=6,
        )

        entry = ttk.Entry(
            parent,
            textvariable=self._var(name, kind),
            width=width,
        )
        entry.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=8,
            pady=6,
        )

        return entry

    def _add_check(
        self,
        parent,
        row: int,
        text: str,
        name: str,
    ):
        checkbox = ttk.Checkbutton(
            parent,
            text=text,
            variable=self._var(name, "bool"),
        )
        checkbox.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=6,
        )
        return checkbox

    def _module_switch(self, parent, name: str):
        frame = ttk.Frame(parent)
        frame.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=8,
            pady=(3, 12),
        )
        ttk.Checkbutton(
            frame,
            text="Enable this module",
            variable=self._var(name, "bool"),
        ).pack(anchor="w")

    def _build_ui(self):
        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Pixel Relay",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            container,
            text="by JECaballeroR",
            foreground="#8294aa",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 2))

        ttk.Label(
            container,
            text=(
                "The app uses the stock Picture album API to select music "
                "immediately and can optionally pause autoplay before returning "
                "to the other enabled modules."
            ),
            foreground="#b8b8b8",
        ).pack(anchor="w", pady=(2, 10))

        notebook = ttk.Notebook(container)
        notebook.pack(fill="x", expand=False)

        # Device
        device_tab = ttk.Frame(notebook, padding=10)
        device_tab.columnconfigure(1, weight=1)
        notebook.add(device_tab, text="Device")

        self._add_entry(
            device_tab, 0, "IP GeekMagic", "device_ip"
        )
        self._add_entry(
            device_tab, 1, "Timeout HTTP", "request_timeout", "int"
        )
        self._add_check(
            device_tab,
            2,
            "Exclusive album control (recommended)",
            "clear_unknown_files",
        )

        ttk.Label(
            device_tab,
            text=(
                "Exclusive control only manages which dashboard files remain "
                "in the album. Music selection now uses album_path directly "
                "and does not rebuild the gallery."
            ),
            foreground="#9a9a9a",
            wraplength=600,
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=(8, 3),
        )

        # Rotation controls
        control_tab = ttk.Frame(notebook, padding=10)
        control_tab.columnconfigure(1, weight=1)
        notebook.add(control_tab, text="Control")

        self._add_check(
            control_tab,
            0,
            "Enable automatic rotation",
            "auto_rotation_enabled",
        )
        self._add_entry(
            control_tab,
            1,
            "Seconds per image",
            "rotation_seconds",
            "int",
        )
        self._add_check(
            control_tab,
            2,
            "Show music when playback starts or the track changes",
            "music_focus_on_change",
        )
        self._add_check(
            control_tab,
            3,
            "Pause autoplay while music is focused",
            "music_pause_autoplay_on_focus",
        )
        self._add_entry(
            control_tab,
            4,
            "Delay after music upload (s)",
            "music_selection_delay_seconds",
            "float",
        )
        self._add_entry(
            control_tab,
            5,
            "Music focus duration (s)",
            "music_focus_seconds",
            "int",
        )
        self._add_check(
            control_tab,
            6,
            "Keep rotating while music is playing",
            "rotate_while_playing",
        )

        control_buttons = ttk.Frame(control_tab)
        control_buttons.grid(
            row=7,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=(12, 6),
        )

        ttk.Button(
            control_buttons,
            text="Resume rotation",
            command=lambda: self.send_monitor_command("resume_rotation"),
        ).pack(side="left", padx=(0, 7))
        ttk.Button(
            control_buttons,
            text="Pause rotation",
            command=lambda: self.send_monitor_command("pause_rotation"),
        ).pack(side="left", padx=(0, 7))
        ttk.Button(
            control_buttons,
            text="Show music now",
            command=lambda: self.send_monitor_command("focus_music"),
        ).pack(side="left", padx=(0, 7))
        ttk.Button(
            control_buttons,
            text="Follow saved settings",
            command=lambda: self.send_monitor_command("follow_config"),
        ).pack(side="left")

        ttk.Button(
            control_tab,
            text="Rebuild gallery",
            command=lambda: self.send_monitor_command("rebuild_gallery"),
        ).grid(
            row=8,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=(4, 8),
        )

        ttk.Label(
            control_tab,
            text=(
                "Music is selected with album_path only. With pause-on-focus "
                "enabled, the same request includes album_autoplay=0. No app "
                "switch or immediate second pause request is sent. i_i is used "
                "when rotation resumes."
            ),
            foreground="#9a9a9a",
            wraplength=680,
        ).grid(
            row=9,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=(8, 3),
        )

        # Music
        music_tab = ttk.Frame(notebook, padding=10)
        music_tab.columnconfigure(1, weight=1)
        notebook.add(music_tab, text="Music")

        self._module_switch(music_tab, "music_enabled")
        self._add_entry(
            music_tab, 1, "Windows polling interval (s)", "poll_seconds", "float"
        )
        self._add_entry(
            music_tab, 2, "Font scale", "font_scale", "float"
        )

        ttk.Label(
            music_tab,
            text=(
                "Music uses a static JPG with title, artist, album, total "
                "duration, and source. It has no progress animation and is "
                "replaced only when the track changes or the gallery is rebuilt."
            ),
            foreground="#9a9a9a",
            wraplength=600,
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=(8, 3),
        )

        # USD/COP
        fx_tab = ttk.Frame(notebook, padding=10)
        fx_tab.columnconfigure(1, weight=1)
        notebook.add(fx_tab, text="Exchange Rate")

        self._module_switch(fx_tab, "fx_enabled")
        self._add_entry(
            fx_tab, 1, "Yahoo symbol", "yahoo_symbol"
        )
        self._add_entry(
            fx_tab, 2, "Refresh interval (s)", "fx_refresh_seconds", "int"
        )
        self._add_entry(
            fx_tab,
            3,
            "Daily closes",
            "fx_history_days",
            "int",
        )
        self._add_check(
            fx_tab,
            4,
            "Show daily-close trend",
            "show_fx_plot",
        )

        # Weather
        weather_tab = ttk.Frame(notebook, padding=10)
        weather_tab.columnconfigure(1, weight=1)
        notebook.add(weather_tab, text="Weather")

        self._module_switch(weather_tab, "weather_enabled")
        self._add_entry(
            weather_tab, 1, "City", "weather_city"
        )
        self._add_entry(
            weather_tab, 2, "Country code", "weather_country_code"
        )
        self._add_entry(
            weather_tab,
            3,
            "Refresh interval (s)",
            "weather_refresh_seconds",
            "int",
        )
        ttk.Label(
            weather_tab,
            text=(
                "Source: Open-Meteo. No browser or API key is required."
            ),
            foreground="#9a9a9a",
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=(8, 3),
        )

        # Calendar
        calendar_tab = ttk.Frame(
            notebook,
            padding=10,
        )
        calendar_tab.columnconfigure(
            1,
            weight=1,
        )
        notebook.add(
            calendar_tab,
            text="Calendar",
        )

        self._module_switch(
            calendar_tab,
            "calendar_enabled",
        )
        self._add_entry(
            calendar_tab,
            1,
            "Private ICS URL",
            "calendar_ics_url",
            width=52,
        )
        self._add_entry(
            calendar_tab,
            2,
            "Refresh interval (s)",
            "calendar_refresh_seconds",
            "int",
        )
        self._add_entry(
            calendar_tab,
            3,
            "Look-ahead days",
            "calendar_days_ahead",
            "int",
        )

        ttk.Label(
            calendar_tab,
            text=(
                "Shows the nearest strictly future timed event. "
                "The private URL is stored only in the local config.json file."
            ),
            foreground="#9a9a9a",
            wraplength=620,
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=(8, 3),
        )

        # Clock
        clock_tab = ttk.Frame(notebook, padding=10)
        clock_tab.columnconfigure(1, weight=1)
        notebook.add(clock_tab, text="Clock")

        self._module_switch(clock_tab, "clock_enabled")
        self._add_check(
            clock_tab,
            1,
            "24-hour format",
            "clock_24h",
        )

        ttk.Label(
            clock_tab,
            text=(
                "The clock shows hours and minutes only. "
                "It updates automatically when the minute changes."
            ),
            foreground="#9a9a9a",
            wraplength=520,
        ).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=(10, 4),
        )

        # Personalizado
        custom_tab = ttk.Frame(notebook, padding=10)
        custom_tab.columnconfigure(1, weight=1)
        notebook.add(custom_tab, text="Notifications")

        self._module_switch(custom_tab, "custom_enabled")
        self._add_entry(
            custom_tab, 1, "Title", "custom_title"
        )

        ttk.Label(custom_tab, text="Message").grid(
            row=2,
            column=0,
            sticky="nw",
            padx=8,
            pady=6,
        )

        self.custom_body_text = tk.Text(
            custom_tab,
            height=5,
            width=44,
            wrap="word",
            bg="#111111",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#1388e9",
            relief="flat",
        )
        self.custom_body_text.grid(
            row=2,
            column=1,
            sticky="ew",
            padx=8,
            pady=6,
        )
        self.custom_body_text.insert(
            "1.0",
            str(self.saved_config.get("custom_body", "")),
        )

        self._add_entry(
            custom_tab, 3, "Pie", "custom_footer"
        )
        self._add_entry(
            custom_tab, 4, "HEX color", "custom_accent"
        )

        button_frame = ttk.Frame(container)
        button_frame.pack(fill="x", pady=(12, 8))

        self.start_button = ttk.Button(
            button_frame,
            text="Start",
            command=self.start_monitor,
        )
        self.start_button.pack(side="left", padx=(0, 8))

        self.stop_button = ttk.Button(
            button_frame,
            text="Stop",
            command=self.stop_monitor,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=(0, 8))

        self.apply_button = ttk.Button(
            button_frame,
            text="Apply and save",
            command=self.apply_current_config,
        )
        self.apply_button.pack(side="left", padx=(0, 8))

        self.status_var = tk.StringVar(value="Detenido")
        ttk.Label(
            container,
            textvariable=self.status_var,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(2, 6))

        self.log_box = scrolledtext.ScrolledText(
            container,
            height=15,
            state="disabled",
            wrap="word",
            font=("Consolas", 9),
            bg="#050505",
            fg="#d6d6d6",
            insertbackground="#ffffff",
            selectbackground="#1388e9",
            relief="flat",
        )
        self.log_box.pack(fill="both", expand=True)

    def get_config(self) -> dict[str, Any]:
        config = {
            name: variable.get()
            for name, variable in self.variables.items()
        }

        config["custom_body"] = self.custom_body_text.get(
            "1.0",
            "end",
        ).strip()

        return config

    def send_monitor_command(self, command: str):
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self._append_log(
                "Start the monitor before using album controls."
            )
            return

        self.command_queue.put((command, None))
        self._append_log(f"Command sent: {command}.")

    def apply_current_config(self):
        try:
            config = self.get_config()
            save_config(config)

            if self.monitor is not None and self.worker_thread is not None:
                if self.worker_thread.is_alive():
                    self.config_queue.put(config)
                    self._append_log(
                        "Changes sent to the monitor. Modules, rotation, and "
                        "music focus will be updated."
                    )
                    return

            self._append_log("Configuration saved.")

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"Could not apply changes:\n{error}",
            )

    def start_monitor(self):
        if self.worker_thread and self.worker_thread.is_alive():
            return

        try:
            config = self.get_config()
            save_config(config)

            if not str(config["device_ip"]).strip():
                raise ValueError("Enter the GeekMagic IP address.")

        except Exception as error:
            messagebox.showerror("Invalid configuration", str(error))
            return

        self.stop_event = threading.Event()
        self.config_queue = queue.Queue()
        self.command_queue = queue.Queue()

        self.monitor = DashboardMonitor(
            config,
            self.stop_event,
            self.log_queue,
            self.config_queue,
            self.command_queue,
        )

        self.worker_thread = threading.Thread(
            target=self.monitor.run,
            name="GeekMagicMonitor",
            daemon=True,
        )
        self.worker_thread.start()

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set("Starting…")
        self._append_log("Starting monitor…")

    def stop_monitor(self):
        self.stop_event.set()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_var.set("Stopping…")

    def _append_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{timestamp}] {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _process_queue(self):
        try:
            while True:
                kind, message = self.log_queue.get_nowait()

                if kind == "status":
                    self.status_var.set(message)

                    if message in {"Detenido", "Error"}:
                        self.start_button.configure(state="normal")
                        self.stop_button.configure(state="disabled")
                else:
                    self._append_log(message)

        except queue.Empty:
            pass

        self.after(150, self._process_queue)

    def _on_close(self):
        self.stop_event.set()

        try:
            save_config(self.get_config())
        except Exception:
            pass

        self.destroy()

def run_gui() -> None:
    app = PixelRelayApp()
    app.mainloop()
