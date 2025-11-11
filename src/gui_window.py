"""
GUI control window for ClickClick auto-clicker application.

Provides a Tkinter-based control panel with:
- Start/Stop toggle button
- Min/Max delay controls (0.1-10.0 seconds)
- Position offset range control (0-50 pixels)
- Hotkey capture (stored in settings)
- Status display and position info
- Always-on-top toggle
- Minimize to status indicator overlay and restore on indicator click
- JSON settings persistence

The GUI window integrates with the main application controller and backend
components via callbacks provided by ClickClickApp.
"""

from __future__ import annotations

import ctypes
import json
import os
import queue
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Any, Callable, Optional, Tuple

try:
    # pynput is optional at runtime; GUI should still function without capture
    from pynput.keyboard import Listener
except Exception:
    Listener = None  # type: ignore


SETTINGS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "settings.json"))

SPACE_4 = 4
SPACE_8 = 8
SPACE_12 = 12
SPACE_16 = 16
MIN_DELAY_SECONDS = 0.1
MAX_DELAY_SECONDS = 10.0
OFFSET_MAX_PX = 50


def hex_lerp(a: str, b: str, t: float) -> str:
    """Interpolate between two hex colors."""
    a = a.lstrip("#")
    b = b.lstrip("#")
    if len(a) != 6 or len(b) != 6:
        return a if t <= 0 else b
    t = max(0.0, min(1.0, t))
    start = tuple(int(a[i : i + 2], 16) for i in range(0, 6, 2))
    end = tuple(int(b[i : i + 2], 16) for i in range(0, 6, 2))
    blended = tuple(int(round(s + (e - s) * t)) for s, e in zip(start, end))
    return "#{:02X}{:02X}{:02X}".format(*blended)


def apply_window_bg(root: tk.Misc, theme: "Theme" | None = None) -> None:
    """Ensure the base Tk window uses the theme background."""
    palette = theme or THEME
    try:
        root.configure(bg=palette.window_bg)
    except Exception:
        pass


@dataclass(frozen=True)
class Theme:
    window_bg: str = "#0f172a"
    card_bg: str = "#111827"
    accent: str = "#2563EB"
    danger: str = "#DC2626"
    secondary_bg: str = "#1f2937"
    highlight: str = "#60A5FA"
    body_text: str = "#E5E7EB"
    strong_text: str = "#F3F4F6"
    muted_text: str = "#9CA3AF"
    pill_idle_bg: str = "#1f2937"
    pill_idle_fg: str = "#F9FAFB"
    font_family: str = "Segoe UI"

    def configure(self, root: tk.Misc, style: ttk.Style) -> None:
        apply_window_bg(root, self)
        try:
            root.option_add("*Font", f"{{{self.font_family}}} 10")
        except tk.TclError:
            pass

        accent_hover = hex_lerp(self.accent, "#FFFFFF", 0.12)
        accent_active = hex_lerp(self.accent, "#000000", 0.2)
        danger_hover = hex_lerp(self.danger, "#FFFFFF", 0.12)
        danger_active = hex_lerp(self.danger, "#000000", 0.2)
        secondary_hover = hex_lerp(self.secondary_bg, "#FFFFFF", 0.08)
        secondary_active = hex_lerp(self.secondary_bg, "#000000", 0.12)

        style.configure("Main.TFrame", background=self.window_bg)
        style.configure("Header.TFrame", background=self.window_bg)
        style.configure("Card.TFrame", background=self.card_bg, relief="flat", borderwidth=0)
        style.configure("CardBody.TFrame", background=self.card_bg)
        style.configure("TSeparator", background=self.secondary_bg)

        heading_font = (self.font_family, 16, "bold")
        card_heading_font = (self.font_family, 12, "bold")
        subtitle_font = (self.font_family, 10)
        strong_font = (self.font_family, 11)
        pill_font = (self.font_family, 9, "bold")

        style.configure("Header.TLabel", background=self.window_bg, foreground="#F9FAFB", font=heading_font)
        style.configure("Subtitle.TLabel", background=self.window_bg, foreground=self.muted_text, font=subtitle_font)
        style.configure("CardHeading.TLabel", background=self.card_bg, foreground="#F9FAFB", font=card_heading_font)
        style.configure("Body.TLabel", background=self.card_bg, foreground=self.body_text, font=subtitle_font)
        style.configure("Muted.TLabel", background=self.card_bg, foreground=self.muted_text, font=subtitle_font)
        style.configure("Strong.TLabel", background=self.card_bg, foreground=self.strong_text, font=strong_font)
        style.configure("Meta.TLabel", background=self.card_bg, foreground=self.highlight, font=(self.font_family, 9))
        style.configure("Error.TLabel", background=self.card_bg, foreground="#F87171", font=(self.font_family, 9))
        style.configure("StatusActive.TLabel", background=self.card_bg, foreground="#34D399", font=(self.font_family, 11, "bold"))
        style.configure("StatusInactive.TLabel", background=self.card_bg, foreground="#F87171", font=(self.font_family, 11, "bold"))
        style.configure(
            "Pill.TLabel",
            background=self.pill_idle_bg,
            foreground=self.pill_idle_fg,
            font=pill_font,
            padding=(SPACE_8, SPACE_4),
        )

        button_padding = (SPACE_16, SPACE_8)
        style.configure(
            "Primary.TButton",
            background=self.accent,
            foreground="#F9FAFB",
            font=(self.font_family, 10, "bold"),
            padding=button_padding,
        )
        style.map(
            "Primary.TButton",
            background=[("active", accent_hover), ("pressed", accent_active)],
            foreground=[("disabled", self.muted_text)],
        )
        style.configure(
            "Danger.TButton",
            background=self.danger,
            foreground="#F9FAFB",
            font=(self.font_family, 10, "bold"),
            padding=button_padding,
        )
        style.map(
            "Danger.TButton",
            background=[("active", danger_hover), ("pressed", danger_active)],
            foreground=[("disabled", "#FECACA")],
        )
        style.configure(
            "Secondary.TButton",
            background=self.secondary_bg,
            foreground=self.body_text,
            font=(self.font_family, 10),
            padding=button_padding,
        )
        style.map(
            "Secondary.TButton",
            background=[("active", secondary_hover), ("pressed", secondary_active)],
            foreground=[("disabled", self.muted_text)],
        )

        style.configure("Toggle.TCheckbutton", background=self.card_bg, foreground=self.body_text, font=(self.font_family, 10))
        style.map("Toggle.TCheckbutton", foreground=[("disabled", self.muted_text)])

        spinbox_layout = style.layout("TSpinbox")
        if spinbox_layout:
            style.layout("Input.Spinbox", spinbox_layout)
        style.configure(
            "Input.Spinbox",
            background=self.card_bg,
            foreground="#F9FAFB",
            fieldbackground=self.secondary_bg,
            arrowsize=12,
        )
        style.configure(
            "ValidationError.TFrame",
            background="#7F1D1D",
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "ValidationError.TLabel",
            background="#7F1D1D",
            foreground="#FEE2E2",
            font=(self.font_family, 10, "bold"),
        )


THEME = Theme()


class GUIWindow:
    """
    Tkinter Toplevel window providing controls for ClickClick.

    Args:
        app: ClickClickApp instance used for coordination
        parent_root: tk.Tk root to attach the window to (recommended)
    """

    def __init__(self, app, parent_root: Optional[tk.Tk] = None) -> None:
        self.app = app
        self.parent_root = parent_root

        self._configure_dpi_awareness()

        # Create the window attached to the shared root if provided
        if self.parent_root is not None:
            self.window: tk.Toplevel = tk.Toplevel(self.parent_root)
        else:
            self.window = tk.Tk()

        self._configure_tk_scaling()

        # Basic window configuration
        self.window.title("ClickClick Auto-Clicker")
        try:
            # Extra vertical space prevents bottom controls from clipping on some displays
            self.window.geometry("520x800")
            self.window.minsize(520, 800)
        except Exception:
            pass
        try:
            self.window.resizable(False, False)
        except Exception:
            pass

        # Widgets and style references (assigned during layout build)
        self.style: Optional[ttk.Style] = None
        self.status_value_label: Optional[ttk.Label] = None
        self.position_label: Optional[ttk.Label] = None
        self.start_stop_button: Optional[ttk.Button] = None
        self.apply_timing_button: Optional[ttk.Button] = None
        self.timing_error_label: Optional[ttk.Label] = None
        self.applied_delay_label: Optional[ttk.Label] = None
        self._offset_display_label: Optional[ttk.Label] = None
        self._offset_scale: Optional[ttk.Scale] = None
        self._in_offset_update = False
        self.status_pill_label: Optional[tk.Label] = None
        self.status_message_label: Optional[ttk.Label] = None
        self.version_label: Optional[ttk.Label] = None
        self.countdown_value_label: Optional[ttk.Label] = None
        self.validation_banner_frame: Optional[ttk.Frame] = None
        self.validation_banner_label: Optional[ttk.Label] = None

        self.theme = THEME
        self._debounce_handles: dict[str, str] = {}
        self._ui_event_queue: queue.Queue[Callable[[], None]] = queue.Queue()
        self._ui_event_after: Optional[str] = None
        self._animation_handles: dict[str, str] = {}
        self._is_running = False
        self._status_pill_colors: dict[str, tuple[str, str]] = {
            "idle": (self.theme.pill_idle_bg, self.theme.pill_idle_fg),
            "running": ("#064E3B", "#ECFDF5"),
        }
        self._countdown_target_ts: Optional[float] = None
        self._countdown_after: Optional[str] = None
        self._validation_messages: dict[str, str] = {}
        self._validation_banner_visible = False

        self.min_delay_var = tk.DoubleVar(value=1.0)
        self.max_delay_var = tk.DoubleVar(value=3.0)
        self._timing_inputs_valid: bool = True
        self.offset_range_var = tk.IntVar(value=3)
        self.always_on_top_var = tk.BooleanVar(value=False)
        self.console_output_var = tk.BooleanVar(value=True)
        self.show_indicator_var = tk.BooleanVar(value=True)
        # Store human-readable hotkey and also parsed fields
        self.hotkey_var = tk.StringVar(value="Numpad 5 (vk=101)")
        self.hotkey_vk: Optional[int] = 101
        self.hotkey_char: Optional[str] = None
        self.hotkey_name: Optional[str] = None

        # Ensure closing the window exits the app entirely
        try:
            self.window.protocol("WM_DELETE_WINDOW", self._on_close_window)
        except Exception:
            pass

        self._apply_theme()
        self._build_layout()
        self._bind_behaviors()
        self._start_ui_event_pump()
        self._validate_timing_inputs()
        self._on_offset_var_changed()

        # Load settings after widgets exist
        self.load_settings()

        # Apply initial component values to backend
        self._apply_delay_settings()
        self._apply_offset_settings()
        self._apply_always_on_top()
        self._apply_show_indicator()
        # Push hotkey to handler
        self._apply_hotkey_to_handler()

    def _configure_dpi_awareness(self) -> None:
        if os.name != "nt":
            return
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    def _configure_tk_scaling(self) -> None:
        if not hasattr(self, "window"):
            return
        scaling = 1.0
        if os.name == "nt":
            try:
                dpi = float(self.window.winfo_fpixels("1i"))
                scaling = max(1.0, dpi / 96.0)
            except Exception:
                scaling = 1.25
        try:
            self.window.tk.call("tk", "scaling", scaling)
        except Exception:
            pass

    # Layout construction
    def _apply_theme(self) -> None:
        self.style = ttk.Style(self.window)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.theme.configure(self.window, self.style)

    def _create_card(self, parent: ttk.Frame, title: str) -> ttk.Frame:
        card = ttk.Frame(parent, style="Card.TFrame", padding=(SPACE_16, SPACE_16))
        card.pack(fill="x", pady=(0, SPACE_16))

        ttk.Label(card, text=title, style="CardHeading.TLabel").pack(anchor="w")
        ttk.Separator(card).pack(fill="x", pady=(SPACE_8, SPACE_12))

        body = ttk.Frame(card, style="CardBody.TFrame")
        body.pack(fill="x")
        return body

    def _build_header_bar(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent, style="Header.TFrame", padding=(SPACE_16, SPACE_12))
        header.pack(fill="x", pady=(0, SPACE_16))

        text_area = ttk.Frame(header, style="Header.TFrame")
        text_area.pack(side="left", fill="both", expand=True)

        title_row = ttk.Frame(text_area, style="Header.TFrame")
        title_row.pack(fill="x")
        ttk.Label(title_row, text=self._resolve_app_name(), style="Header.TLabel").pack(side="left", anchor="w")

        version = self._resolve_version_text()
        if version:
            self.version_label = ttk.Label(title_row, text=version, style="Subtitle.TLabel")
            self.version_label.pack(side="left", padx=(SPACE_8, 0))

        self.status_message_label = ttk.Label(
            text_area,
            text="Automation idle",
            style="Subtitle.TLabel",
        )
        self.status_message_label.pack(anchor="w", pady=(SPACE_4, 0))

        pill_bg, pill_fg = self._status_pill_colors["idle"]
        self.status_pill_label = tk.Label(
            header,
            text="Idle",
            font=(self.theme.font_family, 9, "bold"),
            bg=pill_bg,
            fg=pill_fg,
            padx=SPACE_12,
            pady=SPACE_4,
            borderwidth=0,
            relief="flat",
        )
        self.status_pill_label.pack(side="right", anchor="e")

    def _build_validation_banner(self, parent: ttk.Frame) -> None:
        holder = ttk.Frame(parent, style="Main.TFrame")
        holder.pack(fill="x")
        banner = ttk.Frame(holder, style="ValidationError.TFrame", padding=(SPACE_12, SPACE_8))
        self.validation_banner_frame = banner
        ttk.Label(banner, text="!", style="ValidationError.TLabel").pack(side="left", padx=(0, SPACE_8))
        self.validation_banner_label = ttk.Label(banner, text="", style="ValidationError.TLabel")
        self.validation_banner_label.pack(side="left", fill="x", expand=True)

    def _build_status_card(self, container: ttk.Frame) -> None:
        status_body = self._create_card(container, "Live Status")
        status_body.columnconfigure(0, weight=1)
        status_body.columnconfigure(1, weight=1)

        ttk.Label(status_body, text="Status", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.status_value_label = ttk.Label(status_body, text="Inactive", style="StatusInactive.TLabel")
        self.status_value_label.grid(row=0, column=1, sticky="e")

        ttk.Label(status_body, text="Position", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(SPACE_8, 0))
        self.position_label = ttk.Label(status_body, text="Not Locked", style="Strong.TLabel")
        self.position_label.grid(row=1, column=1, sticky="e", pady=(SPACE_8, 0))

        countdown_row = ttk.Frame(status_body, style="CardBody.TFrame")
        countdown_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(SPACE_12, 0))
        countdown_row.columnconfigure(0, weight=1)
        ttk.Label(countdown_row, text="Next Click", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.countdown_value_label = ttk.Label(countdown_row, text="--.- s", style="Strong.TLabel")
        self.countdown_value_label.grid(row=0, column=1, sticky="e")

        self.start_stop_button = ttk.Button(
            status_body,
            text="Start Auto-Clicker",
            command=self._on_toggle_clicked,
            style="Primary.TButton",
        )
        self.start_stop_button.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(SPACE_16, 0))
        self._start_countdown_loop()

    def _build_timing_card(self, container: ttk.Frame) -> None:
        timing_body = self._create_card(container, "Click Timing")
        timing_body.columnconfigure(0, weight=1)
        timing_body.columnconfigure(1, weight=1)
        timing_body.columnconfigure(2, weight=1)

        ttk.Label(timing_body, text="Min Delay (sec)", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(timing_body, text="Max Delay (sec)", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(SPACE_12, 0))

        ttk.Spinbox(
            timing_body,
            from_=MIN_DELAY_SECONDS,
            to=MAX_DELAY_SECONDS,
            increment=0.1,
            textvariable=self.min_delay_var,
            width=6,
            justify="center",
            style="Input.Spinbox",
            format="%.1f",
        ).grid(row=0, column=1, sticky="w", padx=(SPACE_12, 0))

        ttk.Spinbox(
            timing_body,
            from_=MIN_DELAY_SECONDS,
            to=MAX_DELAY_SECONDS,
            increment=0.1,
            textvariable=self.max_delay_var,
            width=6,
            justify="center",
            style="Input.Spinbox",
            format="%.1f",
        ).grid(row=1, column=1, sticky="w", padx=(SPACE_12, 0), pady=(SPACE_12, 0))

        self.apply_timing_button = ttk.Button(
            timing_body,
            text="Apply Timing",
            command=self._apply_delay_settings,
            style="Primary.TButton",
        )
        self.apply_timing_button.grid(row=0, column=2, rowspan=2, sticky="ew", padx=(SPACE_16, 0))

        self.timing_error_label = ttk.Label(timing_body, text="", style="Error.TLabel")
        self.timing_error_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(SPACE_12, 0))

        self.applied_delay_label = ttk.Label(timing_body, text="Applied: Min 1s, Max 3s", style="Meta.TLabel")
        self.applied_delay_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=(SPACE_8, 0))

    def _build_offset_card(self, container: ttk.Frame) -> None:
        offset_body = self._create_card(container, "Position Offset")
        offset_body.columnconfigure(0, weight=1)
        offset_body.columnconfigure(1, weight=1)

        ttk.Label(offset_body, text="Randomize each click within:", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self._offset_display_label = ttk.Label(offset_body, text="±3 px", style="Strong.TLabel")
        self._offset_display_label.grid(row=0, column=1, sticky="e")
        self._update_offset_display(self.offset_range_var.get())

        self._offset_scale = ttk.Scale(
            offset_body,
            from_=0,
            to=OFFSET_MAX_PX,
            command=self._on_offset_scale_changed,
            orient="horizontal",
        )
        self._offset_scale.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(SPACE_12, 0))
        try:
            self._offset_scale.set(float(self.offset_range_var.get()))
        except Exception:
            pass

        ttk.Spinbox(
            offset_body,
            from_=0,
            to=OFFSET_MAX_PX,
            increment=1,
            textvariable=self.offset_range_var,
            width=6,
            justify="center",
            style="Input.Spinbox",
        ).grid(row=2, column=0, sticky="w", pady=(SPACE_12, 0))
        ttk.Label(offset_body, text="Use the arrows or slider for fine control.", style="Meta.TLabel").grid(
            row=2, column=1, sticky="e", pady=(SPACE_12, 0)
        )

    def _build_behavior_card(self, container: ttk.Frame) -> None:
        behavior_body = self._create_card(container, "Behavior & Visibility")
        behavior_body.columnconfigure(0, weight=1)

        ttk.Checkbutton(
            behavior_body,
            text="Show Status Indicator",
            variable=self.show_indicator_var,
            command=self._apply_show_indicator,
            style="Toggle.TCheckbutton",
        ).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(
            behavior_body,
            text="Always On Top",
            variable=self.always_on_top_var,
            command=self._apply_always_on_top,
            style="Toggle.TCheckbutton",
        ).grid(row=1, column=0, sticky="w", pady=(SPACE_8, 0))
        ttk.Checkbutton(
            behavior_body,
            text="Console Debug Output",
            variable=self.console_output_var,
            command=self._apply_console_output,
            style="Toggle.TCheckbutton",
        ).grid(row=2, column=0, sticky="w", pady=(SPACE_8, 0))

    def _build_hotkey_card(self, container: ttk.Frame) -> None:
        hotkey_body = self._create_card(container, "Toggle Hotkey")
        hotkey_body.columnconfigure(0, weight=1)
        hotkey_body.columnconfigure(1, weight=1)

        ttk.Label(hotkey_body, text="Current Hotkey", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(hotkey_body, textvariable=self.hotkey_var, style="Strong.TLabel").grid(
            row=1, column=0, sticky="w", pady=(SPACE_8, 0)
        )
        ttk.Button(hotkey_body, text="Capture New Hotkey", command=self._capture_hotkey, style="Secondary.TButton").grid(
            row=1, column=1, sticky="e", pady=(SPACE_8, 0)
        )
        ttk.Label(
            hotkey_body,
            text="Hotkeys apply immediately after capture.",
            style="Meta.TLabel",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(SPACE_12, 0))

    def _build_footer(self, container: ttk.Frame) -> None:
        footer = ttk.Frame(container, style="Main.TFrame")
        footer.pack(fill="x", pady=(SPACE_8, 0))
        footer.columnconfigure(0, weight=1)
        footer.columnconfigure(1, weight=1)

        ttk.Button(
            footer,
            text="Minimize to Indicator",
            command=self.minimize_to_indicator,
            style="Secondary.TButton",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(
            footer,
            text="Save Settings",
            command=self.save_settings,
            style="Primary.TButton",
        ).grid(row=0, column=1, sticky="e")

    def _resolve_app_name(self) -> str:
        app_name = getattr(self.app, "APP_NAME", None)
        if isinstance(app_name, str) and app_name.strip():
            return app_name
        config_name = getattr(getattr(self.app, "config", None), "APP_NAME", None)
        if isinstance(config_name, str) and config_name.strip():
            return config_name
        return "ClickClick!"

    def _resolve_version_text(self) -> str:
        version = getattr(self.app, "VERSION", None) or getattr(self.app, "__version__", None)
        if version is None and hasattr(self.app, "config"):
            version = getattr(self.app.config, "VERSION", None)
        if isinstance(version, (str, int, float)):
            version_str = str(version).strip()
            if version_str:
                return version_str if version_str.startswith("v") else f"v{version_str}"
        return ""

    def _build_layout(self) -> None:
        root = self.window

        container = ttk.Frame(root, style="Main.TFrame", padding=SPACE_16 + SPACE_8)
        container.pack(fill="both", expand=True)

        self._build_validation_banner(container)
        self._build_header_bar(container)
        self._build_status_card(container)
        self._build_timing_card(container)
        self._build_offset_card(container)
        self._build_behavior_card(container)
        self._build_hotkey_card(container)
        self._build_footer(container)

    def _bind_behaviors(self) -> None:
        try:
            self.offset_range_var.trace_add("write", lambda *args: self._on_offset_var_changed())
            self.min_delay_var.trace_add(
                "write",
                lambda *args: self.debounce("timing_validation", 150, self._validate_timing_inputs),
            )
            self.max_delay_var.trace_add(
                "write",
                lambda *args: self.debounce("timing_validation", 150, self._validate_timing_inputs),
            )
        except Exception:
            pass

    def debounce(self, key: str, delay_ms: int, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        handle = self._debounce_handles.get(key)
        if handle is not None:
            try:
                self.window.after_cancel(handle)
            except Exception:
                pass

        def _invoke() -> None:
            self._debounce_handles.pop(key, None)
            func(*args, **kwargs)

        try:
            self._debounce_handles[key] = self.window.after(delay_ms, _invoke)
        except Exception:
            _invoke()

    def post_ui_event(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        def _callback() -> None:
            func(*args, **kwargs)

        self._ui_event_queue.put(_callback)

    def _start_ui_event_pump(self) -> None:
        if self._ui_event_after is not None:
            return

        def _drain_queue() -> None:
            while True:
                try:
                    callback = self._ui_event_queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    callback()
                except Exception:
                    pass
            try:
                self._ui_event_after = self.window.after(30, _drain_queue)
            except Exception:
                self._ui_event_after = None

        try:
            self._ui_event_after = self.window.after(30, _drain_queue)
        except Exception:
            _drain_queue()

    def _stop_ui_event_pump(self) -> None:
        if self._ui_event_after is None:
            return
        try:
            self.window.after_cancel(self._ui_event_after)
        except Exception:
            pass
        finally:
            self._ui_event_after = None

    def update_next_click_eta(self, remaining_seconds: Optional[float]) -> None:
        self.post_ui_event(self._apply_next_click_eta, remaining_seconds)

    def _apply_next_click_eta(self, remaining_seconds: Optional[float]) -> None:
        if remaining_seconds is None or remaining_seconds <= 0:
            self._countdown_target_ts = None
            self._countdown_total_interval = None
        else:
            self._countdown_target_ts = time.monotonic() + float(remaining_seconds)
            self._countdown_total_interval = float(remaining_seconds)
        self._update_countdown_label()

    def _start_countdown_loop(self) -> None:
        if self._countdown_after is not None or self.countdown_value_label is None:
            return

        def _tick() -> None:
            self._update_countdown_label()
            try:
                self._countdown_after = self.window.after(100, _tick)
            except Exception:
                self._countdown_after = None

        try:
            self._countdown_after = self.window.after(100, _tick)
        except Exception:
            _tick()

    def _stop_countdown_loop(self) -> None:
        if self._countdown_after is None:
            return
        try:
            self.window.after_cancel(self._countdown_after)
        except Exception:
            pass
        finally:
            self._countdown_after = None
        self._countdown_target_ts = None
        self._countdown_total_interval = None

    def _update_countdown_label(self) -> None:
        if self.countdown_value_label is None:
            return
        if not self._is_running or self._countdown_target_ts is None:
            self.countdown_value_label.configure(text="--.- s")
            return
        remaining = max(0.0, self._countdown_target_ts - time.monotonic())
        self.countdown_value_label.configure(text=f"{remaining:0.1f} s")
        total = getattr(self, "_countdown_total_interval", None)
        if total is None or total <= 0:
            return

    def _set_validation_message(self, key: str, message: str) -> None:
        if message:
            if key in self._validation_messages:
                self._validation_messages.pop(key)
            self._validation_messages[key] = message
        else:
            self._validation_messages.pop(key, None)
        self._refresh_validation_banner()

    def _clear_validation_message(self, key: str) -> None:
        if key in self._validation_messages:
            self._validation_messages.pop(key, None)
            self._refresh_validation_banner()

    def _refresh_validation_banner(self) -> None:
        if not self._validation_messages:
            self._hide_validation_banner()
            return
        latest_message = next(reversed(self._validation_messages.values()))
        self._show_validation_banner(latest_message)

    def _show_validation_banner(self, message: str) -> None:
        if not self.validation_banner_frame or not self.validation_banner_label:
            return
        self.validation_banner_label.configure(text=message)
        if not self._validation_banner_visible:
            try:
                self.validation_banner_frame.pack(fill="x", pady=(0, SPACE_12))
            except Exception:
                pass
            self._validation_banner_visible = True

    def _hide_validation_banner(self) -> None:
        if not self.validation_banner_frame or not self._validation_banner_visible:
            return
        try:
            self.validation_banner_frame.pack_forget()
        except Exception:
            pass
        self._validation_banner_visible = False

    def animate_color(
        self,
        key: str,
        from_hex: str,
        to_hex: str,
        duration_ms: int,
        setter: Callable[[str], None],
        steps: int = 10,
    ) -> None:
        handle = self._animation_handles.pop(key, None)
        if handle is not None:
            try:
                self.window.after_cancel(handle)
            except Exception:
                pass
        from_hex = self._coerce_color_hex(from_hex, to_hex)
        to_hex = self._coerce_color_hex(to_hex, from_hex)
        if from_hex.lower() == to_hex.lower():
            setter(to_hex)
            return
        steps = max(2, steps)
        interval = max(16, duration_ms // steps) if duration_ms > 0 else 0
        step_state = {"index": 0}

        def _tick() -> None:
            idx = step_state["index"]
            t = min(1.0, idx / (steps - 1))
            setter(hex_lerp(from_hex, to_hex, t))
            if t >= 1.0:
                self._animation_handles.pop(key, None)
                return
            step_state["index"] = idx + 1
            self._animation_handles[key] = self.window.after(interval, _tick)

        if interval == 0:
            setter(to_hex)
            return
        step_state["index"] = 0
        self._animation_handles[key] = self.window.after(interval, _tick)

    def _coerce_color_hex(self, value: Any, fallback: str) -> str:
        if isinstance(value, str) and value.startswith("#") and len(value) in {4, 7}:
            if len(value) == 4:
                r, g, b = value[1], value[2], value[3]
                return f"#{r}{r}{g}{g}{b}{b}".upper()
            return value.upper()
        return fallback.upper() if isinstance(fallback, str) else "#000000"

    def _on_offset_var_changed(self) -> None:
        if self._in_offset_update:
            return
        try:
            value = int(self.offset_range_var.get())
        except Exception:
            self._set_validation_message("offset", f"Offset must be a number between 0 and {OFFSET_MAX_PX} px.")
            return
        value = max(0, min(OFFSET_MAX_PX, value))
        self._clear_validation_message("offset")
        if value != self.offset_range_var.get():
            self._in_offset_update = True
            try:
                self.offset_range_var.set(value)
            finally:
                self._in_offset_update = False
            return

        self._update_offset_display(value)
        if self._offset_scale is not None:
            self._in_offset_update = True
            try:
                self._offset_scale.set(float(value))
            finally:
                self._in_offset_update = False

        self._apply_offset_settings(value)

    def _on_offset_scale_changed(self, value: str) -> None:
        if self._in_offset_update:
            return
        try:
            numeric = int(float(value))
        except (TypeError, ValueError):
            self._set_validation_message("offset", f"Offset must be a number between 0 and {OFFSET_MAX_PX} px.")
            return
        self._clear_validation_message("offset")
        numeric = max(0, min(OFFSET_MAX_PX, numeric))
        if numeric != self.offset_range_var.get():
            self._in_offset_update = True
            try:
                self.offset_range_var.set(numeric)
            finally:
                self._in_offset_update = False
        else:
            self._update_offset_display(numeric)
            self._apply_offset_settings(numeric)

    def _update_offset_display(self, value: int) -> None:
        if self._offset_display_label is not None:
            try:
                ratio = min(1.0, max(0.0, float(value) / float(OFFSET_MAX_PX)))
                color = hex_lerp(self.theme.strong_text, self.theme.highlight, ratio)
                self._offset_display_label.configure(text=f"±{value} px", foreground=color)
            except Exception:
                pass

    def reflect_offset_range(self, value: int) -> None:
        self.post_ui_event(self._apply_reflected_offset_range, value)

    def _apply_reflected_offset_range(self, value: int) -> None:
        try:
            numeric = int(value)
        except Exception:
            return
        numeric = max(0, min(OFFSET_MAX_PX, numeric))
        self._in_offset_update = True
        try:
            self.offset_range_var.set(numeric)
            if self._offset_scale is not None:
                self._offset_scale.set(float(numeric))
        except Exception:
            pass
        finally:
            self._in_offset_update = False
        self._update_offset_display(numeric)

    def _status_message_text(self, is_active: bool, locked_position: Optional[Tuple[int, int]]) -> str:
        if is_active and locked_position is not None:
            return f"Running at {locked_position[0]}, {locked_position[1]}"
        if is_active:
            return "Automation running"
        return "Automation idle"

    def _update_status_pill(self, is_active: bool) -> None:
        if self.status_pill_label is None:
            return
        state = "running" if is_active else "idle"
        target_bg, target_fg = self._status_pill_colors[state]
        current_bg = self._coerce_color_hex(self.status_pill_label.cget("background"), target_bg)
        self.status_pill_label.configure(text="Running" if is_active else "Idle", fg=target_fg)
        if current_bg.lower() == target_bg.lower():
            self.status_pill_label.configure(bg=target_bg)
            return
        self.animate_color(
            "status_pill",
            current_bg,
            target_bg,
            240,
            lambda color: self.status_pill_label.configure(bg=color),
        )

    # Public API
    def update_status(self, is_active: bool, locked_position: Optional[Tuple[int, int]]) -> None:
        self.post_ui_event(self._apply_status_update, is_active, locked_position)

    def _apply_status_update(self, is_active: bool, locked_position: Optional[Tuple[int, int]]) -> None:
        if self.status_value_label is not None:
            style = "StatusActive.TLabel" if is_active else "StatusInactive.TLabel"
            self.status_value_label.configure(text="Active" if is_active else "Inactive", style=style)
        if self.start_stop_button is not None:
            if is_active:
                self.start_stop_button.configure(text="Stop Auto-Clicker", style="Danger.TButton")
            else:
                self.start_stop_button.configure(text="Start Auto-Clicker", style="Primary.TButton")
        if self.position_label is not None:
            if locked_position is not None:
                self.position_label.configure(text=f"Position: {locked_position[0]}, {locked_position[1]}")
            else:
                self.position_label.configure(text="Position: Not Locked")
        if self.status_message_label is not None:
            self.status_message_label.configure(text=self._status_message_text(is_active, locked_position))
        self._update_status_pill(is_active)
        self._is_running = is_active
        if not is_active:
            self._countdown_target_ts = None
            self._countdown_total_interval = None
        self._update_countdown_label()

    def minimize_to_indicator(self) -> None:
        try:
            self.window.withdraw()
        except Exception:
            pass

    def restore_window(self) -> None:
        try:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
        except Exception:
            pass

    def _on_close_window(self) -> None:
        """
        Handle window close button click.
        This is called when user clicks the X button on the window.
        """
        self._stop_ui_event_pump()
        self._stop_countdown_loop()
        try:
            # Add diagnostic log
            import src.config as cfg
            if cfg.CONSOLE_OUTPUT_ENABLED:
                print("[DEBUG] GUI _on_close_window called - user clicked close button")
        except Exception:
            pass

        try:
            # Call the app's close handler which triggers full cleanup
            if hasattr(self.app, '_on_close_window'):
                if hasattr(self.app, 'config'):
                    if self.app.config.CONSOLE_OUTPUT_ENABLED:
                        print("[DEBUG] Calling app._on_close_window()")
                self.app._on_close_window()
            else:
                # Fallback: call cleanup directly
                if hasattr(self.app, 'cleanup'):
                    if hasattr(self.app, 'config'):
                        if self.app.config.CONSOLE_OUTPUT_ENABLED:
                            print("[DEBUG] Calling app.cleanup() as fallback")
                    self.app.cleanup()
        except Exception as e:
            try:
                import src.config as cfg
                if cfg.CONSOLE_OUTPUT_ENABLED:
                    print(f"[DEBUG] Error in _on_close_window: {e}")
            except Exception:
                pass

    # Event handlers
    def _on_toggle_clicked(self) -> None:
        try:
            self.app.toggle_clicking()
        except Exception:
            pass

    def _apply_delay_settings(self) -> None:
        try:
            valid, msg = self._timing_is_valid()
            if not valid:
                self._set_timing_error(msg)
                return
            min_d = self._clamp_delay_value(self.min_delay_var.get())
            max_d = self._clamp_delay_value(self.max_delay_var.get())
            self.min_delay_var.set(min_d)
            self.max_delay_var.set(max_d)
            if hasattr(self.app, "update_delay_range"):
                self.app.update_delay_range(float(min_d), float(max_d))
            self._update_applied_delay_label(min_d, max_d)
            self._set_timing_error("")
        except Exception:
            pass

    def _validate_timing_inputs(self) -> None:
        valid, msg = self._timing_is_valid()
        self._timing_inputs_valid = valid
        self._set_timing_error(msg if not valid else "")
        if valid:
            self._clear_validation_message("timing")
        else:
            self._set_validation_message("timing", msg)
        if self.apply_timing_button is not None:
            try:
                if valid:
                    self.apply_timing_button.state(["!disabled"])
                else:
                    self.apply_timing_button.state(["disabled"])
            except Exception:
                pass

    def _timing_is_valid(self) -> tuple[bool, str]:
        try:
            min_d = float(self.min_delay_var.get())
            max_d = float(self.max_delay_var.get())
        except Exception:
            return False, "Enter numeric delays (0.1-10.0s)."
        if min_d < MIN_DELAY_SECONDS or min_d > MAX_DELAY_SECONDS:
            return False, f"Min delay must be between {MIN_DELAY_SECONDS:.1f}s and {MAX_DELAY_SECONDS:.1f}s."
        if max_d < MIN_DELAY_SECONDS or max_d > MAX_DELAY_SECONDS:
            return False, f"Max delay must be between {MIN_DELAY_SECONDS:.1f}s and {MAX_DELAY_SECONDS:.1f}s."
        if max_d < min_d:
            return False, "Max delay must be greater than or equal to Min delay."
        return True, ""

    def _set_timing_error(self, message: str) -> None:
        try:
            if self.timing_error_label is not None:
                self.timing_error_label.configure(text=message)
        except Exception:
            pass

    def _clamp_delay_value(self, value: Any) -> float:
        try:
            numeric = float(value)
        except Exception:
            numeric = MIN_DELAY_SECONDS
        numeric = max(MIN_DELAY_SECONDS, min(MAX_DELAY_SECONDS, round(numeric, 1)))
        return numeric

    def _format_delay_text(self, value: float) -> str:
        if float(value).is_integer():
            return f"{int(value)}s"
        return f"{value:.1f}s"

    def _update_applied_delay_label(self, min_d: float, max_d: float) -> None:
        try:
            if self.applied_delay_label is not None:
                min_text = self._format_delay_text(min_d)
                max_text = self._format_delay_text(max_d)
                self.applied_delay_label.configure(text=f"Applied: Min {min_text}, Max {max_text}")
        except Exception:
            pass

    def _apply_offset_settings(self, value: Optional[int] = None) -> None:
        try:
            rng = int(value if value is not None else self.offset_range_var.get())
        except Exception:
            return
        rng = max(0, min(OFFSET_MAX_PX, rng))
        if value is None and rng != self.offset_range_var.get():
            self._in_offset_update = True
            try:
                self.offset_range_var.set(rng)
            finally:
                self._in_offset_update = False
            return
        if hasattr(self.app, "update_offset_range"):
            self.app.update_offset_range(rng)
        self._update_offset_display(rng)

    def _apply_always_on_top(self) -> None:
        try:
            self.window.attributes('-topmost', bool(self.always_on_top_var.get()))
        except Exception:
            pass

    def _apply_show_indicator(self) -> None:
        try:
            if self.show_indicator_var.get():
                if getattr(self.app.status_indicator, "root", None) is not None:
                    self.app.status_indicator.root.deiconify()
            else:
                if getattr(self.app.status_indicator, "root", None) is not None:
                    self.app.status_indicator.root.withdraw()
        except Exception:
            pass

    def _apply_console_output(self) -> None:
        try:
            # Reflect in config value if present
            import src.config as cfg  # type: ignore
            cfg.CONSOLE_OUTPUT_ENABLED = bool(self.console_output_var.get())
        except Exception:
            try:
                import config as cfg  # type: ignore
                cfg.CONSOLE_OUTPUT_ENABLED = bool(self.console_output_var.get())
            except Exception:
                pass

    # Settings persistence
    def load_settings(self) -> None:
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Clamp persisted values into supported ranges
                self.min_delay_var.set(self._clamp_delay_value(data.get("min_delay", self.min_delay_var.get())))
                self.max_delay_var.set(self._clamp_delay_value(data.get("max_delay", self.max_delay_var.get())))
                self.offset_range_var.set(int(data.get("offset_range", self.offset_range_var.get())))
                self.always_on_top_var.set(bool(data.get("always_on_top", self.always_on_top_var.get())))
                self.console_output_var.set(bool(data.get("console_output", self.console_output_var.get())))
                self.show_indicator_var.set(bool(data.get("show_indicator", self.show_indicator_var.get())))
                # Hotkey deserialization with validation
                hk = data.get("hotkey")
                if isinstance(hk, dict):
                    vk = hk.get("vk")
                    char = hk.get("char")
                    name = hk.get("name")
                    self.hotkey_vk = int(vk) if isinstance(vk, int) else None
                    self.hotkey_char = char if isinstance(char, str) and len(char) == 1 else None
                    self.hotkey_name = name if isinstance(name, str) and name.startswith('Key.') else None
                    self._update_hotkey_label()
                else:
                    # Fallback: string label only
                    try:
                        self.hotkey_var.set(str(hk))
                    except Exception:
                        pass
        except Exception:
            # Corrupt or unreadable settings should not crash
            pass

    def save_settings(self) -> None:
        try:
            data = {
                "min_delay": float(self._clamp_delay_value(self.min_delay_var.get())),
                "max_delay": float(self._clamp_delay_value(self.max_delay_var.get())),
                "offset_range": int(self.offset_range_var.get()),
                "always_on_top": bool(self.always_on_top_var.get()),
                "console_output": bool(self.console_output_var.get()),
                "show_indicator": bool(self.show_indicator_var.get()),
                # Persist hotkey with basic validation
                "hotkey": self._serialize_hotkey(),
            }
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    # Hotkey capture
    def _capture_hotkey(self) -> None:
        if Listener is None:
            # Fallback: inform user capture is unavailable
            try:
                from tkinter import messagebox
                messagebox.showinfo("Hotkey Capture", "pynput is unavailable; cannot capture.")
            except Exception:
                pass
            return

        # Capture next key press in a short-lived listener
        captured = {"done": False}

        def on_press(key):
            if captured["done"]:
                return False
            try:
                # Interpret key: prefer vk if present
                vk = getattr(key, 'vk', None)
                char = getattr(key, 'char', None)
                name = str(key) if vk is None and char is None else None
                self.hotkey_vk = int(vk) if isinstance(vk, int) else None
                self.hotkey_char = str(char) if isinstance(char, str) and len(char) == 1 else None
                self.hotkey_name = name if isinstance(name, str) and name.startswith('Key.') else None
                self._update_hotkey_label()
                self._apply_hotkey_to_handler()
                captured["done"] = True
            finally:
                # Stop listener after capture
                return False

        def run_listener():
            try:
                with Listener(on_press=on_press) as l:
                    l.join()
            except Exception:
                pass

        threading.Thread(target=run_listener, daemon=True).start()

    # Hotkey helpers
    def _update_hotkey_label(self) -> None:
        label = ""
        if self.hotkey_vk is not None:
            label = f"vk={self.hotkey_vk}"
        elif self.hotkey_char is not None:
            label = f"char='{self.hotkey_char}'"
        elif self.hotkey_name is not None:
            label = self.hotkey_name
        else:
            label = "(unset)"
        try:
            self.hotkey_var.set(f"Hotkey: {label}")
        except Exception:
            pass

    def _apply_hotkey_to_handler(self) -> None:
        try:
            if hasattr(self.app, 'hotkey_handler') and hasattr(self.app.hotkey_handler, 'set_hotkey'):
                self.app.hotkey_handler.set_hotkey(vk=self.hotkey_vk, char=self.hotkey_char, name=self.hotkey_name)
        except Exception:
            pass

    def _serialize_hotkey(self) -> dict:
        return {
            "vk": int(self.hotkey_vk) if isinstance(self.hotkey_vk, int) else None,
            "char": self.hotkey_char if isinstance(self.hotkey_char, str) and len(self.hotkey_char) == 1 else None,
            "name": self.hotkey_name if isinstance(self.hotkey_name, str) and self.hotkey_name.startswith('Key.') else None,
        }
