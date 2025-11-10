"""
Hotkey handler module for ClickClick auto-clicker application.

This module handles keyboard input detection and hotkey processing.
It listens for the configured toggle hotkey (numpad 5) and triggers
the application's toggle callback when pressed.
"""

from typing import Callable, Optional

# Import pynput keyboard components
from pynput.keyboard import Key, Listener, KeyCode

# Import configuration
from .config import TOGGLE_HOTKEY, CONSOLE_OUTPUT_ENABLED


class HotkeyHandler:
    """
    Manages keyboard hotkey detection and callback execution.
    
    This class is responsible for:
    - Listening for keyboard events in a background thread
    - Detecting the configured hotkey press
    - Calling the application toggle callback when hotkey is pressed
    - Running non-blockingly to avoid interfering with GUI
    
    TODO: In Phase 6, use pynput.keyboard.Listener for key detection
    TODO: Handle both keyboard.Key and keyboard.KeyCode types
    TODO: Use TOGGLE_HOTKEY from config to determine which key to listen for
    """

    def __init__(self, toggle_callback: Callable[[], None]) -> None:
        """
        Initialize the hotkey handler.

        Args:
            toggle_callback: Function to call when hotkey is pressed
        """
        if not callable(toggle_callback):
            raise TypeError("toggle_callback must be callable")

        self.toggle_callback: Callable[[], None] = toggle_callback

        # Hotkey matching configuration (runtime adjustable)
        # Prefer virtual key code when available (Windows Numpad5 = 101)
        self._hotkey_vk: Optional[int] = None
        self._hotkey_char: Optional[str] = None
        self._hotkey_name: Optional[str] = None

        # Map default TOGGLE_HOTKEY to a sensible default
        # Current default: 'num_5' => VK 101 on Windows
        if isinstance(TOGGLE_HOTKEY, str) and TOGGLE_HOTKEY.lower() in {"num_5", "numpad5", "numpad_5"}:
            self._hotkey_vk = 101

        # Initialize pynput keyboard listener, but do not start yet
        # Use _on_press as the callback for key press events
        self._listener: Optional[Listener] = Listener(on_press=self._on_press)

        # Ensure listener runs as a daemon when started to avoid blocking shutdown
        self._listener.daemon = True

    def start(self) -> None:
        """
        Start keyboard listening in a non-blocking background thread.

        The listener runs in the background and does not block the main thread.
        Safe to call multiple times; will only start if not already running.
        """
        try:
            if self._listener is None:
                # Recreate listener if it was previously cleaned up
                self._listener = Listener(on_press=self._on_press)
                self._listener.daemon = True

            # Start only if not already running
            if not getattr(self._listener, "running", False):
                self._listener.start()
                if CONSOLE_OUTPUT_ENABLED:
                    print(f"[DEBUG] Hotkey listener started. Configured hotkey vk={self._hotkey_vk} char={self._hotkey_char} name={self._hotkey_name}")
        except Exception as e:
            # Prevent any startup errors from crashing the application
            if CONSOLE_OUTPUT_ENABLED:
                print(f"[DEBUG] Error starting listener: {e}")
            pass

    def stop(self) -> None:
        """
        Stop keyboard listening and cleanup resources.

        Ensures a clean shutdown of the listener thread.
        """
        if CONSOLE_OUTPUT_ENABLED:
            print("[DEBUG] HotkeyHandler.stop() called")
        
        if self._listener is not None:
            try:
                if CONSOLE_OUTPUT_ENABLED:
                    print("[DEBUG] Calling listener.stop()...")
                self._listener.stop()
                
                if CONSOLE_OUTPUT_ENABLED:
                    print("[DEBUG] Attempting to join listener thread with 0.5s timeout...")
                # Attempt to join briefly for clean shutdown; ignore if unsupported
                try:
                    self._listener.join(timeout=0.5)
                    if CONSOLE_OUTPUT_ENABLED:
                        print("[DEBUG] Listener thread joined successfully")
                except Exception as e:
                    if CONSOLE_OUTPUT_ENABLED:
                        print(f"[DEBUG] Exception during listener.join(): {e}")
                    pass
            except Exception as e:
                # Prevent shutdown errors from bubbling up
                if CONSOLE_OUTPUT_ENABLED:
                    print(f"[DEBUG] Exception during listener.stop(): {e}")
                pass
            finally:
                self._listener = None
                if CONSOLE_OUTPUT_ENABLED:
                    print("[DEBUG] Listener set to None")

    def set_hotkey(self, vk: Optional[int] = None, char: Optional[str] = None, name: Optional[str] = None) -> None:
        """
        Update the hotkey matching configuration.

        Args:
            vk: Virtual key code (int, e.g., 101 for Numpad 5 on Windows)
            char: Single character to match (e.g., 'x')
            name: String form of Key enum (e.g., 'Key.f8')
        """
        try:
            self._hotkey_vk = int(vk) if vk is not None else None
        except (TypeError, ValueError):
            self._hotkey_vk = None
        if isinstance(char, str) and len(char) == 1:
            self._hotkey_char = char
        else:
            self._hotkey_char = None
        if isinstance(name, str) and name.startswith("Key."):
            self._hotkey_name = name
        else:
            self._hotkey_name = None

    def _on_press(self, key) -> None:
        """
        Callback function for keyboard press events.

        Detects the configured hotkey (numpad 5) and invokes the toggle callback.
        Handles both Key and KeyCode types safely without crashing.

        Args:
            key: The key that was pressed (pynput.keyboard.Key or KeyCode)
        """
        try:
            # DEBUG: Log every key press to understand what we're receiving
            if CONSOLE_OUTPUT_ENABLED:
                print(f"[DEBUG] Key pressed: {key}")
                print(f"[DEBUG]   Type: {type(key)}")
                if hasattr(key, 'vk'):
                    print(f"[DEBUG]   Virtual Key Code: {key.vk}")
                if hasattr(key, 'char'):
                    print(f"[DEBUG]   Char: {key.char}")
            
            # Match order: vk -> char -> name
            is_hotkey_match = False

            if isinstance(key, KeyCode):
                # Prefer virtual key code when present
                if self._hotkey_vk is not None and hasattr(key, 'vk') and key.vk == self._hotkey_vk:
                    is_hotkey_match = True
                elif self._hotkey_char is not None and getattr(key, 'char', None):
                    try:
                        if str(key.char).lower() == str(self._hotkey_char).lower():
                            is_hotkey_match = True
                    except Exception:
                        pass
            else:
                # pynput Key enum
                if self._hotkey_name is not None:
                    if str(key) == self._hotkey_name:
                        is_hotkey_match = True

            if is_hotkey_match:
                if CONSOLE_OUTPUT_ENABLED:
                    print("[DEBUG] Hotkey matched. Calling toggle_callback().")
                self.toggle_callback()
            elif CONSOLE_OUTPUT_ENABLED:
                pass
                
        except AttributeError as e:
            # Some special keys may raise AttributeError; prevent listener crash
            if CONSOLE_OUTPUT_ENABLED:
                print(f"[DEBUG] AttributeError in _on_press: {e}")
            pass
        except Exception as e:
            # Guard against any unexpected errors from callback or comparison
            if CONSOLE_OUTPUT_ENABLED:
                print(f"[DEBUG] Exception in _on_press: {e}")
            pass

    # TODO: Add additional methods for future features:
    # - Multiple hotkey support
    # - Hotkey combination detection
    # - Key press/release distinction
    # - Hotkey customization interface
