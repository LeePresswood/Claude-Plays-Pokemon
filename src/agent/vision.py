"""
Claude API integration for vision-based decision making
"""
import anthropic
from PIL import Image
import base64
import io
import logging
from typing import Optional, Dict, Any
from src.config import ANTHROPIC_API_KEY, MODEL, MAX_TOKENS, VALID_BUTTONS

logger = logging.getLogger(__name__)


class ClaudeVision:
    """Handles communication with Claude API for game decisions"""

    def __init__(self):
        """Initialize the Claude API client"""
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.action_count = 0

        # System prompt that teaches Claude how to play Pokemon
        self.system_prompt = """You are an AI playing Pokemon Red.

You will receive screenshots from the game. Your job is to:
1. Analyze what you see on screen
2. Decide what button to press next
3. Respond with a SINGLE button press

Valid buttons: a, b, start, select, up, down, left, right

Response format (JSON):
{
  "button": "a",
  "reasoning": "I see a dialog box, pressing A to advance the text"
}

Strategy tips:
- Press A to confirm and advance dialog
- Press B to cancel or go back
- Use directional buttons to move and navigate menus
- Press Start to open the menu
- Press Select to switch items (in some contexts)

Keep your reasoning brief. Focus on making progress in the game."""

    def image_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string

        Args:
            image: PIL Image object

        Returns:
            Base64 encoded image string
        """
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def get_action(self, screenshot: Image.Image, recent_history: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Send screenshot to Claude and get next action

        Args:
            screenshot: PIL Image of current game state
            recent_history: Optional string describing recent actions

        Returns:
            Dict with 'button' and 'reasoning' keys, or None if error
        """
        try:
            # Convert image to base64
            image_b64 = self.image_to_base64(screenshot)

            # Build message with context if available
            user_message = "What button should I press next?"
            if recent_history:
                user_message = f"Recent actions:\n{recent_history}\n\nWhat button should I press next?"

            # Call Claude API
            message = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": user_message
                            }
                        ],
                    }
                ],
            )

            # Extract response
            response_text = message.content[0].text
            logger.info(f"Claude response: {response_text}")

            # Parse the response (expecting JSON)
            import json
            try:
                action_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback: try to extract button from text
                logger.warning("Response not valid JSON, attempting to parse")
                action_data = self._parse_text_response(response_text)

            # Validate button
            button = action_data.get("button", "").lower()
            if button not in VALID_BUTTONS:
                logger.error(f"Invalid button in response: {button}")
                return None

            self.action_count += 1
            logger.info(f"Action #{self.action_count}: {button} - {action_data.get('reasoning', 'No reasoning provided')}")

            return action_data

        except Exception as e:
            logger.error(f"Error getting action from Claude: {e}")
            return None

    def _parse_text_response(self, text: str) -> Dict[str, str]:
        """
        Fallback parser for non-JSON responses

        Args:
            text: Response text from Claude

        Returns:
            Dict with button and reasoning
        """
        # Look for button names in the text
        text_lower = text.lower()
        for button in VALID_BUTTONS:
            if button in text_lower:
                return {
                    "button": button,
                    "reasoning": text
                }

        # Default fallback
        logger.warning("Could not parse button from response, defaulting to 'a'")
        return {
            "button": "a",
            "reasoning": text
        }

    def get_action_count(self) -> int:
        """Get the number of actions taken this session"""
        return self.action_count
