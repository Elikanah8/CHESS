# ♟ Chess Game

A feature-rich Python chess game built with **Pygame** and **python-chess**.

## Features
- **vs Computer** — Easy / Medium / Hard AI (Minimax + Alpha-Beta Pruning)
-  **Learning Tutorial** — Interactive lessons for new players
-  **Online Multiplayer** — Play with a friend using a shared room code

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Project Structure

```
chess/
├── main.py              # Entry point
├── core/                # Chess engine (board, pieces, rules)
├── ai/                  # AI engine (Minimax, evaluation, difficulty)
├── ui/                  # Pygame UI (renderer, menu, HUD, tutorial)
├── multiplayer/         # Socket-based online multiplayer
├── utils/               # Constants and helpers
└── assets/              # Images, sounds, fonts
```

## Controls
- **Click** a piece to select it
- **Click** a highlighted square to move
- **R** — Resign | **U** — Undo | **ESC** — Back to menu

## Tech Stack
- Python 3.10+
- Pygame 2.5+
- python-chess 1.10+

---
Built step-by-step 🚀
