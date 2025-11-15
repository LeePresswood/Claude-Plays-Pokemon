"""
Screenshot capture from emulator window
"""
import pyautogui
from PIL import Image, ImageGrab
import pygetwindow as gw
from typing import Optional, Tuple
import logging
import sys

logger = logging.getLogger(__name__)


# mGBA window crop coordinates (determined empirically)
# These remove the Windows title bar, menu bar, and decorative borders
# leaving just the Game Boy screen at 2x scale (320x288 from original 160x144)
MGBA_CROP_BOUNDS = (104, 133, 424, 421)  # (left, top, right, bottom)


def crop_to_game_screen(image: Image.Image, crop_bounds: Tuple[int, int, int, int] = MGBA_CROP_BOUNDS) -> Image.Image:
    """
    Crop screenshot to just the game screen, removing UI chrome

    This removes:
    - Windows title bar and menu bar
    - mGBA decorative borders
    - Pokemon info panels on the sides
    - Pink/red border frame

    Args:
        image: Full window screenshot
        crop_bounds: Tuple of (left, top, right, bottom) coordinates

    Returns:
        Cropped image containing only the game screen
    """
    # If image is already close to game screen size, return as-is
    if image.size[0] <= crop_bounds[2] - crop_bounds[0] + 10:
        logger.debug(f"Image already game-screen sized ({image.size}), skipping crop")
        return image

    try:
        cropped = image.crop(crop_bounds)
        logger.debug(f"Cropped image from {image.size} to {cropped.size}")
        return cropped
    except Exception as e:
        logger.warning(f"Failed to crop image: {e}, returning original")
        return image


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

        Uses ImageGrab on Windows which handles DPI scaling better than pyautogui

        Returns:
            PIL Image object or None if capture failed
        """
        if not self.window and not self.find_window():
            logger.error("Cannot capture screenshot - window not found")
            return None

        try:
            # Activate window to bring it to front
            self.activate_window()

            # Small delay to let window activate
            import time
            time.sleep(0.1)

            # Refresh window object to get current position (in case it moved during activation)
            if not self.find_window():
                logger.error("Lost window reference after activation")
                return None

            # Get window bounds (fresh after activation)
            # self.window is guaranteed to be non-None here because find_window() returned True
            assert self.window is not None
            left = self.window.left
            top = self.window.top
            right = left + self.window.width
            bottom = top + self.window.height

            logger.debug(f"Capturing window '{self.window.title}' at ({left}, {top}, {right}, {bottom})")

            # Use ImageGrab on Windows (handles DPI better)
            if sys.platform == 'win32':
                screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
                logger.debug(f"Captured screenshot with ImageGrab: {screenshot.size}")
            else:
                # Fallback to pyautogui for other platforms
                screenshot = pyautogui.screenshot(region=(left, top, self.window.width, self.window.height))
                logger.debug(f"Captured screenshot with pyautogui: {screenshot.size}")

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
            # First try to restore if minimized
            if self.window.isMinimized:
                self.window.restore()
                import time
                time.sleep(0.1)

            # Then activate
            self.window.activate()

            # On Windows, sometimes we need to be more aggressive
            if sys.platform == 'win32':
                try:
                    import win32gui
                    import win32con

                    # Use the window handle from pygetwindow instead of FindWindow
                    # pygetwindow stores the handle in _hWnd
                    if hasattr(self.window, '_hWnd'):
                        hwnd = self.window._hWnd

                        # Show and restore window if needed
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

                        # Bring to top and set focus
                        win32gui.SetForegroundWindow(hwnd)
                        win32gui.SetFocus(hwnd)

                        logger.debug(f"Activated window using win32gui (hwnd={hwnd}): {self.window.title}")
                    else:
                        logger.debug("Could not get window handle (_hWnd)")
                except Exception as win32_error:
                    logger.debug(f"win32gui activation failed (non-critical): {win32_error}")

            logger.debug("Activated emulator window")
            return True
        except Exception as e:
            logger.error(f"Error activating window: {e}")
            return False
