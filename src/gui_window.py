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
            self.window.geometry("400x600")
        except Exception:
            pass
        try:
            self.window.resizable(False, False)
        except Exception:
            pass

        # Widgets
        self.status_value_label: Optional[tk.Label] = None
        self.position_label: Optional[tk.Label] = None
        self.start_stop_button: Optional[tk.Button] = None
        self.min_delay_var = tk.IntVar(value=1)
        self.max_delay_var = tk.IntVar(value=3)
        self.timing_error_label: Optional[tk.Label] = None
        self.applied_delay_label: Optional[tk.Label] = None
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

        self._build_layout()
        self._bind_behaviors()

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
    def _build_layout(self) -> None:
        root = self.window

        # Status Section
        status_frame = tk.LabelFrame(root, text="Status Section")
        status_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky="w")
        self.status_value_label = tk.Label(status_frame, text="Inactive", fg="red")
        self.status_value_label.grid(row=0, column=1, sticky="w")

        self.position_label = tk.Label(status_frame, text="Position: Not Locked")
        self.position_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 10))

        self.start_stop_button = tk.Button(
            status_frame,
            text="Start Auto-Clicker",
            command=self._on_toggle_clicked,
            width=30,
            height=2,
            bg="#4CAF50",
            fg="white",
        )
        self.start_stop_button.grid(row=2, column=0, columnspan=2, pady=5)

        # Click Timing Settings
        timing_frame = tk.LabelFrame(root, text="Click Timing Settings")
        timing_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(timing_frame, text="Min Delay (sec):").grid(row=0, column=0, sticky="w")
        min_spin = tk.Spinbox(
            timing_frame,
            from_=1,
            to=50,
            increment=1,
            textvariable=self.min_delay_var,
            width=6,
        )
        min_spin.grid(row=0, column=1, sticky="w")

        tk.Label(timing_frame, text="Max Delay (sec):").grid(row=1, column=0, sticky="w")
        max_spin = tk.Spinbox(
            timing_frame,
            from_=1,
            to=50,
            increment=1,
            textvariable=self.max_delay_var,
            width=6,
        )
        max_spin.grid(row=1, column=1, sticky="w")

        # Apply button to confirm timing changes
        tk.Button(timing_frame, text="Apply", command=self._apply_delay_settings, width=8).grid(row=0, column=2, rowspan=2, padx=(10,0))

        # Inline error label (appears when invalid)
        self.timing_error_label = tk.Label(timing_frame, text="", fg="#D32F2F")
        self.timing_error_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # Applied confirmation label
        self.applied_delay_label = tk.Label(timing_frame, text="Applied: Min 1s, Max 3s", fg="#607D8B")
        self.applied_delay_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 0))

        # Apply button to confirm timing changes
        tk.Button(timing_frame, text="✔ Apply", command=self._apply_delay_settings, width=8).grid(row=0, column=2, rowspan=2, padx=(10,0))

        # Position Offset Settings
        offset_frame = tk.LabelFrame(root, text="Position Offset Settings")
        offset_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(offset_frame, text="Offset Range (±px):").grid(row=0, column=0, sticky="w")
        offset_spin = tk.Spinbox(
            offset_frame,
            from_=0,
            to=50,
            increment=1,
            textvariable=self.offset_range_var,
            width=6,
            command=self._apply_offset_settings,
        )
        offset_spin.grid(row=0, column=1, sticky="w")

        # Hotkey Configuration
        hotkey_frame = tk.LabelFrame(root, text="Hotkey Configuration")
        hotkey_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(hotkey_frame, text="Toggle Hotkey:").grid(row=0, column=0, sticky="w")
        hotkey_label = tk.Label(hotkey_frame, textvariable=self.hotkey_var)
        hotkey_label.grid(row=0, column=1, sticky="w")
        tk.Button(hotkey_frame, text="Capture Hotkey", command=self._capture_hotkey).grid(row=1, column=0, columnspan=2, pady=5)

        # Advanced Options
        adv_frame = tk.LabelFrame(root, text="Advanced Options")
        adv_frame.pack(fill="x", padx=10, pady=10)

        tk.Checkbutton(adv_frame, text="Show Status Indicator", variable=self.show_indicator_var, command=self._apply_show_indicator).grid(row=0, column=0, sticky="w")
        tk.Checkbutton(adv_frame, text="Always On Top", variable=self.always_on_top_var, command=self._apply_always_on_top).grid(row=1, column=0, sticky="w")
        tk.Checkbutton(adv_frame, text="Console Debug Output", variable=self.console_output_var, command=self._apply_console_output).grid(row=2, column=0, sticky="w")

        # Footer Buttons
        footer = tk.Frame(root)
        footer.pack(fill="x", padx=10, pady=10)

        tk.Button(footer, text="Minimize to Indicator", command=self.minimize_to_indicator).pack(side="left")
        tk.Button(footer, text="Save", command=self.save_settings).pack(side="right")

    def _bind_behaviors(self) -> None:
        # Update position preview when app locks/unlocks
        # App drives updates via update_status()
        try:
            # Only auto-apply offset; timing applies via tick button
            self.offset_range_var.trace_add('write', lambda *args: self._apply_offset_settings())
            # Validate timing inputs as user types
            self.min_delay_var.trace_add('write', lambda *args: self._validate_timing_inputs())
            self.max_delay_var.trace_add('write', lambda *args: self._validate_timing_inputs())
        except Exception:
            pass

    # Public API
    def update_status(self, is_active: bool, locked_position: Optional[Tuple[int, int]]) -> None:
        # Thread-safe UI updates
        def _apply():
            if self.status_value_label is not None:
                self.status_value_label.configure(text="Active" if is_active else "Inactive", fg="#00AA00" if is_active else "red")
            if self.start_stop_button is not None:
                if is_active:
                    self.start_stop_button.configure(text="Stop Auto-Clicker", bg="#E53935")
                else:
                    self.start_stop_button.configure(text="Start Auto-Clicker", bg="#4CAF50")
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
        self._set_timing_error(msg if not valid else "")
        self._timing_inputs_valid = valid

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

    def _apply_offset_settings(self) -> None:
        try:
            rng = int(self.offset_range_var.get())
            rng = max(0, min(50, rng))
            self.offset_range_var.set(rng)
            if hasattr(self.app, "update_offset_range"):
                self.app.update_offset_range(rng)
        except Exception:
            pass

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
