"""
Main application controller for ClickClick auto-clicker application.

This module serves as the entry point and main orchestrator for the
ClickClick application. It coordinates all components and manages the
application lifecycle including startup, shutdown, and state management.

The main application class is responsible for:
- Initializing all application components
- Managing application state (active/inactive)
- Coordinating between hotkey handler, click scheduler, mouse controller, and status indicator
- Handling graceful shutdown on Ctrl+C
- Running the tkinter main event loop
"""

import signal
import sys
from typing import Optional, Tuple

# Import configuration constants
from .config import CONSOLE_OUTPUT_ENABLED

from .mouse_controller import MouseController
from .click_scheduler import ClickScheduler
from .hotkey_handler import HotkeyHandler
from .status_indicator import StatusIndicator
from .config import MIN_CLICK_DELAY, MAX_CLICK_DELAY, POSITION_OFFSET_RANGE
from .gui_window import GUIWindow


class ClickClickApp:
    """
    Main application controller for ClickClick auto-clicker.
    
    This class orchestrates all application components and manages
    the overall application state and lifecycle. It follows the
    Application Controller pattern to coordinate between different modules.
    
    The application has two main states:
    - Inactive: Auto-clicker is stopped, indicator shows red
    - Active: Auto-clicker is running, indicator shows green
    
    TODO: In Phase 7, implement full application coordination logic
    TODO: Handle state transitions between active/inactive
    TODO: Manage component lifecycle and cleanup
    """

    def __init__(self) -> None:
        """
        Initialize the ClickClick application.
        
        Sets up all application components and initial state.
        Components are created but not started until run() is called.
        """
        # Application state
        self.is_active: bool = False
        self.locked_position: Optional[Tuple[int, int]] = None
        self.running: bool = True

        # Initialize application components
        self.mouse_controller = MouseController()
        self.click_scheduler = ClickScheduler(self.mouse_controller)
        self.click_scheduler.set_next_delay_callback(self._handle_next_delay)
        # Status indicator overlay with restore callback
        self.status_indicator = StatusIndicator(on_click=self._restore_main_window)
        self.hotkey_handler = HotkeyHandler(self.toggle_clicking)
        # GUI control window attached to indicator's root if available
        parent_root = self.status_indicator.root if self.status_indicator.root is not None else None
        self.gui = GUIWindow(self, parent_root=parent_root)

    def toggle_clicking(self) -> None:
        """
        Toggle the auto-clicker between active and inactive states.
        
        This callback function is called by the hotkey handler when
        the configured hotkey is pressed. It manages the transition
        between application states and coordinates all components.
        """
        if not self.is_active:
            # Transition from inactive to active
            try:
                # Lock current mouse position
                self.mouse_controller.lock_current_position()
                self.locked_position = self.mouse_controller.locked_position

                # Start clicking
                self.click_scheduler.start()

                # Update indicator to active state
                self.status_indicator.show_active()
                # Update GUI status
                self.gui.update_status(True, self.locked_position)
                self.is_active = True
            except Exception:
                # Rollback on failure while remaining silent
                try:
                    self.click_scheduler.stop()
                except Exception:
                    pass
                try:
                    self.mouse_controller.unlock_position()
                except Exception:
                    pass
                try:
                    self.status_indicator.show_inactive()
                except Exception:
                    pass
                try:
                    self.gui.update_status(False, None)
                except Exception:
                    pass
                self.locked_position = None
                self.is_active = False
        else:
            # Transition from active to inactive
            try:
                # Stop clicking
                self.click_scheduler.stop()
            except Exception:
                pass

            # Unlock position
            try:
                self.mouse_controller.unlock_position()
            except Exception:
                pass
            self.locked_position = None

            # Update indicator to inactive state
            try:
                self.status_indicator.show_inactive()
            except Exception:
                pass
            try:
                self.gui.update_status(False, None)
            except Exception:
                pass
            self.is_active = False
            self._handle_next_delay(None)

    def run(self) -> None:
        """
        Start the application and enter the main event loop.
        
        - Starts hotkey listener
        - Shows initial inactive indicator
        - Registers Ctrl+C handler
        - Enters tkinter main loop
        """
        try:
            # Show initial inactive state
            self.status_indicator.show_inactive()

            # Start hotkey handler
            self.hotkey_handler.start()

            # Set up signal handler for Ctrl+C
            signal.signal(signal.SIGINT, self._signal_handler)

            # Enter main GUI event loop via shared root
            if self.status_indicator.root is not None:
                self.status_indicator.root.mainloop()
        except KeyboardInterrupt:
            # Graceful shutdown on Ctrl+C
            self._signal_handler(signal.SIGINT, None)
        except Exception as e:
            # Handle errors silently with optional console logging
            if CONSOLE_OUTPUT_ENABLED:
                print(f"Application error: {e}")
            self.cleanup()

    def _handle_next_delay(self, seconds: Optional[float]) -> None:
        try:
            self.gui.update_next_click_eta(seconds)
            if hasattr(self, "status_indicator") and hasattr(self.status_indicator, "set_countdown_eta"):
                self.status_indicator.set_countdown_eta(seconds)
        except Exception:
            pass

    def cleanup(self) -> None:
        """
        Clean up all application resources before exit.
        
        Ensures scheduler, hotkey handler, and indicator are stopped/destroyed.
        Handles exceptions silently per project requirements.
        """
        if CONSOLE_OUTPUT_ENABLED:
            print("[DEBUG] cleanup() called - starting application shutdown")
        try:
            if self.is_active:
                try:
                    self.click_scheduler.stop()
                except Exception:
                    pass

            try:
                if CONSOLE_OUTPUT_ENABLED:
                    print("[DEBUG] Stopping hotkey handler...")
                self.hotkey_handler.stop()
                if CONSOLE_OUTPUT_ENABLED:
                    print("[DEBUG] Hotkey handler stopped")
            except Exception as e:
                if CONSOLE_OUTPUT_ENABLED:
                    print(f"[DEBUG] Error stopping hotkey handler: {e}")
                pass

            try:
                self.status_indicator.destroy()
            except Exception:
                pass
            try:
                # Attempt to destroy GUI window if separate
                if getattr(self.gui, 'window', None) is not None:
                    self.gui.window.destroy()
            except Exception:
                pass
        except Exception as e:
            if CONSOLE_OUTPUT_ENABLED:
                print(f"Cleanup error: {e}")
        finally:
            self.running = False
            if CONSOLE_OUTPUT_ENABLED:
                print("[DEBUG] Calling sys.exit(0) to terminate process")
            try:
                # Ensure full process exit when cleanup requested from GUI close
                sys.exit(0)
            except SystemExit:
                if CONSOLE_OUTPUT_ENABLED:
                    print("[DEBUG] SystemExit raised - process should terminate")
                pass

    def _signal_handler(self, signum, frame) -> None:
        """
        Handle system signals (like Ctrl+C) for graceful shutdown.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        try:
            self.cleanup()
        finally:
            try:
                sys.exit(0)
            except SystemExit:
                # Re-raise to propagate exit cleanly
                raise

    def get_status(self) -> dict:
        """
        Get current application status information.
        
        Returns:
            dict: Current application state information
        """
        return {
            'is_active': self.is_active,
            'locked_position': self.locked_position,
            'running': self.running
        }

    # GUI integration helpers
    def _restore_main_window(self) -> None:
        """
        Callback for status indicator click to restore GUI window.
        """
        try:
            self.gui.restore_window()
        except Exception:
            pass

    def _on_close_window(self) -> None:
        """
        Close callback from GUI window: exit the app entirely.
        """
        try:
            self.cleanup()
        except Exception:
            pass

    def update_delay_range(self, min_delay: float, max_delay: float) -> None:
        """
        Called by GUI when delay settings change.
        """
        try:
            self.click_scheduler.set_delay_range(min_delay, max_delay)
            # If currently active, restart scheduler to adopt changes immediately
            if self.is_active:
                try:
                    self.click_scheduler.stop()
                except Exception:
                    pass
                try:
                    self.click_scheduler.start()
                except Exception:
                    pass
        except Exception:
            pass

    def update_offset_range(self, rng: int) -> None:
        """
        Called by GUI when offset settings change.
        """
        try:
            self.mouse_controller.set_offset_range(rng)
            if hasattr(self, "gui") and hasattr(self.gui, "reflect_offset_range"):
                self.gui.reflect_offset_range(rng)
        except Exception:
            pass


if __name__ == '__main__':
    app = ClickClickApp()
    app.run()
