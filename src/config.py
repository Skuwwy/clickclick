"""
Configuration module for ClickClick auto-clicker application.

This module contains all configuration constants used throughout the application.
It centralizes all settings in one place to eliminate magic numbers and make
the application easily configurable.
"""

# Hotkey Configuration
TOGGLE_HOTKEY: str = 'num_5'  # Numpad 5 key for toggling auto-clicker

# Click Timing Configuration
MIN_CLICK_DELAY: float = 1.0  # Minimum delay between clicks (seconds)
MAX_CLICK_DELAY: float = 3.0  # Maximum delay between clicks (seconds)

# Position Randomization Configuration
POSITION_OFFSET_RANGE: int = 3  # ±3 pixels range for click position randomization

# Visual Indicator Configuration
INDICATOR_SIZE: int = 30  # Size of the circular indicator in pixels
INDICATOR_POSITION: str = 'top-right'  # Options: 'top-right', 'top-left', 'bottom-right', 'bottom-left'
INDICATOR_COLOR_ACTIVE: str = '#00FF00'  # Green color for active state
INDICATOR_COLOR_INACTIVE: str = '#FF0000'  # Red color for inactive state
INDICATOR_OPACITY: float = 0.7  # Transparency level (0.0 to 1.0)

# Debug Configuration
CONSOLE_OUTPUT_ENABLED: bool = False  # Set to True for console logging during development

# TODO: Add additional configuration options for future features:
# - Multiple click types (right-click, double-click)
# - Multiple hotkeys
# - Click patterns and sequences
# - Advanced randomization algorithms
# - GUI settings window preferences