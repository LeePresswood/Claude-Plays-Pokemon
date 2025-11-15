# Knowledge Base

This directory contains the learned knowledge that the AI uses to improve gameplay across sessions.

## Files

- **`learned.json`** - Auto-generated knowledge from gameplay sessions (gitignored, created automatically)
- **`seed_example.json`** - Example seed file showing the structure (committed to repo)

## How It Works

### Active Learning Process

1. **Stuck Detection** - When the AI gets stuck (same screen 3+ times), it analyzes the pattern:
   - "repeated_a_button" - Pressing A repeatedly
   - "multiple_a_presses" - Multiple A without progress
   - "repeated_up_movement" - Walking into a wall
   - etc.

2. **Tracking Solutions** - While stuck, the AI tracks every action taken

3. **Learning from Success** - When unstuck, the AI records:
   - What pattern caused the stuck state
   - What actions successfully unstuck it
   - Success rate for this pattern

4. **Knowledge Integration** - On future runs:
   - Known patterns are included in Claude's prompt
   - Successful solutions are suggested
   - Success rates guide decision-making

### Seeding Knowledge Manually

You can manually add tips to help the AI:

1. Copy `seed_example.json` to `learned.json`
2. Edit `learned.json` to add your tips:

```json
{
  "general_tips": [
    "Add helpful tips here",
    "These are shown to Claude on every decision"
  ],
  "stuck_patterns": {
    "pattern_name": {
      "description": "What the pattern looks like",
      "successful_solutions": ["action1", "action2"]
    }
  }
}
```

3. Run the agent - it will load your tips and build on them

## Tips for Seeding Knowledge

**Good general tips:**
- Specific and actionable ("Press B to close menus")
- Based on game mechanics ("PC screens are for Pokemon storage")
- Situational ("If stuck in a building, look for doors")

**Good stuck pattern solutions:**
- Action sequences that worked: `["b", "down", "down"]`
- Alternative approaches: `["start"]` (open menu to check state)
- Exploratory moves: `["left", "right"]` (try different directions)

**Location-specific tips:**
- Landmark locations ("Oak's lab is at the top of town")
- Common interactions ("PC is on the right in Pokemon Centers")
- Navigation hints ("Exit to Route 1 is north")

## Knowledge Structure

```json
{
  "version": "1.0",
  "last_updated": "2025-11-15T...",

  "general_tips": [
    "Tip 1",
    "Tip 2"
  ],

  "stuck_patterns": {
    "pattern_name": {
      "description": "Human-readable description",
      "successful_solutions": ["action sequence"],
      "times_encountered": 5,
      "total_successes": 4,
      "success_rate": 80.0
    }
  },

  "location_specific": {
    "location_name": {
      "tips": ["tip1", "tip2"],
      "common_issues": ["issue1"]
    }
  },

  "stats": {
    "total_stuck_states": 10,
    "total_unstuck_successes": 8,
    "patterns_learned": 3
  }
}
```

## Viewing Learned Knowledge

After each session, check `learned.json` to see what the AI learned:
- New patterns discovered
- Successful unstuck strategies
- Success rates for different approaches

Over time, the AI builds a comprehensive knowledge base of effective strategies!
