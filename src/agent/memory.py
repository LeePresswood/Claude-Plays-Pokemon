"""
Game state memory and history tracking
"""
from collections import deque
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
import imagehash
from src.config import LOG_DIR

logger = logging.getLogger(__name__)


class GameMemory:
    """Tracks game history and provides context for Claude"""

    def __init__(self, max_history: int = 10):
        """
        Initialize game memory

        Args:
            max_history: Maximum number of recent actions to remember
        """
        self.max_history = max_history
        self.history = deque(maxlen=max_history)
        self.session_start = datetime.now()
        self.session_log = []

        # Stuck detection using perceptual hashing
        self.screenshot_hashes = deque(maxlen=5)  # Keep last 5 screenshot hashes
        self.stuck_threshold = 3  # Same screen 3+ times = stuck

    def add_action(self, button: str, reasoning: str, screenshot_path: str = None):
        """
        Record an action taken

        Args:
            button: Button that was pressed
            reasoning: Claude's reasoning for the action
            screenshot_path: Optional path to saved screenshot
        """
        action = {
            "timestamp": datetime.now().isoformat(),
            "button": button,
            "reasoning": reasoning,
            "screenshot": screenshot_path
        }

        self.history.append(action)
        self.session_log.append(action)

        logger.debug(f"Recorded action: {button}")

    def get_recent_history_text(self, num_actions: int = 5) -> str:
        """
        Get formatted text of recent actions for Claude context

        Args:
            num_actions: Number of recent actions to include

        Returns:
            Formatted string of recent actions
        """
        recent = list(self.history)[-num_actions:]

        if not recent:
            return "No previous actions"

        lines = []
        for i, action in enumerate(recent, 1):
            lines.append(f"{i}. Pressed {action['button']}: {action['reasoning']}")

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get session statistics

        Returns:
            Dict with session stats
        """
        duration = (datetime.now() - self.session_start).total_seconds()

        button_counts = {}
        for action in self.session_log:
            button = action["button"]
            button_counts[button] = button_counts.get(button, 0) + 1

        return {
            "total_actions": len(self.session_log),
            "duration_seconds": duration,
            "actions_per_minute": (len(self.session_log) / duration * 60) if duration > 0 else 0,
            "button_distribution": button_counts
        }

    def save_session_log(self, filename: str = None):
        """
        Save the session log to a JSON file

        Args:
            filename: Optional custom filename, otherwise uses timestamp
        """
        if filename is None:
            timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
            filename = f"session_{timestamp}.json"

        filepath = LOG_DIR / filename

        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "session_start": self.session_start.isoformat(),
                    "session_end": datetime.now().isoformat(),
                    "stats": self.get_stats(),
                    "actions": self.session_log
                }, f, indent=2)

            logger.info(f"Session log saved to {filepath}")

        except Exception as e:
            logger.error(f"Error saving session log: {e}")

    def load_session_log(self, filepath: Path) -> bool:
        """
        Load a previous session log

        Args:
            filepath: Path to session log file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                self.session_log = data.get("actions", [])
                # Restore recent history
                for action in self.session_log[-self.max_history:]:
                    self.history.append(action)

            logger.info(f"Loaded session log from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error loading session log: {e}")
            return False

    def add_screenshot_hash(self, screenshot: Image.Image):
        """
        Compute and store perceptual hash of screenshot for stuck detection

        Args:
            screenshot: PIL Image of current game state
        """
        # Use perceptual hash (pHash) - similar images have similar hashes
        phash = imagehash.phash(screenshot)
        self.screenshot_hashes.append(phash)
        logger.debug(f"Stored screenshot hash: {phash}")

    def is_stuck(self, similarity_threshold: int = 5) -> bool:
        """
        Detect if the agent is stuck (repeated similar screenshots)

        Args:
            similarity_threshold: Hash difference threshold (lower = more similar)

        Returns:
            True if stuck, False otherwise
        """
        if len(self.screenshot_hashes) < self.stuck_threshold:
            return False

        # Get the most recent hash
        latest_hash = self.screenshot_hashes[-1]

        # Count how many recent hashes are similar to the latest
        similar_count = 0
        for phash in list(self.screenshot_hashes)[-self.stuck_threshold:]:
            # Hamming distance between hashes
            if latest_hash - phash <= similarity_threshold:
                similar_count += 1

        # If most recent screenshots are similar, we're stuck
        is_stuck = similar_count >= self.stuck_threshold
        if is_stuck:
            logger.warning(f"Stuck state detected! {similar_count}/{self.stuck_threshold} similar screenshots")

        return is_stuck

    def get_stuck_context(self) -> str:
        """
        Get context message when stuck

        Returns:
            String describing stuck state
        """
        recent_buttons = [action['button'] for action in list(self.history)[-5:]]
        return (
            f"WARNING: You appear to be stuck! "
            f"The last {len(recent_buttons)} actions were: {', '.join(recent_buttons)}. "
            f"The screen looks very similar to previous screenshots. "
            f"Try a completely different approach - maybe go a different direction, "
            f"open the menu, or press B to cancel something."
        )
