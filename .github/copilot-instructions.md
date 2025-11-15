# Claude Plays Pokemon - Autonomous AI Pokemon Player

This is a Python-based autonomous agent that plays Pokémon Red using Claude's vision capabilities via the Anthropic API. The agent operates in a simple loop: screenshot → Claude decision → button press → repeat.

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Current Project State

The project is fully implemented and ready to run. The repository contains:
- **Python implementation**: Complete game loop with emulator integration
- **Claude API integration**: Vision-based decision making using Claude Haiku
- **Logging system**: Comprehensive session tracking and screenshot saving
- **Test utilities**: Setup validation script
- **Documentation**: README, QUICKSTART guide, and town descriptions for context

## Project Structure

```
claude-plays-pokemon/
├── main.py              # Main game loop - start here
├── config.py            # Configuration (API key, model, throttling)
├── test_setup.py        # Setup validation script
├── requirements.txt     # Python dependencies
├── emulator/
│   ├── capture.py       # Screenshot capture via pyautogui
│   └── input.py         # Button press execution
├── agent/
│   ├── vision.py        # Claude API integration
│   └── memory.py        # Game history tracking
├── prompts/
│   └── town-descriptions/  # Strategic context for Claude
└── logs/                # Session logs and screenshots
```

## Working Effectively

### Understanding the Architecture

**Simple Loop Design:**
1. Capture screenshot from emulator window (mGBA)
2. Send to Claude via Anthropic API with recent history
3. Claude returns JSON with button press + reasoning
4. Execute button press in emulator
5. Repeat every 2 seconds (configurable)

**Key Design Principles:**
- **Vision-only**: No game memory access, only screenshots
- **Short decision windows**: Claude decides one button at a time
- **Cost-effective**: Uses Claude Haiku (~$1/1000 actions)
- **Observable**: All decisions logged with screenshots
- **Safe**: Budget limits and throttling built-in

### Important Files

**config.py** - Central configuration:
- `ANTHROPIC_API_KEY`: Loaded from environment variable
- `MODEL`: Claude Haiku by default
- `ACTION_DELAY`: 2 seconds between actions
- `MAX_ACTIONS_PER_SESSION`: 1000 action limit
- `VALID_BUTTONS`: a, b, start, select, up, down, left, right

**agent/vision.py** - Claude integration:
- `ClaudeVision.get_action()`: Main API call
- System prompt teaches Claude how to play Pokemon
- Expects JSON response: `{"button": "a", "reasoning": "..."}`
- Fallback parser for non-JSON responses

**emulator/capture.py** - Screenshot capture:
- Uses `pygetwindow` to find emulator window
- Uses `pyautogui` to capture screenshots
- Window title must contain "mGBA" (configurable)

**emulator/input.py** - Button execution:
- Maps Pokemon buttons to keyboard keys
- Default: Z=A, X=B, Enter=Start, Backspace=Select
- Sends keypresses to active window

## Common Development Tasks

### Testing and Running

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key (required)
export ANTHROPIC_API_KEY="your-key-here"  # Linux/Mac
$env:ANTHROPIC_API_KEY="your-key-here"    # Windows PowerShell

# Validate setup before running
python test_setup.py

# Run the agent
python main.py
```

### Configuration Changes

```python
# In config.py:
ACTION_DELAY = 2.0              # Speed up/slow down gameplay
MAX_ACTIONS_PER_SESSION = 1000  # Budget control
MODEL = "claude-3-5-haiku-20241022"  # Change model
SAVE_SCREENSHOTS = True         # Toggle screenshot saving
```

### Debugging

```bash
# Check logs
tail -f logs/game_*.log

# View screenshots
ls -lt logs/screenshots/

# Check session statistics
cat logs/session_*.json | jq '.stats'
```

### Code Modifications

**To change button mappings** (if using different emulator):
```python
# In emulator/input.py - EmulatorInput.BUTTON_MAP
BUTTON_MAP = {
    "a": "z",      # Change to your emulator's key
    "b": "x",
    # ... etc
}
```

**To improve Claude's decisions**:
```python
# In agent/vision.py - ClaudeVision.system_prompt
# Modify the system prompt to add strategies, type matchups, etc.
```

**To add location context**:
```python
# Load town descriptions from prompts/town-descriptions/
# Include in recent_history when calling vision.get_action()
```

## Current Capabilities

### What Works
- ✅ Window detection and screenshot capture
- ✅ Claude API integration with vision
- ✅ Button press execution
- ✅ Game history tracking
- ✅ Session logging and statistics
- ✅ Cost tracking and budget limits
- ✅ Graceful shutdown (Ctrl+C)

### Current Limitations
- ⚠️ No game state recognition (purely visual)
- ⚠️ No strategic planning beyond recent history
- ⚠️ No battle strategy (just follows Claude's judgment)
- ⚠️ No save state management
- ⚠️ No automatic recovery from stuck states

## Future Enhancement Ideas

### Short-term Improvements
1. **Location detection**: OCR to read town names from screenshots
2. **Context loading**: Auto-load town descriptions when location detected
3. **Stuck detection**: Detect repeated actions and trigger recovery
4. **Battle focus**: Enhanced prompts for battle situations

### Medium-term Features
1. **Hybrid model approach**: Haiku for movement, Sonnet for battles
2. **Knowledge base**: Type matchups, move lists, item effects
3. **Checkpoint system**: Save progress at milestones
4. **Multi-run comparison**: Run multiple strategies in parallel

### Long-term Goals
1. **Complete playthrough**: Successfully beat Elite Four
2. **Speedrun optimization**: Find efficient routing
3. **Different strategies**: Nuzlocke, monotype runs, etc.
4. **Video recording**: Create highlight reels

## Dependencies

**Python packages** (see requirements.txt):
- `anthropic>=0.39.0` - Claude API client
- `pyautogui>=0.9.54` - Screenshot and keyboard automation
- `pygetwindow>=0.0.9` - Window management
- `pillow>=10.0.0` - Image processing
- `pywin32>=306` - Windows-specific window management

**External requirements**:
- Python 3.9+
- mGBA emulator (or compatible)
- Pokemon Red ROM
- Anthropic API key

## Cost Management

**Default settings** (2-second delay, Haiku):
- ~30 actions/minute
- ~1800 actions/hour
- ~$1.80/hour
- ~$1/session (1000 action limit)

**To reduce costs**:
- Increase `ACTION_DELAY` in config.py
- Lower `MAX_ACTIONS_PER_SESSION`
- Set daily budget limits in Anthropic console
- Use local testing before live runs

## Troubleshooting

**"Could not find emulator window"**:
- Check window title contains "mGBA"
- Modify `window_title` parameter in main.py
- Try `python test_setup.py` to debug

**"API key not set"**:
- Verify environment variable: `echo $ANTHROPIC_API_KEY`
- Check for typos in variable name
- Try setting in same terminal session where running script

**Button presses not working**:
- Verify emulator keyboard mappings
- Check emulator window is active/focused
- Modify `BUTTON_MAP` in emulator/input.py if needed

**High API costs**:
- Check `ACTION_DELAY` is not too low
- Verify `MAX_ACTIONS_PER_SESSION` limit is active
- Monitor usage in Anthropic console
- Consider increasing delay or using caching

## References

- **Main Documentation**: README.md - comprehensive project overview
- **Quick Start**: QUICKSTART.md - 5-minute setup guide
- **Town Context**: prompts/town-descriptions/ - strategic info
- **Anthropic Docs**: https://docs.anthropic.com/
- **mGBA**: https://mgba.io/

## Remember

- This is a simple loop architecture, not an MCP server
- Claude has NO memory between API calls - context must be explicit
- Vision-only means Claude sees what a human sees
- Cost control is important - always set limits
- Logs are your friend for debugging decisions
