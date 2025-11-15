"""
Test script to verify setup before running the full game loop
"""
import logging
from emulator.capture import EmulatorCapture
from emulator.input import EmulatorInput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_window_detection():
    """Test if we can find the emulator window"""
    print("\n" + "=" * 60)
    print("TEST 1: Window Detection")
    print("=" * 60)

    capture = EmulatorCapture(window_title="mGBA")

    if capture.find_window():
        print(f"✓ Found window: {capture.window.title}")
        print(f"  Position: ({capture.window.left}, {capture.window.top})")
        print(f"  Size: {capture.window.width}x{capture.window.height}")
        return True
    else:
        print("✗ Could not find emulator window")
        print("  Make sure mGBA is running and the window title contains 'mGBA'")
        return False


def test_screenshot():
    """Test screenshot capture"""
    print("\n" + "=" * 60)
    print("TEST 2: Screenshot Capture")
    print("=" * 60)

    capture = EmulatorCapture(window_title="mGBA")

    if not capture.find_window():
        print("✗ Cannot test - window not found")
        return False

    screenshot = capture.capture_screenshot()
    if screenshot:
        print(f"✓ Screenshot captured: {screenshot.width}x{screenshot.height}")

        # Save test screenshot
        screenshot.save("test_screenshot.png")
        print("  Saved as test_screenshot.png")
        return True
    else:
        print("✗ Failed to capture screenshot")
        return False


def test_button_press():
    """Test button press (will actually press a button!)"""
    print("\n" + "=" * 60)
    print("TEST 3: Button Press")
    print("=" * 60)
    print("This will press the 'A' button in 3 seconds...")
    print("Make sure the emulator window is focused!")

    import time
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    input_handler = EmulatorInput()
    if input_handler.press_button("a"):
        print("✓ Button press sent successfully")
        return True
    else:
        print("✗ Failed to press button")
        return False


def test_api_key():
    """Test if API key is set"""
    print("\n" + "=" * 60)
    print("TEST 4: API Key")
    print("=" * 60)

    try:
        from config import ANTHROPIC_API_KEY
        if ANTHROPIC_API_KEY and len(ANTHROPIC_API_KEY) > 0:
            print(f"✓ API key found (length: {len(ANTHROPIC_API_KEY)})")
            return True
        else:
            print("✗ API key not set")
            print("  Set ANTHROPIC_API_KEY environment variable")
            return False
    except ValueError as e:
        print(f"✗ {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CLAUDE PLAYS POKEMON - SETUP TEST")
    print("=" * 60)

    results = {
        "API Key": test_api_key(),
        "Window Detection": test_window_detection(),
        "Screenshot": test_screenshot(),
    }

    # Only test button press if user confirms
    print("\n" + "=" * 60)
    response = input("Test button press? This will press 'A' in the emulator (y/n): ")
    if response.lower() == 'y':
        results["Button Press"] = test_button_press()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20} {status}")

    all_passed = all(results.values())
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed! You're ready to run main.py")
    else:
        print("✗ Some tests failed. Fix the issues above before running main.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
