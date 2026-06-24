"""
ui/renderer.py
Renders the chess board, pieces, highlights, and animations using Pygame.
"""

import pygame
import chess
from utils.constants import (
    SQUARE_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y,
    LIGHT_SQUARE, DARK_SQUARE,
    HIGHLIGHT_SELECT, HIGHLIGHT_MOVE, HIGHLIGHT_CAPTURE,
    HIGHLIGHT_LASTMOVE, HIGHLIGHT_CHECK,
    WHITE, BLACK,
    PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING,
)

# ── Unicode chess symbols ──────────────────────────────────────────────────────
_UNICODE = {
    (WHITE, KING):   "♔",
    (WHITE, QUEEN):  "♕",
    (WHITE, ROOK):   "♖",
    (WHITE, BISHOP): "♗",
    (WHITE, KNIGHT): "♘",
    (WHITE, PAWN):   "♙",
    (BLACK, KING):   "♚",
    (BLACK, QUEEN):  "♛",
    (BLACK, ROOK):   "♜",
    (BLACK, BISHOP): "♝",
    (BLACK, KNIGHT): "♞",
    (BLACK, PAWN):   "♟",
}

_FALLBACK = {
    KING: "K", QUEEN: "Q", ROOK: "R",
    BISHOP: "B", KNIGHT: "N", PAWN: "P",
}

# Piece colors
_PIECE_COLOR   = {WHITE: (255, 255, 255), BLACK: (30, 30, 30)}
_PIECE_OUTLINE = {WHITE: (50,  50,  50),  BLACK: (200, 200, 200)}


class Renderer:
    """Handles all board and piece drawing."""

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self._piece_font   = None
        self._label_font   = None
        self._overlay_surf = pygame.Surface(
            (SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA
        )
        self._load_fonts()

        # Animation state
        self.anim_piece  = None   # dict: {type, color, from_rc, to_rc, progress}
        self.anim_speed  = 0.12   # 0..1 per frame

    # ── Font loading ──────────────────────────────────────────────────────────

    def _load_fonts(self):
        """Try to load a Unicode-capable font for chess symbols."""
        candidates = [
            "segoeuisymbol", "seguisym", "arial unicode ms",
            "noto sans symbols", "dejavu sans",
        ]
        size = int(SQUARE_SIZE * 0.75)
        for name in candidates:
            try:
                f = pygame.font.SysFont(name, size, bold=False)
                # Test that it can render a chess symbol
                surf = f.render("♔", True, (0, 0, 0))
                if surf.get_width() > 4:
                    self._piece_font = f
                    break
            except Exception:
                continue

        if self._piece_font is None:
            self._piece_font = pygame.font.SysFont("arial", size, bold=True)

        self._label_font = pygame.font.SysFont("arial", 14, bold=False)

    # ── Board drawing ─────────────────────────────────────────────────────────

    def draw_board(self, selected_rc=None, legal_targets=None,
                   last_move_rcs=None, check_king_rc=None,
                   flipped: bool = False):
        """
        Draw the 8×8 board with highlights.
        `flipped=True` renders from Black's perspective.
        """
        legal_targets  = legal_targets  or []
        last_move_rcs  = last_move_rcs  or []

        for row in range(8):
            for col in range(8):
                display_row = (7 - row) if flipped else row
                display_col = (7 - col) if flipped else col

                x = BOARD_OFFSET_X + display_col * SQUARE_SIZE
                y = BOARD_OFFSET_Y + display_row * SQUARE_SIZE

                # Base square colour
                is_light = (row + col) % 2 == 0
                sq_color = LIGHT_SQUARE if is_light else DARK_SQUARE
                pygame.draw.rect(self.surface, sq_color,
                                 (x, y, SQUARE_SIZE, SQUARE_SIZE))

                # Last-move highlight
                if (row, col) in last_move_rcs:
                    self._draw_overlay(x, y, HIGHLIGHT_LASTMOVE)

                # Selected piece highlight
                if selected_rc == (row, col):
                    self._draw_overlay(x, y, HIGHLIGHT_SELECT)

                # Check highlight
                if check_king_rc == (row, col):
                    self._draw_overlay(x, y, HIGHLIGHT_CHECK)

                # Legal move dots / capture rings
                if (row, col) in legal_targets:
                    self._draw_move_hint(x, y, col, row)

        # Rank and file labels
        self._draw_labels(flipped)

        # Board border
        board_rect = pygame.Rect(
            BOARD_OFFSET_X, BOARD_OFFSET_Y,
            SQUARE_SIZE * 8, SQUARE_SIZE * 8
        )
        pygame.draw.rect(self.surface, (80, 90, 110), board_rect, 2)

    def _draw_overlay(self, x, y, color):
        self._overlay_surf.fill((0, 0, 0, 0))
        pygame.draw.rect(self._overlay_surf, color,
                         (0, 0, SQUARE_SIZE, SQUARE_SIZE))
        self.surface.blit(self._overlay_surf, (x, y))

    def _draw_move_hint(self, x, y, col, row):
        """Green dot for empty squares, ring for capture squares."""
        cx = x + SQUARE_SIZE // 2
        cy = y + SQUARE_SIZE // 2
        r  = SQUARE_SIZE // 6
        # We'll decide dot vs ring in draw_pieces; here just draw dot
        surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(surf, (0, 180, 80, 140), (SQUARE_SIZE//2, SQUARE_SIZE//2), r)
        self.surface.blit(surf, (x, y))

    def draw_capture_hint(self, row, col, flipped=False):
        """Draw a capture ring on a target square (call after draw_pieces)."""
        display_row = (7 - row) if flipped else row
        display_col = (7 - col) if flipped else col
        x = BOARD_OFFSET_X + display_col * SQUARE_SIZE
        y = BOARD_OFFSET_Y + display_row * SQUARE_SIZE
        surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(surf, (220, 60, 60, 160),
                           (SQUARE_SIZE//2, SQUARE_SIZE//2),
                           SQUARE_SIZE//2 - 4, 6)
        self.surface.blit(surf, (x, y))

    def _draw_labels(self, flipped: bool):
        files = "abcdefgh"
        ranks = "12345678"
        for i in range(8):
            # File labels (bottom)
            f_idx = (7 - i) if flipped else i
            label = self._label_font.render(files[f_idx], True, (180, 180, 180))
            self.surface.blit(label, (
                BOARD_OFFSET_X + i * SQUARE_SIZE + SQUARE_SIZE - 14,
                BOARD_OFFSET_Y + 8 * SQUARE_SIZE + 4
            ))
            # Rank labels (left)
            r_idx = i if flipped else (7 - i)
            label = self._label_font.render(ranks[r_idx], True, (180, 180, 180))
            self.surface.blit(label, (
                BOARD_OFFSET_X - 18,
                BOARD_OFFSET_Y + i * SQUARE_SIZE + 4
            ))

    # ── Piece drawing ─────────────────────────────────────────────────────────

    def draw_pieces(self, pieces: list[dict], flipped: bool = False,
                    skip_rc=None, legal_targets=None, board_state=None):
        """
        Draw all pieces. `skip_rc` is the square to skip (dragged piece).
        `legal_targets` used to draw capture rings instead of dots on occupied squares.
        """
        legal_targets = legal_targets or []

        for p in pieces:
            row, col = p["row"], p["col"]
            if skip_rc == (row, col):
                continue

            # Draw capture ring if this is a legal capture target
            if (row, col) in legal_targets:
                display_row = (7 - row) if flipped else row
                display_col = (7 - col) if flipped else col
                x = BOARD_OFFSET_X + display_col * SQUARE_SIZE
                y = BOARD_OFFSET_Y + display_row * SQUARE_SIZE
                surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(surf, (220, 60, 60, 150),
                                   (SQUARE_SIZE//2, SQUARE_SIZE//2),
                                   SQUARE_SIZE//2 - 3, 7)
                self.surface.blit(surf, (x, y))

            display_row = (7 - row) if flipped else row
            display_col = (7 - col) if flipped else col
            x = BOARD_OFFSET_X + display_col * SQUARE_SIZE
            y = BOARD_OFFSET_Y + display_row * SQUARE_SIZE
            self._draw_piece(x, y, p["type"], p["color"])

    def _draw_piece(self, x: int, y: int, piece_type: str, color: str):
        """Draw a single piece centered on its square."""
        symbol   = _UNICODE.get((color, piece_type))
        fg_color = _PIECE_COLOR[color]
        outline  = _PIECE_OUTLINE[color]

        cx = x + SQUARE_SIZE // 2
        cy = y + SQUARE_SIZE // 2

        if symbol:
            # Shadow
            sh = self._piece_font.render(symbol, True, (0, 0, 0, 180))
            sr = sh.get_rect(center=(cx + 2, cy + 2))
            self.surface.blit(sh, sr)
            # Outline pass (draw slightly offset in 4 directions)
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                out = self._piece_font.render(symbol, True, outline)
                r   = out.get_rect(center=(cx + dx, cy + dy))
                self.surface.blit(out, r)
            # Main piece
            main = self._piece_font.render(symbol, True, fg_color)
            mr   = main.get_rect(center=(cx, cy))
            self.surface.blit(main, mr)
        else:
            # Fallback: draw a circle with letter
            rad = SQUARE_SIZE // 2 - 6
            pygame.draw.circle(self.surface, fg_color, (cx, cy), rad)
            pygame.draw.circle(self.surface, outline, (cx, cy), rad, 2)
            letter = self._label_font.render(_FALLBACK[piece_type], True, outline)
            lr = letter.get_rect(center=(cx, cy))
            self.surface.blit(letter, lr)

    def draw_dragged_piece(self, pos: tuple, piece_type: str, color: str):
        """Draw a piece being dragged at the mouse position."""
        x = pos[0] - SQUARE_SIZE // 2
        y = pos[1] - SQUARE_SIZE // 2
        self._draw_piece(x, y, piece_type, color)

    # ── Coordinate helpers ────────────────────────────────────────────────────

    @staticmethod
    def pixel_to_rc(pos: tuple, flipped: bool = False) -> tuple[int, int] | None:
        """Convert mouse pixel position to (row, col), or None if outside board."""
        px, py = pos
        col = (px - BOARD_OFFSET_X) // SQUARE_SIZE
        row = (py - BOARD_OFFSET_Y) // SQUARE_SIZE
        if not (0 <= row < 8 and 0 <= col < 8):
            return None
        if flipped:
            return (7 - row, 7 - col)
        return (row, col)

    @staticmethod
    def rc_to_pixel(row: int, col: int, flipped: bool = False) -> tuple[int, int]:
        """Top-left pixel of a square."""
        if flipped:
            row, col = 7 - row, 7 - col
        return (BOARD_OFFSET_X + col * SQUARE_SIZE,
                BOARD_OFFSET_Y + row * SQUARE_SIZE)
