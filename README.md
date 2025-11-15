# Claude Plays Pokemon

> An autonomous AI agent that plays Pokémon Red using computer vision and the Anthropic API

This project is an experimental AI agent that plays **Pokémon Red** autonomously by analyzing screenshots and making decisions through Claude (Anthropic's LLM). Inspired by the legendary [Twitch Plays Pokémon](https://en.wikipedia.org/wiki/Twitch_Plays_Pok%C3%A9mon), this project explores how modern vision-capable AI can tackle classic games through a simple perception → decision → action loop.

---

## Project Goals

-   Let Claude play Pokémon Red autonomously using vision-based gameplay
-   Explore how AI handles long-term planning (beat the game) vs. short-term execution (navigate menus, battles)
-   Test different prompting strategies and model choices (Haiku vs. Sonnet) for cost-effective gameplay
-   Provide a reproducible testbed for vision-based game agents
-   Learn by building something fun and slightly absurd

---

## Why Pokémon Red?

Pokémon Red is an ideal choice for AI-driven gameplay because:

**State-based gameplay**: The game can be effectively represented as a series of discrete state transitions. In the overworld, movement consists of four directional inputs. In battles, players navigate menus to select actions. This structure maps naturally to AI decision-making.

**No time pressure**: Unlike action games, Pokémon Red is entirely turn-based. There are no time-based events or real-time reactions required. The AI can deliberate as long as needed before making each decision.

**Proven with chaotic inputs**: [Twitch Plays Pokémon](https://en.wikipedia.org/wiki/Twitch_Plays_Pok%C3%A9mon) demonstrated that even with thousands of people sending random inputs, the game's robust state machine allowed progression toward goals. If crowd chaos worked, structured AI should work even better.

**Rich decision space**: Despite its simple controls, the game requires strategy (team composition, type matchups), planning (routing, item management), and problem-solving (puzzles, HM usage). This makes it interesting for AI experimentation beyond trivial games.

---

## How It Works

The agent operates in a continuous loop:

1. **Capture** a screenshot from the Game Boy emulator
2. **Send** the image to Claude (via Anthropic API) along with recent game history
3. **Receive** a decision (button press + reasoning) as structured JSON
4. **Execute** the button press in the emulator
5. **Repeat**

The AI has no direct access to game memory or state – it must rely entirely on visual understanding of screenshots, just like a human player would. Context about previous actions helps it maintain continuity across decisions.

---

## Project Structure

```
claude-plays-pokemon/
├── README.md, QUICKSTART.md, CLAUDE.md
├── requirements.txt, setup.py
├── .env.example
├── src/                   # Main source code
│   ├── __main__.py        # Entry point (python -m src)
│   ├── config.py          # API keys, model selection, throttle settings
│   ├── agent/
│   │   ├── vision.py      # Claude API interaction
│   │   └── memory.py      # Game history tracking
│   └── emulator/
│       ├── capture.py     # Screenshot capture from emulator
│       └── input.py       # Button press execution
├── tests/
│   └── test_setup.py      # Setup validation
├── prompts/
│   └── town-descriptions/ # Strategic context for Claude
└── logs/                  # Session logs and screenshots (gitignored)
```

---

## Phased Milestones

### Phase 1: Foundations

-   Collect starter Pokémon
-   Catch a wild Pokémon
-   Defeat first trainer
-   Evolve first Pokémon
-   Win first Gym Badge

### Phase 2: Mobility & Utilities

-   Learn and use HM Cut
-   Learn and use HM Flash
-   Unlock Fly (optional but recommended)
-   Begin long-distance exploration

### Phase 3: Team Rocket & Midgame

-   Defeat Team Rocket in Celadon
-   Defeat Team Rocket in Saffron
-   Progression toward Surf unlock

### Phase 4: Legendary Access

-   Learn HM Surf → Catch/defeat Zapdos
-   Learn HM Strength → Catch/defeat Articuno
-   Retrieve Cinnabar Gym key
-   Catch/defeat Moltres

### Phase 5: Endgame

-   Defeat 8th Gym
-   Reach Indigo Plateau
-   Defeat Elite Four + Rival → Become Champion
-   Catch/defeat Mewtwo

---

## Technical Design Decisions

### Vision-First Approach

The AI relies entirely on screenshot analysis rather than reading game memory. This makes it:

-   More general (works with any emulator)
-   More human-like (same information a player has)
-   More challenging (must interpret visuals correctly)

### Short Decision Windows

Rather than planning hundreds of moves ahead, the AI makes decisions frequently (every 1-2 seconds). This:

-   Reduces hallucination risk from long planning horizons
-   Allows rapid error correction
-   Keeps context windows manageable
-   Mirrors how humans play (constant reassessment)

### Model Selection Strategy

-   **Claude Haiku**: Fast, cheap decisions for routine gameplay (walking, menu navigation)
    -   ~$0.40 per 1000 screenshots
    -   Good for 90%+ of decisions
-   **Claude Sonnet**: Reserved for complex strategic decisions (team composition, gym strategy)
    -   Can be triggered when Haiku expresses uncertainty
    -   Used sparingly to control costs

### Memory & State Tracking

-   Keep recent action history (last 10-20 actions) in context
-   Log structured game state when possible (badges, team, location)
-   Save periodic checkpoints for resuming gameplay
-   No persistent memory between API calls – context must be explicit

### Error Detection & Recovery

The AI should be able to:

-   Recognize when it's stuck (repeating same actions)
-   Detect when it enters wrong buildings/areas
-   Backtrack to known good states
-   Request help (Sonnet) when Haiku is confused

---

## Example: AI Decision Flow

Here's how the AI might navigate from the Player's House to Oak's Lab:

**Perception**:  
Screenshot shows player outside house in Pallet Town. Oak's Lab is visible to the southeast.

**Recent History**:  
Just exited Player's House. No previous attempts to reach Oak's Lab.

**Decision** (returned as JSON):

```json
{
    "action": "DOWN",
    "reasoning": "Need to move south from house toward main path, then east to Oak's Lab. First step: move down."
}
```

**Next Iteration**:  
After moving down, AI sees it's now on the main path. Decides to press RIGHT to move east toward lab...

This continues until the AI reaches the lab entrance and presses A to enter.

---

## Getting Started

### Prerequisites

-   **Python 3.9+**
-   **Game Boy emulator**: mGBA recommended (free, cross-platform, lightweight)
    -   Download: <https://mgba.io/downloads.html>
-   **Anthropic API key**: Get one at <https://console.anthropic.com/>
-   **Pokémon Red ROM**: You must legally own a copy

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/LeePresswood/claude-plays-pokemon
cd claude-plays-pokemon
```

2. **Run setup**

```bash
python setup.py
```

This will automatically:
- Create a virtual environment
- Install all dependencies
- Create a `.env` file from the template

3. **Configure your API key**

Edit the `.env` file and add your API key:

```
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```

4. **Activate the virtual environment**

```bash
.\venv\Scripts\activate  # Windows PowerShell
source venv/bin/activate  # Mac/Linux
```

5. **Configure your emulator (mGBA)**
    - Launch mGBA
    - Load your Pokémon Red ROM (File → Load ROM)
    - **Important**: Make sure the window title contains "mGBA"
    - Recommended: Set the emulator to 2x or 3x window size for better screenshots
    - Optional: Configure keyboard controls (Tools → Settings → Controls)

### Running the Agent

1. **Test your setup first**

```bash
python -m tests.test_setup
```

This will verify:

- API key is configured
- Emulator window can be detected
- Screenshots can be captured
- Button presses work correctly

2. **Start the game loop**

```bash
python -m src
```

The agent will:

- Find your emulator window
- Start taking screenshots every 2 seconds
- Send them to Claude for decisions
- Execute button presses automatically
- Log everything to `logs/` directory

3. **Monitor progress**

- Watch the console output for real-time decisions
- Check `logs/` for detailed session logs and screenshots
- Press `Ctrl+C` to stop at any time

### Tips for First Run

- **Start from the beginning**: Load a new game or early save for best results
- **Keep emulator visible**: The window must not be minimized
- **Watch the first few actions**: Verify the agent is working correctly
- **Check costs**: Monitor your Anthropic console for API usage
- **Save progress**: Use emulator save states to preserve progress

---

## Cost Estimates

Using Claude Haiku for standard gameplay:

-   1000 decisions (several hours): ~$1
-   Full day of gameplay: ~$5-10
-   Complete playthrough estimate: $50-150

Costs can be reduced by:

-   Setting API rate limits
-   Adding sleep delays between actions
-   Using prompt caching for repeated game context
-   Running in "debug mode" with local logs before live API calls

---

## Future Enhancements

**Potential improvements**:

-   Image recognition preprocessing to identify game elements (HP bars, menu states)
-   Fine-tuned prompts for specific game situations (battles, puzzles, shopping)
-   Hybrid approach: Haiku for execution, Sonnet for strategy
-   Persistent knowledge base of Pokémon stats, moves, and type matchups
-   Gameplay recording and replay for analysis
-   Multiple parallel runs with different strategies

---

## Contributing

This is an experimental learning project. Contributions, suggestions, and gameplay recordings are welcome! Feel free to:

-   Open issues for bugs or ideas
-   Submit PRs for improvements
-   Share your own gameplay results
-   Suggest better prompting strategies

---

## License

[Unlicense](LICENSE) - Public domain. Do whatever you want with this code.

---

## Acknowledgments

-   Inspired by [Twitch Plays Pokémon](https://en.wikipedia.org/wiki/Twitch_Plays_Pok%C3%A9mon)
-   Built with [Anthropic's Claude](https://www.anthropic.com/claude)
-   Game: Pokémon Red © Nintendo/Game Freak
