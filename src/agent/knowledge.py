"""
Knowledge base for active learning during gameplay
Learns from stuck states and successful unstuck strategies
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """Manages learned gameplay knowledge and patterns"""

    def __init__(self, knowledge_file: Optional[Path] = None):
        """
        Initialize knowledge base

        Args:
            knowledge_file: Path to knowledge file (default: knowledge/learned.json)
        """
        if knowledge_file is None:
            # Store in knowledge/ directory at project root
            project_root = Path(__file__).parent.parent.parent
            knowledge_dir = project_root / "knowledge"
            knowledge_dir.mkdir(exist_ok=True)
            knowledge_file = knowledge_dir / "learned.json"

        self.knowledge_file = knowledge_file
        self.knowledge = self._load_knowledge()

        # Track current session for learning
        self.current_stuck_pattern = None
        self.actions_since_stuck = []

    def _load_knowledge(self) -> Dict[str, Any]:
        """
        Load knowledge from file

        Returns:
            Dict with knowledge data
        """
        default_knowledge = {
            "version": "1.0",
            "last_updated": None,
            "general_tips": [
                "If you see a menu or PC screen that won't close with A, try pressing B to cancel",
                "If stuck after multiple A presses, try moving in a direction (up/down/left/right)",
                "The START button opens the main menu, which can help diagnose the game state",
            ],
            "stuck_patterns": {
                # Format: "pattern_name": {
                #   "description": "What the pattern looks like",
                #   "successful_solutions": ["action1", "action2"],
                #   "times_encountered": count,
                #   "success_rate": percentage
                # }
            },
            "location_specific": {
                # Format: "location_name": {
                #   "tips": ["tip1", "tip2"],
                #   "common_issues": ["issue1"]
                # }
            },
            "stats": {
                "total_stuck_states": 0,
                "total_unstuck_successes": 0,
                "patterns_learned": 0
            }
        }

        if not self.knowledge_file.exists():
            logger.info(f"Creating new knowledge base at {self.knowledge_file}")
            return default_knowledge

        try:
            with open(self.knowledge_file, 'r') as f:
                knowledge = json.load(f)
                logger.info(f"Loaded knowledge base from {self.knowledge_file}")
                return knowledge
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return default_knowledge

    def save_knowledge(self):
        """Save knowledge to file"""
        try:
            self.knowledge["last_updated"] = datetime.now().isoformat()
            with open(self.knowledge_file, 'w') as f:
                json.dump(self.knowledge, f, indent=2)
            logger.info(f"Saved knowledge base to {self.knowledge_file}")
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")

    def get_context_for_prompt(self) -> str:
        """
        Get knowledge as context string for Claude

        Returns:
            Formatted string with relevant knowledge
        """
        lines = ["=== LEARNED KNOWLEDGE ===\n"]

        # General tips
        if self.knowledge["general_tips"]:
            lines.append("General Tips:")
            for tip in self.knowledge["general_tips"]:
                lines.append(f"  - {tip}")
            lines.append("")

        # Stuck patterns with solutions
        if self.knowledge["stuck_patterns"]:
            lines.append("Known Stuck Patterns & Solutions:")
            for pattern_name, pattern_data in self.knowledge["stuck_patterns"].items():
                if pattern_data.get("successful_solutions"):
                    success_rate = pattern_data.get("success_rate", 0)
                    lines.append(f"  Pattern: {pattern_data['description']}")
                    lines.append(f"    Solutions: {', '.join(pattern_data['successful_solutions'])} (success rate: {success_rate:.0f}%)")
            lines.append("")

        lines.append("=== END LEARNED KNOWLEDGE ===")
        return "\n".join(lines)

    def analyze_stuck_pattern(self, recent_actions: List[Dict[str, Any]]) -> Optional[str]:
        """
        Analyze recent actions to identify stuck pattern

        Args:
            recent_actions: List of recent action dicts with 'button' and 'reasoning'

        Returns:
            Pattern description or None
        """
        if len(recent_actions) < 3:
            return None

        # Get last 5 actions
        last_5 = recent_actions[-5:]
        buttons = [action['button'] for action in last_5]

        # Pattern: Same button repeatedly
        if len(set(buttons)) == 1:
            button = buttons[0]
            return f"repeated_{button}_button"

        # Pattern: Alternating two buttons
        if len(set(buttons)) == 2 and len(buttons) >= 4:
            unique_buttons = list(set(buttons))
            return f"alternating_{unique_buttons[0]}_and_{unique_buttons[1]}"

        # Pattern: Multiple A presses (common when stuck in menus)
        a_count = buttons.count('a')
        if a_count >= 3:
            return "multiple_a_presses"

        # Pattern: Multiple movement attempts in same direction
        directional = ['up', 'down', 'left', 'right']
        directional_presses = [b for b in buttons if b in directional]
        if len(directional_presses) >= 3 and len(set(directional_presses)) == 1:
            direction = directional_presses[0]
            return f"repeated_{direction}_movement"

        return None

    def record_stuck_state(self, pattern: Optional[str], recent_actions: List[Dict[str, Any]]):
        """
        Record that we entered a stuck state

        Args:
            pattern: Pattern description from analyze_stuck_pattern
            recent_actions: Recent action history
        """
        self.current_stuck_pattern = pattern or "unknown_pattern"
        self.actions_since_stuck = []

        # Update stats
        self.knowledge["stats"]["total_stuck_states"] += 1

        logger.info(f"Recorded stuck state with pattern: {self.current_stuck_pattern}")

    def record_unstuck_success(self, unstuck_actions: List[Dict[str, Any]]):
        """
        Record successful unstuck and learn from it

        Args:
            unstuck_actions: Actions taken that led to unstucking
        """
        if not self.current_stuck_pattern:
            logger.warning("Recorded unstuck but no stuck pattern was set")
            return

        # Update stats
        self.knowledge["stats"]["total_unstuck_successes"] += 1

        # Get the key action(s) that unstuck us
        solution_buttons = [action['button'] for action in unstuck_actions[:3]]  # First 3 actions
        solution_str = " -> ".join(solution_buttons)

        # Get or create pattern entry
        patterns = self.knowledge["stuck_patterns"]
        if self.current_stuck_pattern not in patterns:
            patterns[self.current_stuck_pattern] = {
                "description": self._pattern_to_description(self.current_stuck_pattern),
                "successful_solutions": [],
                "times_encountered": 0,
                "total_successes": 0,
                "success_rate": 0
            }

        pattern = patterns[self.current_stuck_pattern]
        pattern["times_encountered"] += 1
        pattern["total_successes"] += 1

        # Add solution if not already known
        if solution_str not in pattern["successful_solutions"]:
            pattern["successful_solutions"].append(solution_str)
            self.knowledge["stats"]["patterns_learned"] += 1
            logger.info(f"Learned new solution for '{self.current_stuck_pattern}': {solution_str}")

        # Update success rate
        pattern["success_rate"] = (pattern["total_successes"] / pattern["times_encountered"]) * 100

        # Save knowledge
        self.save_knowledge()

        # Reset stuck tracking
        self.current_stuck_pattern = None
        self.actions_since_stuck = []

    def _pattern_to_description(self, pattern: str) -> str:
        """Convert pattern name to human-readable description"""
        if pattern.startswith("repeated_"):
            parts = pattern.split("_")
            if "button" in pattern:
                return f"Pressing {parts[1].upper()} button repeatedly"
            elif "movement" in pattern:
                return f"Moving {parts[1]} repeatedly into obstacle"
        elif pattern.startswith("alternating_"):
            parts = pattern.split("_and_")
            return f"Alternating between {parts[0].split('_')[1].upper()} and {parts[1].upper()}"
        elif pattern == "multiple_a_presses":
            return "Multiple A presses without progress"

        return pattern.replace("_", " ").title()

    def get_suggestion_for_stuck_state(self, recent_actions: List[Dict[str, Any]]) -> Optional[str]:
        """
        Get suggestion based on current stuck pattern

        Args:
            recent_actions: Recent action history

        Returns:
            Suggestion string or None
        """
        pattern = self.analyze_stuck_pattern(recent_actions)
        if not pattern:
            return None

        # Check if we know this pattern
        if pattern in self.knowledge["stuck_patterns"]:
            pattern_data = self.knowledge["stuck_patterns"][pattern]
            if pattern_data["successful_solutions"]:
                solutions = pattern_data["successful_solutions"]
                success_rate = pattern_data.get("success_rate", 0)
                return (
                    f"This pattern ('{pattern_data['description']}') was encountered before. "
                    f"Successful solutions: {', '.join(solutions)} (success rate: {success_rate:.0f}%)"
                )

        return None

    def add_general_tip(self, tip: str):
        """
        Add a general tip to the knowledge base (useful for manual seeding)

        Args:
            tip: Tip text
        """
        if tip not in self.knowledge["general_tips"]:
            self.knowledge["general_tips"].append(tip)
            self.save_knowledge()
            logger.info(f"Added general tip: {tip}")

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return self.knowledge["stats"].copy()
