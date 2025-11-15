# Claude Plays Pokemon - Development Guide

This is a Python-based autonomous agent that plays Pokémon Red using Claude's vision capabilities. The agent operates in a simple loop: screenshot → Claude decision → button press → repeat.

## Project Overview

**Architecture**: Simple game loop (not MCP-based)
- Capture screenshot from emulator
- Send to Claude API with recent history
- Claude returns button press + reasoning (JSON)
- Execute button in emulator
- Repeat every 2 seconds

**Key Principles**:
- Vision-only (no game memory access)
- Short decision windows (one button at a time)
- Cost-effective (Claude Haiku ~$1/1000 actions)
- Observable (all decisions logged with screenshots)

## Project Structure

```
claude-plays-pokemon/
├── README.md, QUICKSTART.md, CLAUDE.md
├── setup.py             # Automated setup (venv + dependencies + .env)
├── requirements.txt     # Python dependencies
├── .env, .env.example   # API key (gitignored / template)
├── src/                 # Main source code
│   ├── __main__.py      # Entry point (python -m src)
│   ├── config.py        # Configuration and environment variables
│   ├── agent/
│   │   ├── vision.py    # Claude API integration
│   │   └── memory.py    # Game history tracking
│   └── emulator/
│       ├── capture.py   # Screenshot capture (pyautogui + pygetwindow)
│       └── input.py     # Keyboard automation
├── tests/
│   └── test_setup.py    # Setup validation
├── prompts/
│   └── town-descriptions/  # Strategic context for Claude
└── logs/                # Session logs and screenshots (gitignored)
```

## Common Commands

### Setup & Installation
```bash
# Initial setup (creates venv, installs deps, creates .env)
python setup.py

# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Mac/Linux

# Validate setup
python -m tests.test_setup
```

### Running the Agent
```bash
# Run the game loop
python -m src

# Stop gracefully
Ctrl+C
```

### Development
```bash
# View logs in real-time
tail -f logs/game_*.log

# Check session stats
cat logs/session_*.json | jq '.stats'

# View screenshots
ls -lt logs/screenshots/
```

## Core Files & Functions

### src/config.py
Central configuration loaded at startup:
- `ANTHROPIC_API_KEY` - Loaded from .env file (via python-dotenv)
- `MODEL` - Claude model (default: claude-3-5-haiku-20241022)
- `ACTION_DELAY` - Seconds between actions (default: 2.0)
- `MAX_ACTIONS_PER_SESSION` - Budget limit (default: 1000)
- `VALID_BUTTONS` - a, b, start, select, up, down, left, right

### src/agent/vision.py
**Key Functions**:
- `ClaudeVision.get_action(screenshot, history)` - Main API call
- `system_prompt` - Teaches Claude how to play Pokemon
- Expected response: `{"button": "a", "reasoning": "..."}`

**Modify system prompt here** to improve gameplay strategy, add type matchups, battle tactics, etc.

### src/emulator/capture.py
**Key Functions**:
- `EmulatorCapture.find_window()` - Locates emulator by title
- `EmulatorCapture.capture_screenshot()` - Gets screenshot as PIL Image

Window title must contain "mGBA" by default (configurable in src/__main__.py).

### src/emulator/input.py
**Key Functions**:
- `EmulatorInput.press_button(button)` - Sends single keypress
- `BUTTON_MAP` - Maps Pokemon buttons to keyboard keys

Default mapping: Z=A, X=B, Enter=Start, Backspace=Select

**Change mappings here** if using different emulator or keyboard layout.

## Code Style & Conventions

**Python Style**:
- Follow PEP 8
- Type hints not currently used (can be added)
- Docstrings for all public functions
- Comments for complex logic

**Logging**:
- Use Python `logging` module (already configured)
- Log levels: INFO for actions, DEBUG for details, ERROR for failures
- All logs go to both console and `logs/game_*.log`

**Error Handling**:
- Graceful failures (don't crash on API errors)
- Clear error messages
- Budget safeguards always active

## Testing

### Manual Testing
1. Run `python test_setup.py` to validate:
   - API key configured
   - Emulator window detected
   - Screenshots captured
   - Button presses work

2. Run main loop with low `MAX_ACTIONS_PER_SESSION` to test changes

### What to Test Before Committing
- Setup script creates venv and .env successfully
- Config loads without errors
- API key validation works (try invalid key)
- Emulator window detection (try wrong title)
- Screenshot capture quality
- Button press execution

## Repository Etiquette

### Branching
- `main` is stable
- Create feature branches for experiments
- Use descriptive names: `feature/stuck-detection`, `fix/screenshot-timing`

### Commits
- Descriptive commit messages
- Group related changes
- Don't commit secrets (.env is gitignored)
- Don't commit venv/ or logs/

### What's Gitignored
- `.env` - Your API key (use .env.example as template)
- `venv/` - Virtual environment
- `logs/` - All session data and screenshots
- `__pycache__/` - Python bytecode
- `.claude/` - Local Claude Code settings
- `*.gb`, `*.sav` - ROMs and save files

## Environment Setup

### Prerequisites
- Python 3.9+
- mGBA emulator (https://mgba.io/)
- Pokemon Red ROM (legally owned)
- Anthropic API key (https://console.anthropic.com/)

### First-Time Setup
1. Clone repo
2. Run `python setup.py`
3. Edit `.env` with your API key
4. Activate venv
5. Run `python test_setup.py`
6. Launch mGBA with Pokemon Red
7. Run `python main.py`

### Dependencies
See requirements.txt:
- `anthropic` - Claude API client
- `python-dotenv` - Load .env files
- `pyautogui` - Screenshot and keyboard automation
- `pygetwindow` - Window management
- `pillow` - Image processing
- `pywin32` - Windows-specific (conditional)

## Project-Specific Quirks

### Cost Management
- **Critical**: Always monitor Anthropic console for usage
- Default limit: 1000 actions/session (~$1)
- Increase `ACTION_DELAY` to slow down and save money
- Budget safeguard in config.py prevents runaway costs

### Emulator Window Focus
- Window MUST be visible (not minimized)
- Window title must contain "mGBA" (or change in main.py)
- Buttons only work when window is active
- Setup script helps verify this works

### API Rate Limits
- 2-second delay prevents rate limiting
- python-dotenv loads .env automatically
- No manual environment variable setting needed

### Vision API Limitations
- Claude sees screenshots only (no game memory)
- No save state management built-in (use emulator saves)
- No strategic planning beyond recent history (last 5-10 actions)

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Check `.env` file exists (should be created by setup.py)
- Verify key is valid (starts with sk-ant-api03-)
- Make sure python-dotenv is installed

### "Could not find emulator window"
- Verify mGBA is running
- Check window title contains "mGBA"
- Try running test_setup.py to debug
- Modify `window_title` in main.py if needed

### Button presses not working
- Ensure emulator window is focused
- Check keyboard mappings in mGBA settings
- Modify `BUTTON_MAP` in emulator/input.py if needed

### High API costs
- Check `ACTION_DELAY` setting
- Verify `MAX_ACTIONS_PER_SESSION` limit
- Monitor Anthropic console dashboard
- Consider using longer delays for testing

## Future Enhancements

**Short-term** (good first tasks):
- OCR for location detection
- Auto-load town descriptions when location changes
- Detect stuck states (repeated actions)
- Enhanced battle prompts

**Medium-term**:
- Hybrid models (Haiku for movement, Sonnet for battles)
- Knowledge base (type matchups, moves, items)
- Checkpoint system
- Parallel strategy testing

**Long-term**:
- Complete Elite Four playthrough
- Speedrun optimization
- Alternative challenges (Nuzlocke, monotype)
- Video recording and highlights

## References

- Main docs: README.md (project overview)
- Quick start: QUICKSTART.md (5-minute setup)
- Strategic context: prompts/town-descriptions/
- Anthropic docs: https://docs.anthropic.com/
- Claude Code best practices: https://www.anthropic.com/engineering/claude-code-best-practices
- mGBA: https://mgba.io/

## Remember

- This is NOT an MCP server (simple Python loop)
- Claude has NO memory between API calls
- Vision-only = Claude sees what humans see
- Always set budget limits
- Logs are essential for debugging decisions
- Test with low action limits before long runs
