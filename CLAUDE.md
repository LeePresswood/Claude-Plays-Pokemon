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
├── tests/               # Unit and integration tests
│   ├── test_setup.py    # Setup validation
│   ├── test_agent.py    # Agent unit tests
│   └── test_emulator.py # Emulator unit tests
├── notebooks/           # Jupyter notebooks for analysis (future)
│   ├── analysis/        # Session viewing, metrics
│   ├── development/     # Prompt testing, debugging
│   └── playthrough/     # Highlights, visualizations
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

**This project uses Test-Driven Development (TDD).** Write tests first, then implement features to pass them. This approach ensures clear requirements, verifiable behavior, and confidence in changes.

### Philosophy: Why Tests Make Claude More Effective

**Claude performs best when it has a clear target to iterate against.** Tests provide:

- **Objective pass/fail criteria** - No ambiguity about "done"
- **Immediate feedback** - Run tests, see results, adjust
- **Incremental improvement** - Keep iterating until success
- **Protection from overfitting** - Tests catch implementation shortcuts

Instead of vague requirements like "make it detect stuck states", tests give concrete expectations:
```python
assert memory.is_stuck() is True  # When same button 5+ times
assert memory.is_stuck() is False  # When varied buttons
```

This allows Claude to:
1. Write code
2. Run tests
3. See what failed
4. Adjust code
5. Repeat until all pass

### Quick Testing Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agent.py

# Run specific test
pytest tests/test_agent.py::TestGameMemory::test_add_action

# Run with coverage
pytest --cov=src --cov-report=html
# Open htmlcov/index.html to see coverage report

# Run and stop on first failure
pytest -x

# Run in verbose mode
pytest -v

# Run tests matching pattern
pytest -k "stuck"

# Watch for changes and re-run tests
pytest-watch
```

### TDD Workflow

#### 1. Write Tests First

Before implementing any feature, create or edit test files:

```bash
# tests/test_<module>.py
# Write tests based on expected input/output pairs
# Be explicit about expected behavior
# Don't mock what doesn't exist yet
```

**Example**:
```python
def test_detect_stuck_state():
    """Should detect when player is stuck (repeated same action 5+ times)"""
    from src.agent.memory import GameMemory

    memory = GameMemory()
    # Simulate stuck state: pressing 'up' 5 times
    for _ in range(5):
        memory.add_action("up", "Moving north")

    assert memory.is_stuck() is True
```

#### 2. Run Tests (Should Fail)

```bash
# Activate venv first
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Run tests - they should FAIL
pytest tests/test_agent.py::test_detect_stuck_state -v

# Expected output:
# FAILED - AttributeError: 'GameMemory' object has no attribute 'is_stuck'
```

**This confirms the test is working and the feature doesn't exist yet.**

#### 3. Commit the Tests

```bash
git add tests/test_agent.py
git commit -m "Add test for stuck state detection"
```

#### 4. Implement Code

**Ask Claude to implement the feature to pass the tests:**

> "Now implement the is_stuck() method in src/agent/memory.py to pass the tests. Don't modify the tests. Keep iterating until all tests pass."

Claude will write code like:

```python
# In src/agent/memory.py
def is_stuck(self, threshold: int = 5) -> bool:
    """Detect if player is stuck (repeated same action)"""
    if len(self.history) < threshold:
        return False

    recent_buttons = [action["button"] for action in list(self.history)[-threshold:]]
    return len(set(recent_buttons)) == 1  # All same button
```

#### 5. Iterate Until Tests Pass

**Claude will run tests and make adjustments:**

```bash
pytest tests/test_agent.py::test_detect_stuck_state -v
# FAILED - edge case not handled

# Claude adjusts code...
pytest tests/test_agent.py::test_detect_stuck_state -v
# PASSED!
```

**Key point**: Claude has a clear target (passing tests) to iterate against. This is much more effective than vague requirements.

#### 6. Verify with Subagent (Optional)

For complex features, ask Claude to verify the implementation independently:

> "Review the stuck state detection code independently. Does it:
> 1. Correctly identify stuck states?
> 2. Handle edge cases (empty history, threshold boundary)?
> 3. Avoid overfitting to the test cases?"

This catches issues where the implementation might work for the specific test but fail in real usage.

#### 7. Run Full Test Suite

```bash
# Run all tests to ensure nothing broke
pytest

# With coverage report
pytest --cov=src --cov-report=term-missing
```

#### 8. Commit the Implementation

**Once satisfied, ask Claude to commit:**

> "The tests pass and the implementation looks good. Please commit the code."

```bash
git add src/agent/memory.py
git commit -m "Implement stuck state detection

- Detects when player presses same button 5+ times
- Handles edge cases for empty/short history
- Tests verify behavior"
```

### Working with Claude: Example Prompts

#### Writing Tests

**Good prompt**:
> "I want to add a feature to auto-save checkpoints every 100 actions. Write unit tests for this using TDD. Don't implement the feature yet, just write comprehensive tests that verify:
> 1. Checkpoint is saved at action 100, 200, 300, etc.
> 2. Checkpoint includes action count, timestamp, and recent history
> 3. Checkpoint files are named with timestamp
> 4. Old checkpoints beyond the last 5 are deleted
>
> Make sure the tests will fail right now since the feature doesn't exist."

**Why it works**: Specific requirements, explicit about TDD, tells Claude not to implement yet.

#### Implementing Code

**Good prompt**:
> "Now implement the auto_save_checkpoint() method to pass all the tests. Don't modify the tests. Keep running the tests and iterating on your code until all tests pass. Tell me when you're done and show me the test results."

**Why it works**: Clear target (pass tests), explicit not to change tests, asks for iteration.

#### Verification

**Good prompt**:
> "The tests pass. Now review the implementation as an independent reviewer. Could the code fail in ways the tests don't cover? Are there edge cases we should add tests for?"

**Why it works**: Asks for critical review, catches overfitting.

#### Committing

**Good prompt**:
> "Great! The implementation looks solid. Please commit both the tests and the implementation with appropriate commit messages."

**Why it works**: Clear instruction to finalize the work.

### Writing Good Tests

#### DO

✅ **Test behavior, not implementation**
```python
def test_captures_screenshot():
    """Should return PIL Image when window found"""
    # Tests the what, not the how
```

✅ **Use descriptive names**
```python
def test_rejects_invalid_button_names():
    """Clear what's being tested"""
```

✅ **Test edge cases**
```python
def test_empty_history():
def test_single_action():
def test_max_history_boundary():
```

✅ **Mock external dependencies**
```python
@patch('src.emulator.capture.pyautogui.screenshot')
def test_screenshot(mock_screenshot):
    # Don't actually take screenshots in tests
```

#### DON'T

❌ **Test implementation details**
```python
def test_internal_variable_name():
    # Too brittle
```

❌ **Write tests after code**
```python
# Defeats the purpose of TDD
```

❌ **Mock things that don't exist**
```python
# Write the test for real behavior first
```

❌ **Have tests depend on each other**
```python
# Each test should be independent
```

### Test Structure

```
tests/
├── __init__.py
├── test_setup.py       # Integration test for setup
├── test_emulator.py    # Unit tests for emulator
├── test_agent.py       # Unit tests for agent
└── test_integration.py # End-to-end tests (future)
```

### Coverage Goals

- Aim for **>80% code coverage**
- Focus on **critical paths** (agent decisions, emulator integration)
- Don't test trivial code (getters/setters)
- Test **happy paths** and **error cases**

Check coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

### Manual Testing

1. **Setup validation**: `python -m tests.test_setup`
2. **Integration test**: Run with low `MAX_ACTIONS_PER_SESSION`

### What to Test Before Committing

- All unit tests pass (`pytest`)
- Coverage >80% for new code
- Setup script works (`python setup.py`)
- Integration test runs (`python -m src` with emulator)

### Benefits

- **Confidence**: Tests prove features work
- **Regression Prevention**: Changes don't break existing features
- **Documentation**: Tests show how code should be used
- **Faster Debugging**: Failing tests pinpoint issues
- **Better Design**: Writing tests first leads to better APIs

---

**Remember**: Tests are your target. Give Claude a clear target to iterate against, and it will keep improving until it succeeds.

## Repository Etiquette

### Documentation Organization Rule

**Avoid creating new top-level documentation or ruleset files.** Keep the root directory clean:
- Consolidate related documentation into existing files (like this CLAUDE.md)
- If new documentation is needed, organize it in subdirectories (e.g., `docs/`, `prompts/`)
- Exception: Core project files (README.md, QUICKSTART.md, setup.py, requirements.txt)

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

## Jupyter Notebooks for Analysis

**Once gameplay sessions generate data, use Jupyter notebooks to analyze and visualize the AI's performance.** This is a recommended workflow from Anthropic's Claude Code best practices - notebooks provide an excellent way to explore session logs, understand decision patterns, and create shareable visualizations.

### When to Create Notebooks

**Proactive reminder for Claude**: When the user has run gameplay sessions and accumulated logs, suggest creating notebooks to:
- Visualize session data with screenshots and decisions
- Analyze performance metrics and patterns
- Debug issues with interactive exploration
- Create presentation-ready highlights

### Recommended Structure

Following the documentation organization rule, notebooks should live in a dedicated directory:

```
notebooks/
├── README.md                    # Notebook usage guide
├── analysis/
│   ├── session_viewer.ipynb    # Browse sessions with screenshots
│   ├── performance_stats.ipynb # Button patterns, API costs
│   └── exploration_map.ipynb   # Movement patterns, areas visited
├── development/
│   ├── prompt_testing.ipynb    # Test vision prompts interactively
│   ├── stuck_detection.ipynb   # Debug/tune stuck state logic
│   └── vision_api_test.ipynb   # Test API with sample screenshots
└── playthrough/
    ├── highlights.ipynb         # Curated moments from runs
    ├── battle_analysis.ipynb    # Type matchups, move choices
    └── images/                  # Curated screenshots (committed, not gitignored)
        ├── first_pokemon.png    # Key moments worth sharing
        └── elite_four_victory.png
```

### Use Cases

**Analysis & Visualization**:
- Session replay viewer - chronological screenshots with decisions overlaid
- Performance metrics - buttons pressed over time, decision patterns
- Exploration analysis - which areas visited, movement heatmaps
- Cost analysis - API usage, tokens per decision, cost per milestone

**Documentation & Sharing**:
- Playthrough highlights - key moments with screenshots
- Learning insights - what strategies worked/didn't work
- Battle analysis - type matchup decisions, move effectiveness
- Progress tracking - badges earned, Pokemon caught, items found

**Development & Debugging**:
- Test vision API with sample screenshots interactively
- Prototype new prompts and see results immediately
- Debug stuck state detection with real session data
- Visualize game state memory and history patterns

### Working with Claude on Notebooks

**Recommended workflow**: Open Claude Code and a .ipynb file side-by-side in VS Code. Claude can:
- Read notebook outputs including images
- Interpret data visualizations
- Add new cells with analysis code
- Clean up and improve aesthetics

**Useful prompts**:
> "Create a session viewer notebook that loads logs/session_*.json and displays screenshots with decision overlays"

> "Make this notebook aesthetically pleasing for sharing with colleagues" (reminds Claude to optimize for human viewing)

> "Add visualizations showing button press patterns over time from the session logs"

> "Debug why the agent got stuck - load the session and show me the last 20 actions with screenshots"

### Integration with Session Logs

Notebooks should work seamlessly with the logging system:
- Read `logs/session_*.json` for structured data
- Load `logs/screenshots/*.png` for visuals
- Parse `logs/game_*.log` for detailed traces
- Combine data sources for comprehensive analysis

### Dependencies

Add to requirements.txt when creating notebooks:
```
jupyter>=1.0.0
notebook>=7.0.0
matplotlib>=3.7.0  # For basic plots
pandas>=2.0.0      # For data analysis
```

### Data Management Strategy

**Runtime artifacts vs. curated highlights:**

- **Never commit**: `logs/` directory (session data, screenshots) - gitignored runtime artifacts
- **Do commit**: Curated notebook outputs for sharing highlights and insights

**Workflow for shareable notebooks**:
1. Develop notebook using local `logs/` data (gitignored)
2. For highlights notebooks, copy key screenshots into `notebooks/playthrough/images/`
3. Update notebook to reference the copied images (not `../../logs/`)
4. Clear all other notebook outputs before committing
5. Commit the notebook code + curated images only

This keeps the repo clean while allowing you to share interesting moments from your playthroughs.

### Best Practices

- **Clean outputs before committing** - Large image outputs bloat git history
- **Clear development notebook outputs** - Only commit outputs for curated highlights
- **Use relative paths** - `../logs/` for local data, `./images/` for committed highlights
- **Document assumptions** - What data format is expected
- **Keep notebooks focused** - One clear purpose per notebook
- **Make them aesthetically pleasing** - Optimize for human viewers
- **Add markdown context** - Explain what each section does
- **Separate runtime from highlights** - Local logs stay gitignored, curated content gets committed

### Future Enhancement Checklist

When ready to add notebooks:
- [ ] Create `notebooks/` directory structure (analysis/, development/, playthrough/)
- [ ] Create `notebooks/playthrough/images/` for curated screenshots
- [ ] Add Jupyter dependencies to requirements.txt
- [ ] Create `notebooks/README.md` with usage guide and data management rules
- [ ] Build `session_viewer.ipynb` as first notebook (uses `../logs/` data)
- [ ] Add `.ipynb_checkpoints/` to .gitignore (already done)
- [ ] Create example highlight with curated image workflow

---

**Remember**: Notebooks are powerful for post-run analysis. Once session data exists, Claude should proactively suggest creating notebooks to help understand the AI's gameplay patterns.

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
- **Jupyter notebooks** - Create session viewer after first gameplay runs
- OCR for location detection
- Auto-load town descriptions when location changes
- Detect stuck states (repeated actions)
- Enhanced battle prompts

**Medium-term**:
- Hybrid models (Haiku for movement, Sonnet for battles)
- Knowledge base (type matchups, moves, items)
- Checkpoint system
- Parallel strategy testing
- **Analysis notebooks** - Performance metrics, exploration heatmaps

**Long-term**:
- Complete Elite Four playthrough
- Speedrun optimization
- Alternative challenges (Nuzlocke, monotype)
- Video recording and highlights
- **Playthrough highlights notebook** - Shareable visualization of best moments

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
