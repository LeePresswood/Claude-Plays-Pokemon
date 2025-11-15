"""
Claude API integration for vision-based decision making
"""
import anthropic
from PIL import Image
import base64
import io
import logging
from typing import Optional, Dict, Any
from src.config import ANTHROPIC_API_KEY, MODEL, MAX_TOKENS, VALID_BUTTONS, MAX_BUTTONS_PER_RESPONSE, USE_EXTENDED_THINKING

logger = logging.getLogger(__name__)


class ClaudeVision:
    """Handles communication with Claude API for game decisions"""

    def __init__(self, knowledge_base=None):
        """
        Initialize the Claude API client

        Args:
            knowledge_base: Optional KnowledgeBase instance for active learning
        """
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.action_count = 0
        self.knowledge_base = knowledge_base

        # System prompt that teaches Claude how to play Pokemon
        self.system_prompt = f"""You are an AI playing Pokemon Red.

You will receive screenshots from the game. Your job is to:
1. Analyze what you see on screen
2. Decide what button(s) to press next
3. Respond with 1-{MAX_BUTTONS_PER_RESPONSE} button presses

Valid buttons: a, b, start, select, up, down, left, right

Response format (JSON):
{{
  "buttons": ["up", "up", "up"],
  "reasoning": "I see an open room. Moving north 3 steps to reach the door."
}}

For a single button:
{{
  "buttons": ["a"],
  "reasoning": "I see a dialog box, pressing A to advance the text"
}}

IMPORTANT - Prefer multi-button sequences when possible:
- Multi-button sequences are MORE EFFICIENT (fewer API calls, lower cost)
- Each response incurs API overhead - minimize this by planning ahead
- Walking across empty rooms: Use 3-5 movement buttons (e.g., ["up", "up", "up", "up"])
- Navigating menus: Combine navigation + selection (e.g., ["down", "down", "a"])
- Exiting areas: Plan the full path (e.g., ["down", "down", "right", "right"])

When to use single buttons:
- Dialog boxes (need to see text progression)
- Battle decisions (each choice has unique consequences)
- Complex menu interactions (PC, inventory management)
- When unsure about the game state

Strategy tips:
- Press A to confirm and advance dialog
- Press B to cancel or go back
- Use directional buttons to move and navigate menus
- Press Start to open the menu
- Press Select to switch items (in some contexts)
- Think ahead: Where do you want to be in 3-5 steps?

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
            # Crop to game screen only (remove UI chrome)
            from src.emulator.capture import crop_to_game_screen
            screenshot = crop_to_game_screen(screenshot)

            # Convert image to base64
            image_b64 = self.image_to_base64(screenshot)

            # Build message with context if available
            message_parts = []

            # Add learned knowledge if available
            if self.knowledge_base:
                knowledge_context = self.knowledge_base.get_context_for_prompt()
                if knowledge_context:
                    message_parts.append(knowledge_context)

            # Add recent history
            if recent_history:
                message_parts.append(f"Recent actions:\n{recent_history}")

            # Add question
            message_parts.append("What button should I press next?")

            user_message = "\n\n".join(message_parts)

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

            # Normalize response format (support both old "button" and new "buttons" format)
            buttons = action_data.get("buttons")
            if buttons is None:
                # Backward compatibility: convert single "button" to "buttons" list
                single_button = action_data.get("button", "").lower()
                if single_button:
                    buttons = [single_button]
                else:
                    logger.error("No buttons in response")
                    return None

            # Ensure buttons is a list
            if isinstance(buttons, str):
                buttons = [buttons]

            # Validate all buttons
            buttons = [b.lower() for b in buttons]
            for button in buttons:
                if button not in VALID_BUTTONS:
                    logger.error(f"Invalid button in response: {button}")
                    return None

            # Enforce max buttons limit
            if len(buttons) > MAX_BUTTONS_PER_RESPONSE:
                logger.warning(f"Response has {len(buttons)} buttons, truncating to {MAX_BUTTONS_PER_RESPONSE}")
                buttons = buttons[:MAX_BUTTONS_PER_RESPONSE]

            # Update action count (count each button press)
            self.action_count += len(buttons)

            # Update action_data with normalized buttons
            action_data["buttons"] = buttons

            logger.info(f"Action #{self.action_count}: {buttons} - {action_data.get('reasoning', 'No reasoning provided')}")

            return action_data

        except Exception as e:
            logger.error(f"Error getting action from Claude: {e}")
            return None

    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """
        Fallback parser for non-JSON responses

        Args:
            text: Response text from Claude

        Returns:
            Dict with buttons and reasoning
        """
        # Look for button names in the text (check longer names first to avoid partial matches)
        text_lower = text.lower()
        # Sort by length descending to match "start" and "select" before "a"
        sorted_buttons = sorted(VALID_BUTTONS, key=len, reverse=True)
        for button in sorted_buttons:
            # Use word boundaries to avoid matching "a" in "advance"
            import re
            pattern = r'\b' + re.escape(button) + r'\b'
            if re.search(pattern, text_lower):
                return {
                    "buttons": [button],
                    "reasoning": text
                }

        # Default fallback
        logger.warning("Could not parse button from response, defaulting to 'a'")
        return {
            "buttons": ["a"],
            "reasoning": text
        }

    def get_action_with_thinking(
        self,
        screenshot: Image.Image,
        recent_history: Optional[str] = None,
        stuck_context: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get action with extended thinking - considers multiple options first

        Args:
            screenshot: PIL Image of current game state
            recent_history: Optional string describing recent actions
            stuck_context: Optional warning about being stuck

        Returns:
            Dict with 'buttons' and 'reasoning' keys, or None if error
        """
        try:
            # Crop to game screen only (remove UI chrome)
            from src.emulator.capture import crop_to_game_screen
            screenshot = crop_to_game_screen(screenshot)

            # Convert image to base64
            image_b64 = self.image_to_base64(screenshot)

            # Build context message
            context_parts = []

            # Add learned knowledge if available
            if self.knowledge_base:
                knowledge_context = self.knowledge_base.get_context_for_prompt()
                if knowledge_context:
                    context_parts.append(knowledge_context)

            # Add recent history
            if recent_history:
                context_parts.append(f"Recent actions:\n{recent_history}")

            # Add stuck context
            if stuck_context:
                context_parts.append(f"\n{stuck_context}")

            context = "\n\n".join(context_parts) if context_parts else ""

            # Multi-turn conversation for extended thinking
            messages = [
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
                            "text": f"""{context}

Please analyze the situation carefully:
1. What do you see on screen?
2. What are 2-3 different options for what to do next?
3. Which option is most likely to make progress?

Think through each option before deciding."""
                        }
                    ],
                }
            ]

            # First turn: Let Claude think through options
            logger.info("Using extended thinking mode...")
            thinking_response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=self.system_prompt,
                messages=messages
            )

            thinking_text = thinking_response.content[0].text
            logger.info(f"Claude's thinking: {thinking_text[:200]}...")

            # Second turn: Ask for final decision
            messages.append({
                "role": "assistant",
                "content": thinking_text
            })
            messages.append({
                "role": "user",
                "content": "Based on your analysis, what button(s) should I press? Respond in JSON format as specified."
            })

            decision_response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=self.system_prompt,
                messages=messages
            )

            response_text = decision_response.content[0].text
            logger.info(f"Claude decision: {response_text}")

            # Parse and validate the response (same logic as get_action)
            import json
            try:
                action_data = json.loads(response_text)
            except json.JSONDecodeError:
                logger.warning("Response not valid JSON, attempting to parse")
                action_data = self._parse_text_response(response_text)

            # Normalize response format
            buttons = action_data.get("buttons")
            if buttons is None:
                single_button = action_data.get("button", "").lower()
                if single_button:
                    buttons = [single_button]
                else:
                    logger.error("No buttons in response")
                    return None

            if isinstance(buttons, str):
                buttons = [buttons]

            buttons = [b.lower() for b in buttons]
            for button in buttons:
                if button not in VALID_BUTTONS:
                    logger.error(f"Invalid button in response: {button}")
                    return None

            if len(buttons) > MAX_BUTTONS_PER_RESPONSE:
                logger.warning(f"Response has {len(buttons)} buttons, truncating to {MAX_BUTTONS_PER_RESPONSE}")
                buttons = buttons[:MAX_BUTTONS_PER_RESPONSE]

            self.action_count += len(buttons)
            action_data["buttons"] = buttons
            action_data["thinking"] = thinking_text  # Include the thinking process

            logger.info(f"Action #{self.action_count}: {buttons} - {action_data.get('reasoning', 'No reasoning provided')}")

            return action_data

        except Exception as e:
            logger.error(f"Error in extended thinking mode: {e}")
            return None

    def get_action_count(self) -> int:
        """Get the number of actions taken this session"""
        return self.action_count
