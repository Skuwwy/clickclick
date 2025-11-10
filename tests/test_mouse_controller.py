"""
Unit tests for the MouseController module.

Validates:
- Position locking captures correct coordinates (object with x/y attrs and tuple)
- Random offsets are within ±POSITION_OFFSET_RANGE pixels
- Clicks execute at correct positions when locked
- Silent error handling during click
"""

import unittest
from unittest.mock import patch

from src.mouse_controller import MouseController
from src.config import POSITION_OFFSET_RANGE


class TestMouseController(unittest.TestCase):
    """Tests for MouseController behavior."""

    def test_lock_current_position_captures_correct_coordinates_with_xy_attrs(self) -> None:
        """lock_current_position stores current mouse coordinates when position has x/y attrs."""
        controller = MouseController()
        fake_point = type("Point", (), {"x": 150, "y": 275})()

        with patch("src.mouse_controller.pyautogui.position", return_value=fake_point):
            controller.lock_current_position()

        self.assertEqual(controller.locked_position, (150, 275))

    def test_lock_current_position_captures_correct_coordinates_with_tuple(self) -> None:
        """lock_current_position stores current mouse coordinates when position is a tuple."""
        controller = MouseController()
        fake_point = (321, 654)

        with patch("src.mouse_controller.pyautogui.position", return_value=fake_point):
            controller.lock_current_position()

        self.assertEqual(controller.locked_position, (321, 654))

    def test_random_offsets_within_range(self) -> None:
        """_get_random_offset returns values within +/- POSITION_OFFSET_RANGE."""
        controller = MouseController()

        for _ in range(200):
            ox, oy = controller._get_random_offset()
            self.assertGreaterEqual(ox, -POSITION_OFFSET_RANGE)
            self.assertLessEqual(ox, POSITION_OFFSET_RANGE)
            self.assertGreaterEqual(oy, -POSITION_OFFSET_RANGE)
            self.assertLessEqual(oy, POSITION_OFFSET_RANGE)

    def test_click_executes_at_correct_position(self) -> None:
        """click_at_locked_position calls pyautogui.click with locked position plus offset."""
        controller = MouseController()
        controller.locked_position = (100, 200)

        with patch.object(MouseController, "_get_random_offset", return_value=(2, -3)):
            with patch("src.mouse_controller.pyautogui.click") as mock_click:
                controller.click_at_locked_position()
                mock_click.assert_called_once_with(x=102, y=197)

    def test_click_does_nothing_when_position_not_locked(self) -> None:
        """click_at_locked_position returns early when no position is locked."""
        controller = MouseController()
        controller.locked_position = None

        with patch("src.mouse_controller.pyautogui.click") as mock_click:
            controller.click_at_locked_position()
            mock_click.assert_not_called()

    def test_click_silent_error_handling(self) -> None:
        """Errors during click are caught and do not propagate."""
        controller = MouseController()
        controller.locked_position = (50, 60)

        with patch("src.mouse_controller.pyautogui.click", side_effect=RuntimeError("boom")):
            # Ensure logging is disabled to keep output silent
            with patch("src.mouse_controller.CONSOLE_OUTPUT_ENABLED", False):
                # Should not raise
                controller.click_at_locked_position()


if __name__ == "__main__":
    unittest.main()