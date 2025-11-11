"""
Status indicator GUI module for ClickClick auto-clicker application.

This module creates a minimal GUI overlay that displays the current
application state through a colored circular indicator. The indicator
appears as a small overlay in a screen corner and changes color
based on whether the auto-clicker is active or inactive.
"""

import time
import tkinter as tk
from typing import Optional, Tuple, Callable

# Import configuration constants
from .config import (
    INDICATOR_SIZE, INDICATOR_POSITION, INDICATOR_COLOR_ACTIVE,
    INDICATOR_COLOR_INACTIVE, INDICATOR_OPACITY, INDICATOR_MARGIN
)

# TODO: Import configuration constants in Phase 4 implementation


class StatusIndicator:
    """
    Creates and manages a minimal GUI overlay for status indication.
    
    This class is responsible for:
    - Creating a transparent, frameless tkinter window overlay
    - Drawing a circular indicator that changes color based on state
    - Positioning the indicator in a configurable screen corner
    - Providing clean show_active/show_inactive state transitions
    
    The indicator uses tkinter because it's built into Python and
    provides sufficient functionality for a simple overlay without
    adding external dependencies.
    
    TODO: In Phase 4, implement tkinter window creation
    TODO: Handle cross-platform transparency differences
    TODO: Use Canvas for circular drawing with color changes
    """

    def __init__(self, on_click: Optional[Callable[[], None]] = None) -> None:
        """
        Initialize the status indicator GUI.
        
        Sets up the tkinter root window, configures it as an overlay,
        creates the circular drawing, and positions it on screen.
        """
        self.root: Optional[tk.Tk] = tk.Tk()
        self.canvas: Optional[tk.Canvas] = None
        self.circle_id: Optional[int] = None
        self.arc_id: Optional[int] = None
        self._on_click_cb = on_click
        self._countdown_target_ts: Optional[float] = None
        self._countdown_total_interval: Optional[float] = None
        self._countdown_after: Optional[str] = None
        self._is_active: bool = False

        # Configure window and create the indicator
        self._setup_window()
        self._create_canvas()
        self._bind_click()

    def show_active(self) -> None:
        """
        Change the indicator to active state (green color).
        Uses tkinter's after to be thread-safe if invoked from non-GUI threads.
        """
        self._is_active = True
        if self.root is not None and self.canvas is not None and self.circle_id is not None:
            self.root.after(0, lambda: self.canvas.itemconfig(self.circle_id, fill=INDICATOR_COLOR_ACTIVE))

    def show_inactive(self) -> None:
        """
        Change the indicator to inactive state (red color).
        Uses tkinter's after to be thread-safe if invoked from non-GUI threads.
        """
        self._is_active = False
        self.set_countdown_eta(None)
        if self.root is not None and self.canvas is not None and self.circle_id is not None:
            self.root.after(0, lambda: self.canvas.itemconfig(self.circle_id, fill=INDICATOR_COLOR_INACTIVE))

    def set_countdown_eta(self, seconds: Optional[float]) -> None:
        """
        Update the countdown overlay to represent the remaining time until the next click.
        """
        if self.root is None:
            return

        def _apply() -> None:
            self._apply_countdown_eta(seconds)

        try:
            self.root.after(0, _apply)
        except Exception:
            _apply()

    def destroy(self) -> None:
        """
        Close the indicator window and cleanup resources.
        """
        if self.root is not None:
            try:
                # Safely destroy the tkinter window
                self.root.destroy()
            except tk.TclError:
                # Window may already be destroyed; ignore
                pass
            finally:
                # Reset references
                if self._countdown_after is not None:
                    try:
                        self.root.after_cancel(self._countdown_after)
                    except Exception:
                        pass
                self._countdown_after = None
                self.root = None
                self.canvas = None
                self.circle_id = None
                self.arc_id = None

    def _bind_click(self) -> None:
        """
        Bind mouse click on the indicator to callback to restore the main window.
        """
        if self.root is None or self.canvas is None:
            return
        try:
            def handle_click(event=None):
                try:
                    if callable(self._on_click_cb):
                        self._on_click_cb()
                except Exception:
                    pass
            # Bind both left click on canvas and entire window
            self.canvas.bind("<Button-1>", handle_click)
            self.root.bind("<Button-1>", handle_click)
        except Exception:
            pass

    def _calculate_position(self) -> Tuple[int, int]:
        """
        Calculate the screen position for the indicator based on config.

        Positions in one of the four corners with INDICATOR_MARGIN offset.

        Returns:
            Tuple[int, int]: (x, y) coordinates for window placement
        """
        if self.root is None:
            return 0, 0

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        size = INDICATOR_SIZE
        margin = INDICATOR_MARGIN
        position = (INDICATOR_POSITION or 'top-right').lower()

        # Vertical position
        if 'top' in position:
            y = margin
        elif 'bottom' in position:
            y = max(0, screen_height - size - margin)
        else:
            # Default to top if unspecified
            y = margin

        # Horizontal position
        if 'left' in position:
            x = margin
        elif 'right' in position:
            x = max(0, screen_width - size - margin)
        else:
            # Default to right if unspecified
            x = max(0, screen_width - size - margin)

        return x, y

    def _setup_window(self) -> None:
        """
        Configure the tkinter window for overlay display.

        - Frameless (overrideredirect)
        - Always on top
        - Transparency via alpha, with Windows-specific color key
        - Window sized and positioned according to configuration
        """
        if self.root is None:
            return

        # Remove window decorations and keep on top
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)

        # Base window background set to white. On Windows, we make this white fully transparent.
        self.root.configure(bg='white')

        # Clamp and apply opacity if supported
        try:
            opacity = float(INDICATOR_OPACITY)
        except (TypeError, ValueError):
            opacity = 0.7
        opacity = max(0.0, min(1.0, opacity))
        try:
            self.root.attributes('-alpha', opacity)
        except tk.TclError:
            # Some platforms/window managers may not support alpha
            pass

        # Platform-specific transparency handling
        try:
            import platform
            if platform.system() == 'Windows':
                # Make white color fully transparent on Windows
                self.root.attributes('-transparentcolor', 'white')
        except Exception:
            # Be conservative: any platform-specific issues are non-fatal
            pass

        # Disable resizing
        self.root.resizable(False, False)

        # Set window size and position
        x, y = self._calculate_position()
        self.root.geometry(f'{INDICATOR_SIZE}x{INDICATOR_SIZE}+{x}+{y}')

    def _create_canvas(self) -> None:
        """
        Create and configure the canvas for circular drawing.
        
        - Creates a tkinter Canvas sized to INDICATOR_SIZE
        - Draws a circle occupying the full INDICATOR_SIZE (30x30 pixels)
        - Initializes the circle color to inactive (red)
        """
        if self.root is None:
            return

        self.canvas = tk.Canvas(
            self.root,
            width=INDICATOR_SIZE,
            height=INDICATOR_SIZE,
            highlightthickness=0,
            bg='white',
            bd=0
        )
        self.canvas.pack()

        # Draw circle with no margin to meet 30x30 requirement
        margin = 0
        self.circle_id = self.canvas.create_oval(
            margin,
            margin,
            INDICATOR_SIZE - margin,
            INDICATOR_SIZE - margin,
            fill=INDICATOR_COLOR_INACTIVE,
            outline=''
        )

        arc_margin = 2
        self.arc_id = self.canvas.create_arc(
            arc_margin,
            arc_margin,
            INDICATOR_SIZE - arc_margin,
            INDICATOR_SIZE - arc_margin,
            start=90,
            extent=0,
            style="arc",
            outline="#F9FAFB",
            width=3,
            state="hidden",
        )

    def _apply_countdown_eta(self, seconds: Optional[float]) -> None:
        if seconds is None or seconds <= 0 or not self._is_active:
            self._countdown_target_ts = None
            self._countdown_total_interval = None
            self._update_countdown_arc()
            return
        self._countdown_target_ts = time.monotonic() + float(seconds)
        self._countdown_total_interval = float(seconds)
        self._update_countdown_arc()
        self._ensure_countdown_loop()

    def _ensure_countdown_loop(self) -> None:
        if self.root is None or self._countdown_after is not None:
            return

        def _tick() -> None:
            self._countdown_after = None
            self._update_countdown_arc()
            if self._countdown_target_ts is not None:
                self._ensure_countdown_loop()

        self._countdown_after = self.root.after(120, _tick)

    def _update_countdown_arc(self) -> None:
        if self.canvas is None or self.arc_id is None:
            return
        if (
            not self._is_active
            or self._countdown_target_ts is None
            or self._countdown_total_interval is None
            or self._countdown_total_interval <= 0
        ):
            self.canvas.itemconfigure(self.arc_id, state="hidden", extent=0)
            return

        remaining = max(0.0, self._countdown_target_ts - time.monotonic())
        if remaining <= 0:
            self.canvas.itemconfigure(self.arc_id, state="hidden", extent=0)
            self._countdown_target_ts = None
            self._countdown_total_interval = None
            return

        fraction = max(0.0, min(1.0, remaining / self._countdown_total_interval))
        extent = -360 * fraction  # clockwise
        self.canvas.itemconfigure(self.arc_id, state="normal", extent=extent)
        
    # TODO: Add additional methods for future features:
    # - Multiple indicator support (multi-monitor)
    # - Custom shapes beyond circles
    # - Animation effects for state changes
    # - Configuration UI for indicator appearance
    # - Status text display (optional)
