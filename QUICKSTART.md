# Quick Start Guide

Get Claude playing Pokemon in 5 minutes!

## Prerequisites Checklist

Before you begin, make sure you have:

- [ ] Python 3.9 or newer installed
- [ ] mGBA emulator downloaded and installed
- [ ] Pokemon Red ROM file (legally obtained)
- [ ] Anthropic API key (from <https://console.anthropic.com/>)

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
python setup.py
```

This creates a virtual environment and installs all dependencies. Then activate it:

```bash
.\venv\Scripts\activate  # Windows - you'll see (venv) in your prompt
source venv/bin/activate  # Mac/Linux
```

### 2. Set Your API Key

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```

### 3. Launch mGBA

1. Open mGBA
2. Load your Pokemon Red ROM (File → Load ROM)
3. Start a new game or load a save
4. **Leave the emulator window visible** (don't minimize it)

### 4. Test Your Setup

```bash
python -m tests.test_setup
```

Expected output:

```
============================================================
CLAUDE PLAYS POKEMON - SETUP TEST
============================================================

TEST 1: Window Detection
============================================================
✓ Found window: mGBA - Pokemon Red
  Position: (100, 100)
  Size: 640x576

TEST 2: Screenshot Capture
============================================================
✓ Screenshot captured: 640x576
  Saved as test_screenshot.png

TEST 3: API Key
============================================================
✓ API key found (length: 108)

Test button press? This will press 'A' in the emulator (y/n): n

============================================================
TEST SUMMARY
============================================================
API Key              ✓ PASS
Window Detection     ✓ PASS
Screenshot           ✓ PASS
============================================================
✓ All tests passed! You're ready to run the agent
============================================================
```

### 5. Run the Agent

```bash
python -m src
```

You should see:

```
============================================================
CLAUDE PLAYS POKEMON
============================================================

Make sure:
1. Your emulator (mGBA) is running with Pokemon Red loaded
2. The emulator window is visible (not minimized)
3. ANTHROPIC_API_KEY environment variable is set

Press Ctrl+C to stop at any time
============================================================

Starting in 3 seconds...
2024-01-15 10:30:00 - Setting up Pokemon Agent...
2024-01-15 10:30:00 - Found emulator window: mGBA - Pokemon Red
2024-01-15 10:30:00 - Setup complete!
2024-01-15 10:30:03 - Starting game loop (max 1000 actions)...
2024-01-15 10:30:03 - Claude response: {"button": "a", "reasoning": "..."}
2024-01-15 10:30:03 - Action #1: a - Advancing dialog box
```

## What Happens Next

The agent will:

1. Take a screenshot every 2 seconds
2. Send it to Claude for analysis
3. Receive a button press decision
4. Execute the button
5. Repeat

All actions are logged to:

- Console output (real-time)
- `logs/game_YYYYMMDD_HHMMSS.log` (detailed log file)
- `logs/screenshots/` (saved screenshots for each action)
- `logs/session_YYYYMMDD_HHMMSS.json` (structured session data)

## Stopping the Agent

Press `Ctrl+C` at any time to stop gracefully. The agent will:

- Save all logs
- Print session statistics
- Show estimated API costs

## Troubleshooting

### "Could not find emulator window"

- Make sure mGBA is running
- Check that the window title contains "mGBA"
- Try maximizing the emulator window

### "ANTHROPIC_API_KEY environment variable not set"

- Verify you set the environment variable
- On Windows, try closing and reopening your terminal
- Check for typos in the variable name

### "Failed to capture screenshot"

- Don't minimize the emulator window
- Make sure the window isn't hidden behind other windows
- Try moving the emulator to your primary monitor

### Button presses aren't working

- Verify keyboard controls in mGBA (Tools → Settings → Controls)
- Default mapping expects: Z=A, X=B, Enter=Start, Backspace=Select
- Make sure the emulator window is focused when the agent runs

### API errors or rate limits

- Check your API key is valid
- Verify you have credits in your Anthropic account
- Monitor usage at <https://console.anthropic.com/>

## Cost Monitoring

At the default 2-second delay:

- **~30 actions/minute** = ~1800 actions/hour
- **Estimated cost**: ~$1.80/hour with Haiku
- **Daily budget**: Set in [config.py](config.py#L24) (default: 1000 actions/session)

You can adjust `ACTION_DELAY` in [config.py](config.py) to slow down (save money) or speed up (faster gameplay).

## Next Steps

Once the agent is running successfully:

1. Watch it play for a few minutes
2. Check the logs to see Claude's reasoning
3. Review screenshots to see what it's seeing
4. Adjust settings in [config.py](config.py) if needed
5. Let it run and see how far it gets!

Good luck, and may Claude become the very best! 🎮
