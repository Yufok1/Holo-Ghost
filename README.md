# 👻 HOLO-GHOST

**The Digital Holy Ghost - System-Agnostic Input Observer & Intelligence Layer**

> "I see what you do. I remember what you did. I understand what it means."

---

## 🌟 What Is This?

HOLO-GHOST is a **providential observation system** - it watches the flow of human-computer interaction, understands context, identifies patterns, and remembers everything in an immutable chain.

Not just anti-cheat. Not just analytics. Not just AI. **All of it, and more.**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   👁️  INPUT OBSERVER                                            │
│       ├── Mouse: position, velocity, acceleration, clicks       │
│       ├── Keyboard: keys, timing, patterns                      │
│       └── Context: active window, game state                    │
│                                                                 │
│   🧠  LLM CORE (Mistral Nemo 12B)                               │
│       ├── Pattern recognition                                   │
│       ├── Anomaly detection                                     │
│       └── Natural language insights                             │
│                                                                 │
│   ⛓️   PROVENANCE CHAIN                                          │
│       ├── Merkle-chained events                                 │
│       ├── Session receipts                                      │
│       └── Verifiable history                                    │
│                                                                 │
│   🎬  CLIP RECORDER                                             │
│       ├── Screen capture on flag                                │
│       ├── Input replay data                                     │
│       └── Evidence packaging                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Use Cases (Many Birds, One Stone)

| Use Case | How HOLO-GHOST Helps |
|----------|---------------------|
| **Anti-Cheat** | Detects inhuman input patterns, aimbots, macros |
| **Skill Analysis** | Understands player improvement over time |
| **Accessibility** | Identifies input struggles, suggests adaptations |
| **Content Creation** | Auto-clips highlight moments |
| **Training Data** | Generates labeled input datasets |
| **Session Journals** | Natural language summaries of play sessions |
| **Dispute Resolution** | Verifiable receipts with merkle proofs |
| **Research** | Human-computer interaction studies |

---

## 🏗️ Architecture

```
holo_ghost/
├── core/
│   ├── __init__.py
│   ├── ghost.py           # Main Ghost orchestrator
│   ├── config.py          # Configuration management
│   └── events.py          # Event system (pub/sub)
│
├── input/
│   ├── __init__.py
│   ├── observer.py        # Low-level input hooks
│   ├── mouse.py           # Mouse state & metrics
│   ├── keyboard.py        # Keyboard state & metrics
│   └── patterns.py        # Input pattern detection
│
├── game/
│   ├── __init__.py
│   ├── detector.py        # Active game detection
│   ├── bridge.py          # Game-specific integrations
│   └── registry.py        # Known games database
│
├── provenance/
│   ├── __init__.py
│   ├── chain.py           # Merkle chain implementation
│   ├── receipts.py        # Session receipts
│   └── verify.py          # Verification utilities
│
├── llm/
│   ├── __init__.py
│   ├── engine.py          # LLM interface (vLLM/local)
│   ├── prompts.py         # System prompts
│   └── analysis.py        # Pattern analysis via LLM
│
├── recorder/
│   ├── __init__.py
│   ├── screen.py          # Screen capture
│   ├── inputs.py          # Input replay format
│   └── clips.py           # Clip management
│
├── api/
│   ├── __init__.py
│   ├── server.py          # REST/WebSocket API
│   └── routes.py          # API endpoints
│
├── ui/
│   ├── overlay.py         # In-game overlay (optional)
│   └── dashboard.html     # Web dashboard
│
├── main.py                # Entry point
├── requirements.txt
└── setup.py
```

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/glassboxgames/holo-ghost.git
cd holo-ghost

# Install
pip install -e .

# Run (background daemon)
holo-ghost start

# Run with overlay
holo-ghost start --overlay

# Check status
holo-ghost status
```

---

## ⚙️ Configuration

```yaml
# config.yaml
ghost:
  name: "HOLO-GHOST"
  
input:
  mouse:
    poll_rate: 1000  # Hz
    track_velocity: true
    track_acceleration: true
  keyboard:
    track_timing: true
    track_patterns: true

llm:
  engine: "vllm"  # or "local", "openai"
  model: "mistralai/Mistral-Nemo-Instruct-2407"
  url: "http://localhost:8000/v1"

provenance:
  enabled: true
  chain_file: "~/.holo_ghost/chain.db"

recorder:
  enabled: true
  format: "mp4"
  quality: "high"
  pre_buffer: 30  # seconds before flag
  post_buffer: 10  # seconds after flag

games:
  auto_detect: true
  known_games:
    - "valorant.exe"
    - "cs2.exe"
    - "overwatch.exe"
    # ... etc
```

---

## 🔌 Integration APIs

### Python SDK

```python
from holo_ghost import Ghost

# Connect to running daemon
ghost = Ghost.connect()

# Get current session
session = ghost.current_session

# Query recent inputs
inputs = ghost.query_inputs(
    last_seconds=60,
    include_mouse=True,
    include_keyboard=True
)

# Ask the Ghost
response = ghost.ask("What patterns do you see in my aim?")

# Flag a moment
ghost.flag("suspicious_snap", confidence=0.85)

# Get session receipt
receipt = ghost.get_receipt()
```

### WebSocket API

```javascript
const ws = new WebSocket('ws://localhost:7777/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'input_event') {
        // Real-time input stream
    } else if (data.type === 'flag') {
        // Ghost flagged something
    } else if (data.type === 'insight') {
        // LLM generated insight
    }
};
```

---

## 👁️ The Ghost's Perception

The Ghost doesn't just see inputs - it **understands** them:

```
RAW INPUT:
  mouse_dx: 847, mouse_dy: -12, dt: 16ms, click: true

GHOST PERCEPTION:
  "Rapid horizontal snap (52,937°/s) followed by immediate click.
   Movement profile: linear acceleration, no micro-corrections.
   Context: CS2 active, player in combat.
   Confidence in human origin: 23%"
```

---

## ⛓️ Provenance Chain

Every observation is chained:

```
Block #1847392
├── Timestamp: 2026-01-14T15:42:31.847Z
├── Event: mouse_snap
├── Data: {dx: 847, dy: -12, dt: 16, click: true}
├── Context: {game: "cs2", map: "dust2", round: 12}
├── Analysis: "Inhuman snap velocity"
├── Previous Hash: 7f3a9c2b...
└── Block Hash: 4e8d1f7a...
```

Receipts are verifiable. History is immutable. The Ghost remembers.

---

## 🎬 Clip System

When the Ghost flags something, it captures:

```
clip_20260114_154231_suspicious_snap/
├── video.mp4          # Screen recording (30s pre, 10s post)
├── inputs.json        # Raw input replay data
├── analysis.json      # LLM analysis
├── chain_excerpt.json # Relevant merkle chain segment
└── receipt.json       # Verifiable receipt
```

---

## 🧠 LLM Integration

The Ghost's intelligence comes from Mistral Nemo 12B (or your choice):

```python
# The Ghost can answer questions about what it's seen
ghost.ask("How has my aim improved this week?")

# Generate session summaries
ghost.summarize_session()

# Analyze specific moments
ghost.analyze_clip("clip_20260114_154231")

# Compare patterns
ghost.compare("my_aim", "pro_player_dataset")
```

---

## 📜 License

MIT - Use it, extend it, make it your own.

---

## 🤝 Contributing

The Ghost welcomes all who seek to understand.

---

*"I am the observer. I am the chain. I am the Ghost between input and action."*
