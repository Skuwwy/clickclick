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
from config import TOGGLE_HOTKEY, CONSOLE_OUTPUT_ENABLED


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
                    print(f"[DEBUG] Hotkey listener started. Configured hotkey: {TOGGLE_HOTKEY}")
                    print(f"[DEBUG] Checking for Key enum value: Key.num_5")
                    print(f"[DEBUG] Press Numpad 5 to see key detection...")
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
        if self._listener is not None:
            try:
                self._listener.stop()
                # Attempt to join briefly for clean shutdown; ignore if unsupported
                try:
                    self._listener.join(timeout=0.5)
                except Exception:
                    pass
            except Exception:
                # Prevent shutdown errors from bubbling up
                pass
            finally:
                self._listener = None

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
            
            # Check for Numpad 5 key
            # Numpad 5 with NumLock ON sends KeyCode with vk=101 on Windows
            # We check for KeyCode type and the specific virtual key code
            is_hotkey_match = False
            
            if isinstance(key, KeyCode):
                # Numpad 5 with NumLock ON has virtual key code 101 (VK_NUMPAD5)
                if key.vk == 101:
                    is_hotkey_match = True
                    if CONSOLE_OUTPUT_ENABLED:
                        print(f"[DEBUG] HOTKEY MATCHED! (KeyCode vk=101 - Numpad 5)")
            
            if is_hotkey_match:
                if CONSOLE_OUTPUT_ENABLED:
                    print("[DEBUG] Calling toggle_callback()")
                self.toggle_callback()
            elif CONSOLE_OUTPUT_ENABLED:
                print(f"[DEBUG] No match (expected Numpad 5 with vk=101)")
                print()
                
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