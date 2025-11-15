"""
Unit tests for emulator integration

Test-driven development: Write tests first, then implement features.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import numpy as np


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


class TestScreenCropping:
    """Tests for automatic game screen cropping"""

    def test_crop_to_game_screen_with_borders(self):
        """Should crop image to just the game screen, removing UI chrome"""
        from src.emulator.capture import crop_to_game_screen

        # Create a test image with borders (simulating mGBA window)
        # Full window: 528x508
        # Game screen should be cropped to 320x288 (2x scale of 160x144)
        test_image = Image.new('RGB', (528, 508), color=(255, 192, 203))  # Pink border

        # Draw a "game screen" in the center at coordinates (104, 133) to (424, 421)
        game_area = Image.new('RGB', (320, 288), color=(100, 150, 100))  # Greenish game color
        test_image.paste(game_area, (104, 133))

        # Crop to game screen
        cropped = crop_to_game_screen(test_image)

        # Should be 320x288 (Game Boy 160x144 at 2x scale)
        assert cropped.size == (320, 288)

        # Should have correct aspect ratio (10:9 for Game Boy)
        aspect_ratio = cropped.size[0] / cropped.size[1]
        expected_ratio = 160 / 144
        assert abs(aspect_ratio - expected_ratio) < 0.01

    def test_crop_coordinates_are_correct(self):
        """Should use correct crop coordinates for mGBA window"""
        from src.emulator.capture import crop_to_game_screen

        # Create test image and verify exact crop bounds
        test_image = Image.new('RGB', (528, 508))

        # Put a distinctive pixel at the expected top-left of game screen
        test_array = np.array(test_image)
        test_array[133, 104] = [255, 0, 0]  # Red pixel at game screen top-left
        test_array[420, 423] = [0, 255, 0]  # Green pixel at game screen bottom-right
        test_image = Image.fromarray(test_array)

        cropped = crop_to_game_screen(test_image)
        cropped_array = np.array(cropped)

        # Top-left pixel should be the red one
        assert list(cropped_array[0, 0]) == [255, 0, 0]

        # Bottom-right should be the green one
        assert list(cropped_array[-1, -1]) == [0, 255, 0]

    def test_crop_preserves_game_content(self):
        """Should preserve all game screen content without distortion"""
        from src.emulator.capture import crop_to_game_screen

        # Load an actual screenshot for testing
        import os
        test_screenshot_path = 'logs/screenshots/action_0072_013714.png'

        if os.path.exists(test_screenshot_path):
            original = Image.open(test_screenshot_path)
            cropped = crop_to_game_screen(original)

            # Should have reduced size (removed borders)
            assert cropped.size[0] < original.size[0]
            assert cropped.size[1] < original.size[1]

            # Should maintain Game Boy aspect ratio
            aspect_ratio = cropped.size[0] / cropped.size[1]
            expected_ratio = 160 / 144
            assert abs(aspect_ratio - expected_ratio) < 0.01

    def test_crop_handles_already_cropped_image(self):
        """Should handle images that are already game-screen sized"""
        from src.emulator.capture import crop_to_game_screen

        # Image already at game screen size
        game_sized = Image.new('RGB', (320, 288))
        result = crop_to_game_screen(game_sized)

        # Should return image as-is or with minimal change
        assert result.size == (320, 288)
