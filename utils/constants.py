"""
utils/constants.py
Global constants for the Chess Game.
"""

import os

# ── Window ─────────────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 1200
WINDOW_HEIGHT = 800
FPS           = 60
WINDOW_TITLE  = "♟  Chess — by ElkanDev"

# ── Board ──────────────────────────────────────────────────────────────────────
BOARD_COLS     = 8
BOARD_ROWS     = 8
SQUARE_SIZE    = 80          # px per square  (8 × 80 = 640)
BOARD_OFFSET_X = 80          # left padding
BOARD_OFFSET_Y = 80          # top padding

# ── Colour Palette (Dark Premium Theme) ───────────────────────────────────────
# Background
BG_COLOR           = (15,  17,  26)     # near-black navy
PANEL_COLOR        = (24,  27,  40)     # dark slate for side panels
PANEL_BORDER       = (45,  50,  70)

# Board squares
LIGHT_SQUARE       = (235, 227, 209)    # warm ivory
DARK_SQUARE        = (115, 149, 82)     # classic green

# Highlights
HIGHLIGHT_SELECT   = (246, 246, 130, 180)   # yellow glow  (selection)
HIGHLIGHT_MOVE     = (106, 176, 76,  130)   # green dot    (legal move)
HIGHLIGHT_CAPTURE  = (220, 80,  60,  160)   # red glow     (capture target)
HIGHLIGHT_LASTMOVE = (205, 210, 106, 120)   # pale yellow  (last move)
HIGHLIGHT_CHECK    = (220, 50,  50,  180)   # red pulse    (king in check)

# Text / UI
TEXT_PRIMARY       = (230, 230, 245)
TEXT_SECONDARY     = (150, 155, 175)
TEXT_ACCENT        = (99,  202, 183)    # teal accent
TEXT_GOLD          = (255, 213, 100)

# Buttons
BTN_PRIMARY        = (99,  202, 183)
BTN_PRIMARY_HOVER  = (120, 220, 200)
BTN_SECONDARY      = (45,  50,  70)
BTN_SECONDARY_HOVER= (60,  66,  90)
BTN_DANGER         = (200, 70,  70)
BTN_DANGER_HOVER   = (220, 90,  90)

# ── Piece type codes (also used as dict keys) ─────────────────────────────────
PAWN   = "P"
KNIGHT = "N"
BISHOP = "B"
ROOK   = "R"
QUEEN  = "Q"
KING   = "K"

# ── Colour codes ──────────────────────────────────────────────────────────────
WHITE = "white"
BLACK = "black"

# ── AI Difficulty ─────────────────────────────────────────────────────────────
EASY   = "easy"
MEDIUM = "medium"
HARD   = "hard"

AI_DEPTH = {
    EASY:   2,
    MEDIUM: 3,
    HARD:   5,
}

AI_RANDOM_FACTOR = {
    EASY:   0.35,   # 35 % chance of picking a random legal move instead
    MEDIUM: 0.08,
    HARD:   0.00,
}

# ── Piece values (centipawns) ──────────────────────────────────────────────────
PIECE_VALUE = {
    PAWN:   100,
    KNIGHT: 320,
    BISHOP: 330,
    ROOK:   500,
    QUEEN:  900,
    KING:   20000,
}

# ── Asset paths ────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR    = os.path.join(BASE_DIR, "assets")
PIECES_DIR    = os.path.join(ASSETS_DIR, "pieces")
SOUNDS_DIR    = os.path.join(ASSETS_DIR, "sounds")
FONTS_DIR     = os.path.join(ASSETS_DIR, "fonts")

# ── Game states ────────────────────────────────────────────────────────────────
STATE_MENU        = "menu"
STATE_DIFFICULTY  = "difficulty"
STATE_COLOR_PICK  = "color_pick"
STATE_GAME_VS_AI  = "game_vs_ai"
STATE_GAME_LOCAL  = "game_local"       # Local 2-player (same machine)
STATE_MULTIPLAYER = "multiplayer"
STATE_TUTORIAL    = "tutorial"
STATE_GAME_OVER   = "game_over"

# ── Multiplayer ────────────────────────────────────────────────────────────────
MP_DEFAULT_HOST = "127.0.0.1"
MP_DEFAULT_PORT = 65432
MP_CODE_LENGTH  = 6
MP_BUFFER_SIZE  = 4096
