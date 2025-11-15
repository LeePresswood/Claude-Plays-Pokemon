"""
Claude Plays Pokemon - Main Game Loop

A simple autonomous Pokemon Red player powered by Claude's vision capabilities.
"""
import time
import logging
from datetime import datetime
from pathlib import Path

from emulator.capture import EmulatorCapture
from emulator.input import EmulatorInput
from agent.vision import ClaudeVision
from agent.memory import GameMemory
from config import (
    ACTION_DELAY,
    MAX_ACTIONS_PER_SESSION,
    WARN_COST_THRESHOLD,
    LOG_DIR,
    SAVE_SCREENSHOTS
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'game_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PokemonAgent:
    """Main game loop controller"""

    def __init__(self, window_title: str = "mGBA"):
        """
        Initialize the Pokemon playing agent

        Args:
            window_title: Partial title of emulator window
        """
        self.capture = EmulatorCapture(window_title)
        self.input = EmulatorInput()
        self.vision = ClaudeVision()
        self.memory = GameMemory()

        self.running = False
        self.screenshot_dir = LOG_DIR / "screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)

    def setup(self) -> bool:
        """
        Setup and verify all components

        Returns:
            True if setup successful, False otherwise
        """
        logger.info("Setting up Pokemon Agent...")

        # Find emulator window
        if not self.capture.find_window():
            logger.error("Could not find emulator window. Is the emulator running?")
            return False

        # Activate the window
        if not self.capture.activate_window():
            logger.warning("Could not activate window, continuing anyway...")

        logger.info("Setup complete!")
        return True

    def save_screenshot(self, image, action_number: int) -> str:
        """
        Save screenshot to disk

        Args:
            image: PIL Image to save
            action_number: Current action number for filename

        Returns:
            Path to saved screenshot
        """
        filename = f"action_{action_number:04d}_{datetime.now().strftime('%H%M%S')}.png"
        filepath = self.screenshot_dir / filename
        image.save(filepath)
        return str(filepath)

    def run_single_step(self) -> bool:
        """
        Execute a single step of the game loop:
        1. Capture screenshot
        2. Get action from Claude
        3. Execute button press

        Returns:
            True if step successful, False if should stop
        """
        # Capture screenshot
        screenshot = self.capture.capture_screenshot()
        if screenshot is None:
            logger.error("Failed to capture screenshot")
            return False

        # Save screenshot if enabled
        screenshot_path = None
        if SAVE_SCREENSHOTS:
            screenshot_path = self.save_screenshot(screenshot, self.vision.get_action_count())

        # Get recent history for context
        history = self.memory.get_recent_history_text()

        # Get action from Claude
        action = self.vision.get_action(screenshot, history)
        if action is None:
            logger.error("Failed to get action from Claude")
            return False

        button = action["button"]
        reasoning = action.get("reasoning", "No reasoning provided")

        # Record the action
        self.memory.add_action(button, reasoning, screenshot_path)

        # Execute button press
        # Activate window before pressing button
        self.capture.activate_window()
        time.sleep(0.1)  # Small delay to ensure window is active

        if not self.input.press_button(button):
            logger.error(f"Failed to press button: {button}")
            return False

        # Log progress
        logger.info(f"Action #{self.vision.get_action_count()}: {button} - {reasoning}")

        return True

    def run(self, max_actions: int = MAX_ACTIONS_PER_SESSION):
        """
        Run the main game loop

        Args:
            max_actions: Maximum number of actions to take
        """
        logger.info(f"Starting game loop (max {max_actions} actions)...")
        self.running = True

        try:
            while self.running and self.vision.get_action_count() < max_actions:
                # Check if we should warn about costs
                if self.vision.get_action_count() == WARN_COST_THRESHOLD:
                    logger.warning(f"Reached {WARN_COST_THRESHOLD} actions. Estimated cost: ~${WARN_COST_THRESHOLD / 1000:.2f}")

                # Execute one step
                success = self.run_single_step()
                if not success:
                    logger.error("Step failed, stopping...")
                    break

                # Delay before next action
                time.sleep(ACTION_DELAY)

        except KeyboardInterrupt:
            logger.info("Stopped by user (Ctrl+C)")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self):
        """Stop the agent and save logs"""
        self.running = False

        # Print statistics
        stats = self.memory.get_stats()
        logger.info("=" * 50)
        logger.info("SESSION STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total actions: {stats['total_actions']}")
        logger.info(f"Duration: {stats['duration_seconds']:.1f} seconds")
        logger.info(f"Actions per minute: {stats['actions_per_minute']:.1f}")
        logger.info(f"Estimated cost: ~${stats['total_actions'] / 1000:.2f}")
        logger.info(f"Button distribution: {stats['button_distribution']}")
        logger.info("=" * 50)

        # Save session log
        self.memory.save_session_log()
        logger.info("Session log saved. Goodbye!")


def main():
    """Main entry point"""
    print("=" * 60)
    print("CLAUDE PLAYS POKEMON")
    print("=" * 60)
    print()
    print("Make sure:")
    print("1. Your emulator (mGBA) is running with Pokemon Red loaded")
    print("2. The emulator window is visible (not minimized)")
    print("3. API key is set in .env file")
    print()
    print("Press Ctrl+C to stop at any time")
    print("=" * 60)
    print()

    # Create agent
    agent = PokemonAgent(window_title="mGBA")

    # Setup
    if not agent.setup():
        logger.error("Setup failed. Exiting.")
        return

    # Small delay before starting
    print("Starting in 3 seconds...")
    time.sleep(3)

    # Run the game loop
    agent.run()


if __name__ == "__main__":
    main()
