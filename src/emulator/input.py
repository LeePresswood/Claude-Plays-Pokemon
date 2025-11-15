"""
Button press execution to emulator
"""
import pyautogui
import time
import logging
from typing import List
from src.config import BUTTON_PRESS_DURATION, VALID_BUTTONS, BUTTON_SEQUENCE_DELAY

logger = logging.getLogger(__name__)


class EmulatorInput:
    """Sends keyboard input to the emulator"""

    # Map Pokemon buttons to keyboard keys (default mGBA mapping)
    BUTTON_MAP = {
        "a": "z",
        "b": "x",
        "start": "enter",
        "select": "backspace",
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right"
    }

    def __init__(self):
        """Initialize the input system"""
        # Disable pyautogui failsafe (moving mouse to corner to abort)
        # You can enable this during debugging
        pyautogui.FAILSAFE = True

    def press_button(self, button: str, duration: float = BUTTON_PRESS_DURATION) -> bool:
        """
        Press a single button

        Args:
            button: Pokemon button name (a, b, start, select, up, down, left, right)
            duration: How long to hold the button

        Returns:
            True if successful, False otherwise
        """
        button = button.lower()

        if button not in VALID_BUTTONS:
            logger.error(f"Invalid button: {button}. Valid buttons: {VALID_BUTTONS}")
            return False

        try:
            key = self.BUTTON_MAP[button]
            # Use keyDown/keyUp for better control instead of press()
            pyautogui.keyDown(key)
            time.sleep(duration)
            pyautogui.keyUp(key)
            logger.info(f"Pressed button: {button} (key: {key})")
            return True

        except Exception as e:
            logger.error(f"Error pressing button {button}: {e}")
            return False

    def press_buttons(self, buttons: List[str], delay: float = None) -> bool:
        """
        Press a sequence of buttons with configurable delay

        Args:
            buttons: List of button names to press in order
            delay: Delay between button presses (defaults to BUTTON_SEQUENCE_DELAY)

        Returns:
            True if all successful, False otherwise
        """
        if delay is None:
            delay = BUTTON_SEQUENCE_DELAY

        success = True
        for i, button in enumerate(buttons):
            if not self.press_button(button):
                success = False
                break

            # Add delay between buttons (but not after the last one)
            if i < len(buttons) - 1:
                time.sleep(delay)

        return success

    def hold_button(self, button: str, duration: float) -> bool:
        """
        Hold a button for a specific duration

        Args:
            button: Pokemon button name
            duration: How long to hold in seconds

        Returns:
            True if successful, False otherwise
        """
        button = button.lower()

        if button not in VALID_BUTTONS:
            logger.error(f"Invalid button: {button}")
            return False

        try:
            key = self.BUTTON_MAP[button]
            pyautogui.keyDown(key)
            time.sleep(duration)
            pyautogui.keyUp(key)
            logger.info(f"Held button {button} for {duration}s")
            return True

        except Exception as e:
            logger.error(f"Error holding button {button}: {e}")
            return False
