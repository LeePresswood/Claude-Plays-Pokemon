"""
Unit tests for AI agent components

Test-driven development: Write tests first, then implement features.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import json


class TestClaudeVision:
    """Tests for Claude API integration"""

    def test_get_action_valid_response(self):
        """Should parse valid JSON response from Claude"""
        from src.agent.vision import ClaudeVision

        with patch('src.agent.vision.anthropic.Anthropic') as mock_anthropic:
            # Mock API response
            mock_client = Mock()
            mock_message = Mock()
            mock_message.content = [Mock(text='{"button": "a", "reasoning": "Advancing dialog"}')]
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            vision = ClaudeVision()
            screenshot = Image.new('RGB', (160, 144))
            result = vision.get_action(screenshot)

            assert result is not None
            assert result["button"] == "a"
            assert "reasoning" in result
            assert vision.get_action_count() == 1

    def test_get_action_invalid_button(self):
        """Should reject invalid button in response"""
        from src.agent.vision import ClaudeVision

        with patch('src.agent.vision.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_message = Mock()
            mock_message.content = [Mock(text='{"button": "invalid", "reasoning": "Test"}')]
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            vision = ClaudeVision()
            screenshot = Image.new('RGB', (160, 144))
            result = vision.get_action(screenshot)

            assert result is None

    def test_get_action_with_history(self):
        """Should include recent history in API call"""
        from src.agent.vision import ClaudeVision

        with patch('src.agent.vision.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_message = Mock()
            mock_message.content = [Mock(text='{"button": "up", "reasoning": "Moving north"}')]
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            vision = ClaudeVision()
            screenshot = Image.new('RGB', (160, 144))
            history = "1. Pressed a: Advanced dialog\n2. Pressed b: Closed menu"

            result = vision.get_action(screenshot, history)

            assert result is not None
            # Verify history was passed to API
            call_args = mock_client.messages.create.call_args
            assert history in str(call_args)

    def test_image_to_base64(self):
        """Should convert PIL Image to base64 string"""
        from src.agent.vision import ClaudeVision

        vision = ClaudeVision()
        image = Image.new('RGB', (10, 10), color='red')
        result = vision.image_to_base64(image)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_fallback_parser(self):
        """Should extract button from non-JSON text response"""
        from src.agent.vision import ClaudeVision

        vision = ClaudeVision()
        text = "I think we should press the up button to move forward"
        result = vision._parse_text_response(text)

        assert result["button"] == "up"
        assert result["reasoning"] == text


class TestGameMemory:
    """Tests for game state memory"""

    def test_add_action(self):
        """Should record action in history"""
        from src.agent.memory import GameMemory

        memory = GameMemory(max_history=5)
        memory.add_action("a", "Advancing dialog", "/path/to/screenshot.png")

        assert len(memory.history) == 1
        assert len(memory.session_log) == 1

    def test_max_history_limit(self):
        """Should respect max_history limit"""
        from src.agent.memory import GameMemory

        memory = GameMemory(max_history=3)

        for i in range(5):
            memory.add_action("a", f"Action {i}")

        assert len(memory.history) == 3  # Should only keep last 3
        assert len(memory.session_log) == 5  # Should keep all

    def test_get_recent_history_text(self):
        """Should format recent actions as text"""
        from src.agent.memory import GameMemory

        memory = GameMemory()
        memory.add_action("a", "First action")
        memory.add_action("b", "Second action")
        memory.add_action("up", "Third action")

        text = memory.get_recent_history_text(2)

        assert "2." in text
        assert "up" in text
        assert "Third action" in text

    def test_get_stats(self):
        """Should calculate session statistics"""
        from src.agent.memory import GameMemory

        memory = GameMemory()
        memory.add_action("a", "Test 1")
        memory.add_action("a", "Test 2")
        memory.add_action("b", "Test 3")

        stats = memory.get_stats()

        assert stats["total_actions"] == 3
        assert stats["button_distribution"]["a"] == 2
        assert stats["button_distribution"]["b"] == 1
        assert "duration_seconds" in stats

    def test_save_and_load_session(self):
        """Should save and load session logs"""
        from src.agent.memory import GameMemory
        import tempfile
        from pathlib import Path

        memory = GameMemory()
        memory.add_action("a", "Test action")

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = Path(f.name)

        try:
            memory.save_session_log(temp_path.name)

            new_memory = GameMemory()
            result = new_memory.load_session_log(temp_path)

            assert result is True
            assert len(new_memory.session_log) == 1
            assert new_memory.session_log[0]["button"] == "a"
        finally:
            temp_path.unlink(missing_ok=True)
