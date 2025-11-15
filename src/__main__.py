"""
Claude Plays Pokemon - Main Game Loop

A simple autonomous Pokemon Red player powered by Claude's vision capabilities.
"""
import time
import logging
from datetime import datetime
from pathlib import Path

from src.emulator.capture import EmulatorCapture
from src.emulator.input import EmulatorInput
from src.agent.vision import ClaudeVision
from src.agent.memory import GameMemory
from src.agent.knowledge import KnowledgeBase
from src.config import (
    ACTION_DELAY,
    MAX_ACTIONS_PER_SESSION,
    WARN_COST_THRESHOLD,
    LOG_DIR,
    SAVE_SCREENSHOTS,
    USE_EXTENDED_THINKING
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
        self.knowledge = KnowledgeBase()
        self.vision = ClaudeVision(knowledge_base=self.knowledge)
        self.memory = GameMemory()

        # Track stuck/unstuck states for learning
        self.was_stuck = False
        self.actions_while_stuck = []

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

        # Store screenshot hash for stuck detection
        self.memory.add_screenshot_hash(screenshot)

        # Check if stuck
        is_stuck = self.memory.is_stuck()

        # Get recent history for context
        history = self.memory.get_recent_history_text()
        recent_actions = list(self.memory.history)

        # Handle stuck state transitions
        if is_stuck and not self.was_stuck:
            # Just became stuck - record it and analyze pattern
            pattern = self.knowledge.analyze_stuck_pattern(recent_actions)
            self.knowledge.record_stuck_state(pattern, recent_actions)
            self.was_stuck = True
            self.actions_while_stuck = []
            logger.warning(f"Entered stuck state with pattern: {pattern}")

        elif not is_stuck and self.was_stuck:
            # Just became unstuck - learn from it!
            if self.actions_while_stuck:
                logger.info(f"Became unstuck after {len(self.actions_while_stuck)} actions")
                self.knowledge.record_unstuck_success(self.actions_while_stuck)
            self.was_stuck = False
            self.actions_while_stuck = []

        # Build stuck context with knowledge suggestions
        stuck_context = None
        if is_stuck:
            stuck_context = self.memory.get_stuck_context()
            # Add knowledge-based suggestions
            suggestion = self.knowledge.get_suggestion_for_stuck_state(recent_actions)
            if suggestion:
                stuck_context += f"\n\n{suggestion}"

        # Use extended thinking if stuck or enabled
        if USE_EXTENDED_THINKING and is_stuck:
            logger.warning("Detected stuck state - using extended thinking mode")
            action = self.vision.get_action_with_thinking(screenshot, history, stuck_context)
        else:
            # Normal single-turn decision
            action = self.vision.get_action(screenshot, history)

        if action is None:
            logger.error("Failed to get action from Claude")
            return False

        buttons = action["buttons"]
        reasoning = action.get("reasoning", "No reasoning provided")

        # Record the action (store as comma-separated string for compatibility)
        button_str = ",".join(buttons) if len(buttons) > 1 else buttons[0]
        self.memory.add_action(button_str, reasoning, screenshot_path)

        # Track actions while stuck for learning
        if self.was_stuck:
            self.actions_while_stuck.append({
                "button": button_str,
                "reasoning": reasoning
            })

        # Execute button sequence
        # Activate window before pressing buttons
        if not self.capture.activate_window():
            logger.error("Failed to activate emulator window")
            return False

        # Longer delay to ensure window is truly focused and ready for input
        time.sleep(0.3)

        if not self.input.press_buttons(buttons):
            logger.error(f"Failed to press buttons: {buttons}")
            return False

        # Log progress
        if len(buttons) == 1:
            logger.info(f"Action #{self.vision.get_action_count()}: {buttons[0]} - {reasoning}")
        else:
            logger.info(f"Action #{self.vision.get_action_count()}: {buttons} ({len(buttons)} buttons) - {reasoning}")

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
        knowledge_stats = self.knowledge.get_stats()

        logger.info("=" * 50)
        logger.info("SESSION STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total actions: {stats['total_actions']}")
        logger.info(f"Duration: {stats['duration_seconds']:.1f} seconds")
        logger.info(f"Actions per minute: {stats['actions_per_minute']:.1f}")
        logger.info(f"Estimated cost: ~${stats['total_actions'] / 1000:.2f}")
        logger.info(f"Button distribution: {stats['button_distribution']}")
        logger.info("")
        logger.info("LEARNING STATISTICS")
        logger.info(f"Stuck states encountered: {knowledge_stats['total_stuck_states']}")
        logger.info(f"Successfully unstuck: {knowledge_stats['total_unstuck_successes']}")
        logger.info(f"Patterns learned: {knowledge_stats['patterns_learned']}")
        logger.info("=" * 50)

        # Save session log and knowledge
        self.memory.save_session_log()
        self.knowledge.save_knowledge()
        logger.info("Session log and knowledge base saved. Goodbye!")


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
