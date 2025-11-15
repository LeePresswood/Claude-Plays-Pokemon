"""
Unit tests for knowledge base and active learning system

Test-driven development: Write tests first, then implement features.
"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch


class TestKnowledgeBase:
    """Tests for KnowledgeBase learning system"""

    def test_initialization_creates_default_knowledge(self):
        """Should initialize with default knowledge structure"""
        from src.agent.knowledge import KnowledgeBase

        with tempfile.TemporaryDirectory() as tmpdir:
            kb_file = Path(tmpdir) / "test_knowledge.json"
            kb = KnowledgeBase(knowledge_file=kb_file)

            assert kb.knowledge is not None
            assert "general_tips" in kb.knowledge
            assert "stuck_patterns" in kb.knowledge
            assert "stats" in kb.knowledge

    def test_load_existing_knowledge(self):
        """Should load knowledge from existing file"""
        from src.agent.knowledge import KnowledgeBase

        with tempfile.TemporaryDirectory() as tmpdir:
            kb_file = Path(tmpdir) / "test_knowledge.json"

            # Create a knowledge file
            test_data = {
                "version": "1.0",
                "general_tips": ["Test tip"],
                "stuck_patterns": {},
                "location_specific": {},
                "stats": {"total_stuck_states": 5}
            }
            with open(kb_file, 'w') as f:
                json.dump(test_data, f)

            # Load it
            kb = KnowledgeBase(knowledge_file=kb_file)

            assert kb.knowledge["general_tips"] == ["Test tip"]
            assert kb.knowledge["stats"]["total_stuck_states"] == 5

    def test_save_knowledge(self):
        """Should save knowledge to file"""
        from src.agent.knowledge import KnowledgeBase

        with tempfile.TemporaryDirectory() as tmpdir:
            kb_file = Path(tmpdir) / "test_knowledge.json"
            kb = KnowledgeBase(knowledge_file=kb_file)

            kb.knowledge["general_tips"].append("New tip")
            kb.save_knowledge()

            # Verify file was created and contains the tip
            assert kb_file.exists()
            with open(kb_file, 'r') as f:
                data = json.load(f)
            assert "New tip" in data["general_tips"]

    def test_analyze_stuck_pattern_repeated_button(self):
        """Should detect repeated button pattern"""
        from src.agent.knowledge import KnowledgeBase

        kb = KnowledgeBase()
        actions = [
            {"button": "a", "reasoning": "Test 1"},
            {"button": "a", "reasoning": "Test 2"},
            {"button": "a", "reasoning": "Test 3"},
            {"button": "a", "reasoning": "Test 4"},
            {"button": "a", "reasoning": "Test 5"},
        ]

        pattern = kb.analyze_stuck_pattern(actions)
        assert pattern == "repeated_a_button"

    def test_analyze_stuck_pattern_multiple_a_presses(self):
        """Should detect multiple A presses pattern"""
        from src.agent.knowledge import KnowledgeBase

        kb = KnowledgeBase()
        actions = [
            {"button": "up", "reasoning": "Test 1"},
            {"button": "a", "reasoning": "Test 2"},
            {"button": "a", "reasoning": "Test 3"},
            {"button": "down", "reasoning": "Test 4"},
            {"button": "a", "reasoning": "Test 5"},
        ]

        pattern = kb.analyze_stuck_pattern(actions)
        assert pattern == "multiple_a_presses"

    def test_analyze_stuck_pattern_repeated_movement(self):
        """Should detect repeated directional movement"""
        from src.agent.knowledge import KnowledgeBase

        kb = KnowledgeBase()
        actions = [
            {"button": "up", "reasoning": "Test 1"},
            {"button": "up", "reasoning": "Test 2"},
            {"button": "up", "reasoning": "Test 3"},
            {"button": "up", "reasoning": "Test 4"},
        ]

        pattern = kb.analyze_stuck_pattern(actions)
        assert pattern == "repeated_up_movement"

    def test_analyze_stuck_pattern_alternating(self):
        """Should detect alternating button pattern"""
        from src.agent.knowledge import KnowledgeBase

        kb = KnowledgeBase()
        actions = [
            {"button": "a", "reasoning": "Test 1"},
            {"button": "b", "reasoning": "Test 2"},
            {"button": "a", "reasoning": "Test 3"},
            {"button": "b", "reasoning": "Test 4"},
        ]

        pattern = kb.analyze_stuck_pattern(actions)
        assert pattern in ["alternating_a_and_b", "alternating_b_and_a"]

    def test_analyze_stuck_pattern_insufficient_history(self):
        """Should return None if not enough history"""
        from src.agent.knowledge import KnowledgeBase

        kb = KnowledgeBase()
        actions = [
            {"button": "a", "reasoning": "Test 1"},
        ]

        pattern = kb.analyze_stuck_pattern(actions)
        assert pattern is None

    def test_record_stuck_state(self):
        """Should record stuck state and update stats"""
        from src.agent.knowledge import KnowledgeBase

        kb = KnowledgeBase()
        initial_count = kb.knowledge["stats"]["total_stuck_states"]

        actions = [{"button": "a", "reasoning": "Test"}]
        pattern = "repeated_a_button"
        kb.record_stuck_state(pattern, actions)

        assert kb.current_stuck_pattern == pattern
        assert kb.knowledge["stats"]["total_stuck_states"] == initial_count + 1

    def test_record_unstuck_success(self):
        """Should record successful unstuck and learn solution"""
        from src.agent.knowledge import KnowledgeBase

        with tempfile.TemporaryDirectory() as tmpdir:
            kb_file = Path(tmpdir) / "test_knowledge.json"
            kb = KnowledgeBase(knowledge_file=kb_file)

            # Set up stuck state
            pattern = "repeated_a_button"
            kb.record_stuck_state(pattern, [])

            # Record successful unstuck
            unstuck_actions = [
                {"button": "b", "reasoning": "Cancel"},
                {"button": "down", "reasoning": "Move"},
            ]
            kb.record_unstuck_success(unstuck_actions)

            # Verify learning
            assert pattern in kb.knowledge["stuck_patterns"]
            pattern_data = kb.knowledge["stuck_patterns"][pattern]
            assert "b -> down" in pattern_data["successful_solutions"]
            assert pattern_data["total_successes"] == 1
            assert pattern_data["success_rate"] == 100.0

    def test_record_unstuck_updates_existing_pattern(self):
        """Should update existing pattern with new solution"""
        from src.agent.knowledge import KnowledgeBase

        with tempfile.TemporaryDirectory() as tmpdir:
            kb_file = Path(tmpdir) / "test_knowledge.json"
            kb = KnowledgeBase(knowledge_file=kb_file)

            # First unstuck
            pattern = "repeated_a_button"
            kb.record_stuck_state(pattern, [])
            kb.record_unstuck_success([{"button": "b", "reasoning": "Cancel"}])

            # Second unstuck with same pattern
            kb.record_stuck_state(pattern, [])
            kb.record_unstuck_success([{"button": "down", "reasoning": "Move"}])

            # Verify both solutions are stored
            pattern_data = kb.knowledge["stuck_patterns"][pattern]
            assert len(pattern_data["successful_solutions"]) == 2
            assert "b" in pattern_data["successful_solutions"]
            assert "down" in pattern_data["successful_solutions"]
            assert pattern_data["times_encountered"] == 2
            assert pattern_data["total_successes"] == 2

    def test_get_suggestion_for_known_pattern(self):
        """Should provide suggestion for known stuck pattern"""
        from src.agent.knowledge import KnowledgeBase

        kb = KnowledgeBase()

        # Manually add a known pattern
        kb.knowledge["stuck_patterns"]["repeated_a_button"] = {
            "description": "Pressing A repeatedly",
            "successful_solutions": ["b", "down"],
            "success_rate": 80.0
        }

        # Create actions that match the pattern
        actions = [
            {"button": "a", "reasoning": "Test"} for _ in range(5)
        ]

        suggestion = kb.get_suggestion_for_stuck_state(actions)

        assert suggestion is not None
        assert "b" in suggestion
        assert "80" in suggestion or "success" in suggestion.lower()

    def test_get_suggestion_for_unknown_pattern(self):
        """Should return None for unknown pattern"""
        from src.agent.knowledge import KnowledgeBase

        kb = KnowledgeBase()
        actions = [{"button": "a", "reasoning": "Test"}]

        suggestion = kb.get_suggestion_for_stuck_state(actions)
        assert suggestion is None

    def test_get_context_for_prompt(self):
        """Should format knowledge as prompt context"""
        from src.agent.knowledge import KnowledgeBase

        kb = KnowledgeBase()
        kb.knowledge["general_tips"] = ["Tip 1", "Tip 2"]
        kb.knowledge["stuck_patterns"]["test_pattern"] = {
            "description": "Test Pattern",
            "successful_solutions": ["b", "down"],
            "success_rate": 90.0
        }

        context = kb.get_context_for_prompt()

        assert "Tip 1" in context
        assert "Test Pattern" in context
        assert "b, down" in context or "b" in context and "down" in context

    def test_add_general_tip(self):
        """Should add general tip to knowledge base"""
        from src.agent.knowledge import KnowledgeBase

        with tempfile.TemporaryDirectory() as tmpdir:
            kb_file = Path(tmpdir) / "test_knowledge.json"
            kb = KnowledgeBase(knowledge_file=kb_file)

            initial_count = len(kb.knowledge["general_tips"])
            kb.add_general_tip("New manual tip")

            assert len(kb.knowledge["general_tips"]) == initial_count + 1
            assert "New manual tip" in kb.knowledge["general_tips"]

    def test_add_duplicate_tip_ignored(self):
        """Should not add duplicate tips"""
        from src.agent.knowledge import KnowledgeBase

        kb = KnowledgeBase()
        kb.knowledge["general_tips"] = ["Existing tip"]

        kb.add_general_tip("Existing tip")

        assert kb.knowledge["general_tips"].count("Existing tip") == 1

    def test_get_stats(self):
        """Should return copy of stats"""
        from src.agent.knowledge import KnowledgeBase

        kb = KnowledgeBase()
        kb.knowledge["stats"]["total_stuck_states"] = 5

        stats = kb.get_stats()

        assert stats["total_stuck_states"] == 5
        # Verify it's a copy (modifying shouldn't affect original)
        stats["total_stuck_states"] = 10
        assert kb.knowledge["stats"]["total_stuck_states"] == 5

    def test_pattern_to_description_conversion(self):
        """Should convert pattern names to readable descriptions"""
        from src.agent.knowledge import KnowledgeBase

        kb = KnowledgeBase()

        # Test various pattern conversions
        assert "A" in kb._pattern_to_description("repeated_a_button")
        assert "up" in kb._pattern_to_description("repeated_up_movement")
        assert "Multiple A" in kb._pattern_to_description("multiple_a_presses")

    def test_record_unstuck_without_stuck_state(self):
        """Should handle unstuck record without prior stuck state"""
        from src.agent.knowledge import KnowledgeBase

        with tempfile.TemporaryDirectory() as tmpdir:
            kb_file = Path(tmpdir) / "test_knowledge.json"
            kb = KnowledgeBase(knowledge_file=kb_file)

            initial_successes = kb.knowledge["stats"]["total_unstuck_successes"]

            # Try to record unstuck without setting stuck state first
            kb.record_unstuck_success([{"button": "a", "reasoning": "Test"}])

            # Should not crash, just log a warning
            # Stats should not be affected
            assert kb.knowledge["stats"]["total_unstuck_successes"] == initial_successes
