"""
Click scheduler module for ClickClick auto-clicker application.

This module manages the timing and execution of automated mouse clicks.
It coordinates the clicking behavior by running a background thread that
executes clicks at randomized intervals for natural behavior simulation.
"""

import threading
import time
import random
from typing import Optional

# Import configuration constants
from .config import MIN_CLICK_DELAY, MAX_CLICK_DELAY, CONSOLE_OUTPUT_ENABLED

# Import required modules for Phase 5 implementation
from .mouse_controller import MouseController


class ClickScheduler:
    """
    Manages click timing and coordination with background thread execution.
    
    This class is responsible for:
    - Running a background thread for non-blocking click execution
    - Coordinating click timing with randomized delays
    - Providing clean start/stop functionality
    - Thread-safe state management
    
    The scheduler implements a producer-consumer pattern where it produces
    click commands that are consumed by the mouse controller.
    
    TODO: In Phase 5, implement threading with threading.Thread
    TODO: Use random.uniform() for generating delays between clicks
    TODO: Ensure thread-safe access to is_active flag
    """

    def __init__(self, mouse_controller: MouseController) -> None:
        """
        Initialize the click scheduler.
        
        Args:
            mouse_controller: MouseController instance for executing clicks
        """
        if mouse_controller is None:
            raise ValueError("mouse_controller must not be None")
        self.mouse_controller: MouseController = mouse_controller
        self.is_active: bool = False
        self.thread: Optional[threading.Thread] = None
        # Lock to ensure thread-safe access to is_active and state changes
        self._state_lock = threading.Lock()
        # Runtime-adjustable delay bounds
        self._min_delay: float = float(MIN_CLICK_DELAY)
        self._max_delay: float = float(MAX_CLICK_DELAY)
        
        if CONSOLE_OUTPUT_ENABLED:
            print("ClickScheduler initialized")

    def start(self) -> None:
        """
        Start the click scheduler in a background thread.
        
        This method should:
        1. Set is_active to True
        2. Create a new thread running _clicking_loop()
        3. Start the thread with daemon=True for clean exit
        4. Return immediately to avoid blocking
        
        Raises:
            RuntimeError: If scheduler is already running
        """
        # Thread-safe activation
        with self._state_lock:
            if self.is_active:
                raise RuntimeError("Click scheduler is already running")
            self.is_active = True

        # Create and start the background thread
        self.thread = threading.Thread(
            target=self._clicking_loop,
            name="ClickSchedulerThread",
            daemon=True,
        )
        try:
            self.thread.start()
            if CONSOLE_OUTPUT_ENABLED:
                print("Click scheduler started")
        except Exception as e:
            # Roll back active state on failure
            with self._state_lock:
                self.is_active = False
            self.thread = None
            if CONSOLE_OUTPUT_ENABLED:
                print(f"Failed to start click scheduler thread: {e}")
            raise

    def stop(self) -> None:
        """
        Stop the click scheduler and wait for thread completion.
        
        This method:
        1. Sets is_active to False to signal thread to stop
        2. Waits for the thread to complete (join) with timeout
        3. Cleans up the thread reference
        4. Logs state transitions if enabled
        """
        # Thread-safe deactivation
        with self._state_lock:
            if not self.is_active:
                return
            self.is_active = False

        # Join the thread to wait for completion
        if self.thread is not None:
            try:
                # Timeout slightly above max delay to avoid hanging
                timeout = float(self._max_delay) + 1.0
                self.thread.join(timeout=timeout)
            except Exception as e:
                if CONSOLE_OUTPUT_ENABLED:
                    print(f"Error while joining click scheduler thread: {e}")
            finally:
                if self.thread.is_alive() and CONSOLE_OUTPUT_ENABLED:
                    print("Click scheduler thread did not exit within timeout")
                self.thread = None

        if CONSOLE_OUTPUT_ENABLED:
            print("Click scheduler stopped")

    def _clicking_loop(self) -> None:
        """
        Main clicking loop that runs in a background thread.
        
        This method:
        1. Loops while is_active is True
        2. Generates random delay using random.uniform()
        3. Sleeps for the delay duration
        4. Executes click via mouse_controller.click_at_locked_position()
        5. Handles any exceptions gracefully
        """
        while True:
            # Check active state under lock for thread safety
            with self._state_lock:
                active = self.is_active
            if not active:
                break

            try:
                # Generate random delay between configured bounds
                # Re-read under lock to avoid stale values during updates
                with self._state_lock:
                    mn = float(self._min_delay)
                    mx = float(self._max_delay)
                delay = random.uniform(mn, mx)
                time.sleep(delay)

                # Double-check active state before clicking
                with self._state_lock:
                    if not self.is_active:
                        continue

                # Execute the click
                self.mouse_controller.click_at_locked_position()
            except Exception as e:
                # Handle errors silently per requirements, with optional logging
                if CONSOLE_OUTPUT_ENABLED:
                    print(f"Click execution error: {e}")
                continue

    def get_status(self) -> dict:
        """
        Get current scheduler status information.
        
        Returns:
            dict: Status information including active state and thread info
            
        TODO: Implement status reporting for monitoring/debugging
        """
        return {
            'is_active': self.is_active,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'thread_name': self.thread.name if self.thread else None,
            'min_delay': self._min_delay,
            'max_delay': self._max_delay,
        }
        
    # TODO: Add additional methods for future features:
    # - Dynamic delay adjustment
    # - Click count tracking
    # - Scheduler statistics
    # - Pause/resume functionality
    # - Multiple scheduler support

    def set_delay_range(self, min_delay: float, max_delay: float) -> None:
        """
        Update the delay range used by the scheduler.

        Ensures reasonable bounds and min <= max.
        """
        try:
            mn = max(0.01, float(min_delay))
            mx = max(0.01, float(max_delay))
        except (TypeError, ValueError):
            return
        if mn > mx:
            mn, mx = mx, mn
        with self._state_lock:
            self._min_delay = mn
            self._max_delay = mx
        if CONSOLE_OUTPUT_ENABLED:
            print(f"[DEBUG] ClickScheduler delay range set to {self._min_delay:.2f}s - {self._max_delay:.2f}s")
