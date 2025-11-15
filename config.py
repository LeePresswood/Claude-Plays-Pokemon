"""
Configuration file for Claude Plays Pokemon
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY not set. Create a .env file with your API key "
        "(see .env.example) or set the environment variable."
    )

# Model Configuration
MODEL = "claude-3-5-haiku-20241022"  # Cost-effective Haiku model
MAX_TOKENS = 1024  # Enough for button press decisions

# Game Loop Configuration
ACTION_DELAY = 2.0  # Seconds between actions (for cost control and debugging)
BUTTON_PRESS_DURATION = 0.1  # How long to hold each button

# Valid Pokemon Red buttons
VALID_BUTTONS = ["a", "b", "start", "select", "up", "down", "left", "right"]

# Logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
SAVE_SCREENSHOTS = True  # Save screenshots with decisions for debugging

# Budget safeguards
MAX_ACTIONS_PER_SESSION = 1000  # Stop after this many actions
WARN_COST_THRESHOLD = 100  # Warn if estimated cost exceeds this many actions
