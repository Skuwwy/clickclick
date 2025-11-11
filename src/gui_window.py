"""
GUI control window for ClickClick auto-clicker application.

Provides a Tkinter-based control panel with:
- Start/Stop toggle button
- Min/Max delay controls (0.1–10.0 seconds)
- Position offset range control (0–50 pixels)
- Hotkey capture (stored in settings)
- Status display and position info
- Always-on-top toggle
- Minimize to status indicator overlay and restore on indicator click
- JSON settings persistence

The GUI window integrates with the main application controller and backend
components via callbacks provided by ClickClickApp.
"""

import json
import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from typing import Optional, Tuple

try:
    # pynput is optional at runtime; GUI should still function without capture
    from pynput.keyboard import Listener
except Exception:
    Listener = None  # type: ignore


SETTINGS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "settings.json"))


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

        # Create the window attached to the shared root if provided
        if self.parent_root is not None:
            self.window: tk.Toplevel = tk.Toplevel(self.parent_root)
        else:
            self.window = tk.Tk()

        # Basic window configuration
        self.window.title("ClickClick Auto-Clicker")
        try:
            self.window.geometry("420x560")
            self.window.minsize(420, 520)
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

        self.min_delay_var = tk.IntVar(value=1)
        self.max_delay_var = tk.IntVar(value=3)
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

    # Layout construction
    def _apply_theme(self) -> None:
        base_bg = "#0f172a"
        card_bg = "#111827"
        accent = "#2563EB"
        danger = "#DC2626"
        secondary_bg = "#1f2937"
        highlight = "#60A5FA"

        self.style = ttk.Style(self.window)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.window.configure(bg=base_bg)
        font_family = "Segoe UI"
        try:
            available_families = set(tkfont.families(self.window))
        except tk.TclError:
            available_families = set()

        if font_family not in available_families:
            try:
                font_family = tkfont.nametofont("TkDefaultFont").cget("family")
            except tk.TclError:
                font_family = "TkDefaultFont"

        try:
            self.window.option_add("*Font", f"{{{font_family}}} 10")
        except tk.TclError:
            pass

        self.style.configure("Main.TFrame", background=base_bg)
        self.style.configure("Card.TFrame", background=card_bg, relief="flat", borderwidth=0)
        self.style.configure("CardBody.TFrame", background=card_bg)
        self.style.configure("CardHeading.TLabel", background=card_bg, foreground="#F9FAFB", font=(font_family, 12, "bold"))
        self.style.configure("Header.TLabel", background=base_bg, foreground="#F9FAFB", font=(font_family, 16, "bold"))
        self.style.configure("Subtitle.TLabel", background=base_bg, foreground="#9CA3AF", font=(font_family, 10))
        self.style.configure("Body.TLabel", background=card_bg, foreground="#E5E7EB", font=(font_family, 10))
        self.style.configure("BodyMuted.TLabel", background=card_bg, foreground="#9CA3AF", font=(font_family, 10))
        self.style.configure("BodyStrong.TLabel", background=card_bg, foreground="#F3F4F6", font=(font_family, 11))
        self.style.configure("Meta.TLabel", background=card_bg, foreground=highlight, font=(font_family, 9))
        self.style.configure("Error.TLabel", background=card_bg, foreground="#F87171", font=(font_family, 9))
        self.style.configure("StatusActive.TLabel", background=card_bg, foreground="#34D399", font=(font_family, 11, "bold"))
        self.style.configure("StatusInactive.TLabel", background=card_bg, foreground="#F87171", font=(font_family, 11, "bold"))

        self.style.configure(
            "Accent.TButton",
            background=accent,
            foreground="#F9FAFB",
            font=(font_family, 10, "bold"),
            padding=(16, 10),
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", "#1D4ED8"), ("pressed", "#1E40AF")],
            foreground=[("disabled", "#9CA3AF")],
        )
        self.style.configure(
            "Danger.TButton",
            background=danger,
            foreground="#F9FAFB",
            font=(font_family, 10, "bold"),
            padding=(16, 10),
        )
        self.style.map(
            "Danger.TButton",
            background=[("active", "#B91C1C"), ("pressed", "#7F1D1D")],
            foreground=[("disabled", "#FECACA")],
        )
        self.style.configure(
            "Secondary.TButton",
            background=secondary_bg,
            foreground="#E5E7EB",
            font=(font_family, 10),
            padding=(16, 10),
        )
        self.style.map(
            "Secondary.TButton",
            background=[("active", "#374151"), ("pressed", "#1f2937")],
            foreground=[("disabled", "#6B7280")],
        )

        self.style.configure("Toggle.TCheckbutton", background=card_bg, foreground="#E5E7EB", font=(font_family, 10))
        self.style.map("Toggle.TCheckbutton", foreground=[("disabled", "#6B7280")])
        self.style.configure(
            "Input.Spinbox",
            background=card_bg,
            foreground="#F9FAFB",
            fieldbackground="#1f2937",
            arrowsize=12,
        )
        self.style.configure("TSeparator", background="#1f2937")

    def _create_card(self, parent: ttk.Frame, title: str) -> ttk.Frame:
        card = ttk.Frame(parent, style="Card.TFrame", padding=(16, 18))
        card.pack(fill="x", pady=(0, 16))

        ttk.Label(card, text=title, style="CardHeading.TLabel").pack(anchor="w")
        ttk.Separator(card).pack(fill="x", pady=(10, 14))

        body = ttk.Frame(card, style="CardBody.TFrame")
        body.pack(fill="x")
        return body

    def _build_layout(self) -> None:
        root = self.window

        container = ttk.Frame(root, style="Main.TFrame", padding=24)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="ClickClick Auto-Clicker", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            container,
            text="Configure timing, offsets and automation hotkeys.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 22))

        # Status Section
        status_body = self._create_card(container, "Live Status")
        status_body.columnconfigure(0, weight=1)
        status_body.columnconfigure(1, weight=1)

        ttk.Label(status_body, text="Status", style="BodyMuted.TLabel").grid(row=0, column=0, sticky="w")
        self.status_value_label = ttk.Label(status_body, text="Inactive", style="StatusInactive.TLabel")
        self.status_value_label.grid(row=0, column=1, sticky="e")

        self.position_label = ttk.Label(status_body, text="Position: Not Locked", style="BodyStrong.TLabel")
        self.position_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.start_stop_button = ttk.Button(
            status_body,
            text="Start Auto-Clicker",
            command=self._on_toggle_clicked,
            style="Accent.TButton",
        )
        self.start_stop_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(18, 0))

        # Click Timing Settings
        timing_body = self._create_card(container, "Click Timing")
        timing_body.columnconfigure(0, weight=1)
        timing_body.columnconfigure(1, weight=1)
        timing_body.columnconfigure(2, weight=1)

        ttk.Label(timing_body, text="Min Delay (sec)", style="BodyMuted.TLabel").grid(row=0, column=0, sticky="w")
        min_spin = ttk.Spinbox(
            timing_body,
            from_=1,
            to=50,
            increment=1,
            textvariable=self.min_delay_var,
            width=6,
            justify="center",
            style="Input.Spinbox",
        )
        min_spin.grid(row=0, column=1, sticky="w", padx=(12, 0))

        ttk.Label(timing_body, text="Max Delay (sec)", style="BodyMuted.TLabel").grid(row=1, column=0, sticky="w", pady=(12, 0))
        max_spin = ttk.Spinbox(
            timing_body,
            from_=1,
            to=50,
            increment=1,
            textvariable=self.max_delay_var,
            width=6,
            justify="center",
            style="Input.Spinbox",
        )
        max_spin.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=(12, 0))

        self.apply_timing_button = ttk.Button(
            timing_body,
            text="Apply Timing",
            command=self._apply_delay_settings,
            style="Accent.TButton",
        )
        self.apply_timing_button.grid(row=0, column=2, rowspan=2, sticky="ew", padx=(18, 0))

        self.timing_error_label = ttk.Label(timing_body, text="", style="Error.TLabel")
        self.timing_error_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(12, 0))

        self.applied_delay_label = ttk.Label(timing_body, text="Applied: Min 1s, Max 3s", style="Meta.TLabel")
        self.applied_delay_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # Position Offset Settings
        offset_body = self._create_card(container, "Position Offset")
        offset_body.columnconfigure(0, weight=1)
        offset_body.columnconfigure(1, weight=1)

        ttk.Label(offset_body, text="Randomize each click within:", style="BodyMuted.TLabel").grid(row=0, column=0, sticky="w")
        self._offset_display_label = ttk.Label(offset_body, text="±3 px", style="BodyStrong.TLabel")
        self._offset_display_label.grid(row=0, column=1, sticky="e")

        self._offset_scale = ttk.Scale(
            offset_body,
            from_=0,
            to=50,
            command=self._on_offset_scale_changed,
            orient="horizontal",
        )
        self._offset_scale.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        try:
            self._offset_scale.set(float(self.offset_range_var.get()))
        except Exception:
            pass

        ttk.Spinbox(
            offset_body,
            from_=0,
            to=50,
            increment=1,
            textvariable=self.offset_range_var,
            width=6,
            justify="center",
            style="Input.Spinbox",
        ).grid(row=2, column=0, sticky="w", pady=(14, 0))
        ttk.Label(offset_body, text="Use the arrows or slider for fine control.", style="Meta.TLabel").grid(
            row=2, column=1, sticky="e", pady=(14, 0)
        )

        # Hotkey Configuration
        hotkey_body = self._create_card(container, "Toggle Hotkey")
        hotkey_body.columnconfigure(0, weight=1)
        hotkey_body.columnconfigure(1, weight=1)

        ttk.Label(hotkey_body, text="Current Hotkey", style="BodyMuted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(hotkey_body, textvariable=self.hotkey_var, style="BodyStrong.TLabel").grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Button(hotkey_body, text="Capture New Hotkey", command=self._capture_hotkey, style="Secondary.TButton").grid(
            row=1, column=1, sticky="e", pady=(6, 0)
        )
        ttk.Label(
            hotkey_body,
            text="Hotkeys apply immediately after capture.",
            style="Meta.TLabel",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 0))

        # Advanced Options
        adv_body = self._create_card(container, "Advanced Options")
        adv_body.columnconfigure(0, weight=1)

        ttk.Checkbutton(
            adv_body,
            text="Show Status Indicator",
            variable=self.show_indicator_var,
            command=self._apply_show_indicator,
            style="Toggle.TCheckbutton",
        ).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(
            adv_body,
            text="Always On Top",
            variable=self.always_on_top_var,
            command=self._apply_always_on_top,
            style="Toggle.TCheckbutton",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Checkbutton(
            adv_body,
            text="Console Debug Output",
            variable=self.console_output_var,
            command=self._apply_console_output,
            style="Toggle.TCheckbutton",
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))

        # Footer Buttons
        footer = ttk.Frame(container, style="Main.TFrame")
        footer.pack(fill="x", pady=(6, 0))
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
            style="Accent.TButton",
        ).grid(row=0, column=1, sticky="e")

    def _bind_behaviors(self) -> None:
        try:
            self.offset_range_var.trace_add("write", lambda *args: self._on_offset_var_changed())
            self.min_delay_var.trace_add("write", lambda *args: self._validate_timing_inputs())
            self.max_delay_var.trace_add("write", lambda *args: self._validate_timing_inputs())
        except Exception:
            pass

    def _on_offset_var_changed(self) -> None:
        if self._in_offset_update:
            return
        try:
            value = int(self.offset_range_var.get())
        except Exception:
            return
        value = max(0, min(50, value))
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
            return
        numeric = max(0, min(50, numeric))
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
                self._offset_display_label.configure(text=f"±{value} px")
            except Exception:
                pass

    # Public API
    def update_status(self, is_active: bool, locked_position: Optional[Tuple[int, int]]) -> None:
        # Thread-safe UI updates
        def _apply():
            if self.status_value_label is not None:
                style = "StatusActive.TLabel" if is_active else "StatusInactive.TLabel"
                self.status_value_label.configure(text="Active" if is_active else "Inactive", style=style)
            if self.start_stop_button is not None:
                if is_active:
                    self.start_stop_button.configure(text="Stop Auto-Clicker", style="Danger.TButton")
                else:
                    self.start_stop_button.configure(text="Start Auto-Clicker", style="Accent.TButton")
            if self.position_label is not None:
                if locked_position is not None:
                    self.position_label.configure(text=f"Position: {locked_position[0]}, {locked_position[1]}")
                else:
                    self.position_label.configure(text="Position: Not Locked")

        try:
            self.window.after(0, _apply)
        except Exception:
            _apply()

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
            min_d = int(self.min_delay_var.get())
            max_d = int(self.max_delay_var.get())
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
            min_d = int(self.min_delay_var.get())
            max_d = int(self.max_delay_var.get())
        except Exception:
            return False, "Enter whole numbers for delays."
        if min_d < 1 or min_d > 50:
            return False, "Min delay must be between 1 and 50 seconds."
        if max_d < 1 or max_d > 50:
            return False, "Max delay must be between 1 and 50 seconds."
        if max_d < min_d:
            return False, "Max delay must be greater than or equal to Min delay."
        return True, ""

    def _set_timing_error(self, message: str) -> None:
        try:
            if self.timing_error_label is not None:
                self.timing_error_label.configure(text=message)
        except Exception:
            pass

    def _update_applied_delay_label(self, min_d: int, max_d: int) -> None:
        try:
            if self.applied_delay_label is not None:
                self.applied_delay_label.configure(text=f"Applied: Min {min_d}s, Max {max_d}s")
        except Exception:
            pass

    def _apply_offset_settings(self, value: Optional[int] = None) -> None:
        try:
            rng = int(value if value is not None else self.offset_range_var.get())
        except Exception:
            return
        rng = max(0, min(50, rng))
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
                # Coerce to integers for whole-second UI
                self.min_delay_var.set(int(float(data.get("min_delay", self.min_delay_var.get()))))
                self.max_delay_var.set(int(float(data.get("max_delay", self.max_delay_var.get()))))
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
                "min_delay": float(int(self.min_delay_var.get())),
                "max_delay": float(int(self.max_delay_var.get())),
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
