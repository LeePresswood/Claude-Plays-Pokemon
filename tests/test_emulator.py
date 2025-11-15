"""
Unit tests for emulator integration

Test-driven development: Write tests first, then implement features.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image


class TestEmulatorCapture:
    """Tests for screenshot capture functionality"""

    def test_find_window_success(self):
        """Should find emulator window when it exists"""
        from src.emulator.capture import EmulatorCapture

        with patch('src.emulator.capture.gw.getWindowsWithTitle') as mock_get_windows:
            # Mock window found
            mock_window = Mock()
            mock_window.title = "mGBA - Pokemon Red"
            mock_get_windows.return_value = [mock_window]

            capture = EmulatorCapture(window_title="mGBA")
            result = capture.find_window()

            assert result is True
            assert capture.window == mock_window
            mock_get_windows.assert_called_once_with("mGBA")

    def test_find_window_not_found(self):
        """Should return False when window doesn't exist"""
        from src.emulator.capture import EmulatorCapture

        with patch('src.emulator.capture.gw.getWindowsWithTitle') as mock_get_windows:
            mock_get_windows.return_value = []

            capture = EmulatorCapture(window_title="mGBA")
            result = capture.find_window()

            assert result is False
            assert capture.window is None

    def test_capture_screenshot_success(self):
        """Should capture screenshot when window is found"""
        from src.emulator.capture import EmulatorCapture

        with patch('src.emulator.capture.gw.getWindowsWithTitle') as mock_get_windows, \
             patch('src.emulator.capture.pyautogui.screenshot') as mock_screenshot:

            # Setup mocks
            mock_window = Mock()
            mock_window.left, mock_window.top = 100, 100
            mock_window.width, mock_window.height = 640, 576
            mock_get_windows.return_value = [mock_window]

            mock_image = Mock(spec=Image.Image)
            mock_screenshot.return_value = mock_image

            # Test
            capture = EmulatorCapture(window_title="mGBA")
            capture.find_window()
            result = capture.capture_screenshot()

            assert result == mock_image
            mock_screenshot.assert_called_once_with(region=(100, 100, 640, 576))

    def test_capture_screenshot_no_window(self):
        """Should return None when no window found"""
        from src.emulator.capture import EmulatorCapture

        capture = EmulatorCapture(window_title="mGBA")
        result = capture.capture_screenshot()

        assert result is None


class TestEmulatorInput:
    """Tests for keyboard input functionality"""

    def test_press_button_valid(self):
        """Should press valid button successfully"""
        from src.emulator.input import EmulatorInput

        with patch('src.emulator.input.pyautogui.press') as mock_press:
            emulator_input = EmulatorInput()
            result = emulator_input.press_button("a")

            assert result is True
            mock_press.assert_called_once()

    def test_press_button_invalid(self):
        """Should reject invalid button names"""
        from src.emulator.input import EmulatorInput

        with patch('src.emulator.input.pyautogui.press') as mock_press:
            emulator_input = EmulatorInput()
            result = emulator_input.press_button("invalid")

            assert result is False
            mock_press.assert_not_called()

    def test_press_buttons_sequence(self):
        """Should press multiple buttons in sequence"""
        from src.emulator.input import EmulatorInput

        with patch('src.emulator.input.pyautogui.press') as mock_press, \
             patch('src.emulator.input.time.sleep'):

            emulator_input = EmulatorInput()
            result = emulator_input.press_buttons(["a", "b", "start"])

            assert result is True
            assert mock_press.call_count == 3

    def test_button_mapping(self):
        """Should map Pokemon buttons to correct keyboard keys"""
        from src.emulator.input import EmulatorInput

        emulator_input = EmulatorInput()

        assert emulator_input.BUTTON_MAP["a"] == "z"
        assert emulator_input.BUTTON_MAP["b"] == "x"
        assert emulator_input.BUTTON_MAP["start"] == "enter"
        assert emulator_input.BUTTON_MAP["select"] == "backspace"
