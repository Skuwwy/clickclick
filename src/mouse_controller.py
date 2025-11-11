"""
Mouse controller module for ClickClick auto-clicker application.

This module handles all mouse-related operations including:
- Capturing and locking mouse position
- Executing clicks with randomization
- Position offset calculation for natural clicking behavior
"""

import random
from typing import Optional, Tuple

# Import configuration constants
from .config import POSITION_OFFSET_RANGE, CONSOLE_OUTPUT_ENABLED

# Import pyautogui for mouse control with graceful fallback when unavailable
try:
    import pyautogui  # type: ignore
except Exception as import_error:  # pragma: no cover - exercised in headless CI
    class _PyAutoGUIStub:
        """Minimal stub replicating PyAutoGUI surface for test environments."""

        FAILSAFE = False

        @staticmethod
        def position() -> Tuple[int, int]:
            return (0, 0)

        @staticmethod
        def click(*_args, **_kwargs) -> None:
            return None

    pyautogui = _PyAutoGUIStub()  # type: ignore[assignment]
    if CONSOLE_OUTPUT_ENABLED:
        print(f"[DEBUG] Using PyAutoGUI stub due to import error: {import_error}")


class MouseController:
    """
    Manages mouse position locking and click execution with randomization.
    
    This class is responsible for:
    - Capturing the current mouse position when auto-clicking starts
    - Calculating random offsets for natural clicking behavior
    - Executing clicks at the locked position with small random variations
    """

    def __init__(self) -> None:
        """
        Initialize the mouse controller.
        
        Sets up the locked_position attribute to None, indicating no position
        is currently locked for clicking.
        """
        self.locked_position: Optional[Tuple[int, int]] = None
        # Runtime-adjustable offset range (defaults to config)
        self.offset_range: int = POSITION_OFFSET_RANGE
        
        # PyAutoGUI configuration (fail-safe settings)
        # Fail-safe allows moving the mouse to a corner to abort operations
        try:
            pyautogui.FAILSAFE = True
        except Exception:
            # Keep silent to avoid crashing in environments where pyautogui
            # configuration may not be available.
            if CONSOLE_OUTPUT_ENABLED:
                print("PyAutoGUI fail-safe configuration could not be set")

    def lock_current_position(self) -> None:
        """
        Capture and lock the current mouse position.
        
        This method should be called when the auto-clicker is activated
        to capture the position where clicks should be performed.
        """
        try:
            pos = pyautogui.position()
            # Support both Point-like objects and tuples
            if hasattr(pos, "x") and hasattr(pos, "y"):
                x = int(pos.x)
                y = int(pos.y)
            else:
                x = int(pos[0])
                y = int(pos[1])
            self.locked_position = (x, y)
            if CONSOLE_OUTPUT_ENABLED:
                print(f"Locked mouse position at ({x}, {y})")
        except Exception as e:
            # Silent failure per requirements
            if CONSOLE_OUTPUT_ENABLED:
                print(f"Failed to lock mouse position: {e}")
    def unlock_position(self) -> None:
        """
        Clear the locked mouse position.
        
        This method should be called when the auto-clicker is deactivated
        to release the position lock.
        """
        prev = self.locked_position
        self.locked_position = None
        if CONSOLE_OUTPUT_ENABLED:
            if prev is not None:
                print(f"Unlocked mouse position from {prev}")
            else:
                print("Unlock requested but no position was locked")

    def click_at_locked_position(self) -> None:
        """
        Execute a click at the locked position with random offset.
        
        This method should:
        1. Check if a position is currently locked
        2. Calculate a random offset within the configured range
        3. Execute a click at the offset position using PyAutoGUI
        4. Handle errors gracefully with silent failure
        """
        if self.locked_position is None:
            return
        
        try:
            # Calculate offset and target position
            offset_x, offset_y = self._get_random_offset()
            target_x = int(self.locked_position[0] + offset_x)
            target_y = int(self.locked_position[1] + offset_y)
            
            if CONSOLE_OUTPUT_ENABLED:
                print(f"Clicking at ({target_x}, {target_y}) with offset ({offset_x}, {offset_y})")
            
            # Execute the click
            pyautogui.click(x=target_x, y=target_y)
        except Exception as e:
            # Silent failure per requirements
            if CONSOLE_OUTPUT_ENABLED:
                print(f"Click execution error: {e}")


    def set_offset_range(self, value: int) -> None:
        """
        Update the position offset range used for randomization.

        Clamps the value to a reasonable range [0, 50].
        """
        try:
            v = int(value)
        except (TypeError, ValueError):
            return
        self.offset_range = max(0, min(50, v))

    def _get_random_offset(self) -> Tuple[int, int]:
        """
        Calculate random offset within the configured position range.
        
        Returns a tuple (offset_x, offset_y) where each value is randomly
        chosen within the range [-POSITION_OFFSET_RANGE, POSITION_OFFSET_RANGE].
        
        Returns:
            Tuple[int, int]: Random offset coordinates
        """
        rng = int(self.offset_range)
        offset_x = random.randint(-rng, rng)
        offset_y = random.randint(-rng, rng)
        return (offset_x, offset_y)
