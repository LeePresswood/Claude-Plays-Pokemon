"""
Screenshot capture from emulator window
"""
import pyautogui
from PIL import Image
import pygetwindow as gw
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmulatorCapture:
    """Captures screenshots from the emulator window"""

    def __init__(self, window_title: str = "mGBA"):
        """
        Initialize the capture system

        Args:
            window_title: Partial title of the emulator window to capture
        """
        self.window_title = window_title
        self.window = None

    def find_window(self) -> bool:
        """
        Find the emulator window

        Returns:
            True if window found, False otherwise
        """
        try:
            windows = gw.getWindowsWithTitle(self.window_title)
            if windows:
                self.window = windows[0]
                logger.info(f"Found emulator window: {self.window.title}")
                return True
            else:
                logger.warning(f"No window found with title containing '{self.window_title}'")
                return False
        except Exception as e:
            logger.error(f"Error finding window: {e}")
            return False

    def capture_screenshot(self) -> Optional[Image.Image]:
        """
        Capture a screenshot of the emulator window

        Returns:
            PIL Image object or None if capture failed
        """
        if not self.window and not self.find_window():
            logger.error("Cannot capture screenshot - window not found")
            return None

        try:
            # Get window position and size
            left, top = self.window.left, self.window.top
            width, height = self.window.width, self.window.height

            # Capture the region
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            logger.debug(f"Captured screenshot: {width}x{height}")
            return screenshot

        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None

    def activate_window(self) -> bool:
        """
        Bring the emulator window to front and activate it

        Returns:
            True if successful, False otherwise
        """
        if not self.window and not self.find_window():
            return False

        try:
            self.window.activate()
            logger.debug("Activated emulator window")
            return True
        except Exception as e:
            logger.error(f"Error activating window: {e}")
            return False
