"""
Quick manual test for button inputs
Run this with the emulator open to verify button presses work
"""
import time
from src.emulator.capture import EmulatorCapture
from src.emulator.input import EmulatorInput

def main():
    print("Testing emulator input...")
    print("Make sure mGBA is open and visible!")
    time.sleep(2)

    capture = EmulatorCapture()
    if not capture.find_window():
        print("ERROR: Could not find emulator window")
        return

    print(f"Found window: {capture.window.title}")

    # Activate window
    print("Activating window...")
    if not capture.activate_window():
        print("ERROR: Could not activate window")
        return

    time.sleep(0.5)

    # Test button presses
    input_system = EmulatorInput()

    print("\nTesting button presses...")
    print("You should see the character move/buttons respond in the emulator")

    buttons_to_test = ["a", "b", "up", "down", "left", "right", "start"]

    for button in buttons_to_test:
        print(f"  Pressing {button}...")
        # Re-activate before each press to ensure focus
        capture.activate_window()
        time.sleep(0.3)
        input_system.press_button(button)
        time.sleep(1)  # Wait to see the effect

    print("\nTest complete! Did you see the buttons working in the emulator?")

if __name__ == "__main__":
    main()
