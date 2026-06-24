"""
ui/tutorial.py
Interactive step-by-step chess tutorial with 10 lessons.
"""

import pygame
import math
from core.board import BoardState
from core.rules import load_tutorial_position
from ui.renderer import Renderer
from utils.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, SQUARE_SIZE,
    BOARD_OFFSET_X, BOARD_OFFSET_Y,
    BG_COLOR, PANEL_COLOR, PANEL_BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT, TEXT_GOLD,
    BTN_PRIMARY, BTN_PRIMARY_HOVER, BTN_SECONDARY, BTN_SECONDARY_HOVER,
    WHITE, BLACK,
)

# ── Lesson definitions ────────────────────────────────────────────────────────

LESSONS = [
    {
        "id":        1,
        "title":     "The Chess Board",
        "position":  "start",
        "highlights":[],
        "text": [
            "Welcome to Chess! The board has 64 squares (8×8).",
            "Light squares and dark squares alternate in a checkerboard pattern.",
            "Files (columns) are labeled a–h. Ranks (rows) are numbered 1–8.",
            "Each player starts with 16 pieces on ranks 1-2 (White) and 7-8 (Black).",
        ],
        "hint": "Look at the starting position. White pieces are at the bottom.",
    },
    {
        "id":        2,
        "title":     "The Pawn ♙",
        "position":  "start",
        "highlights": [(6,0),(6,1),(6,2),(6,3),(6,4),(6,5),(6,6),(6,7)],
        "text": [
            "Pawns move FORWARD only — they can never go backwards.",
            "On their first move, a pawn can move 1 OR 2 squares forward.",
            "After that, only 1 square forward per move.",
            "Pawns CAPTURE diagonally — one square forward-left or forward-right.",
            "If a pawn reaches the other end of the board, it PROMOTES to any piece!",
        ],
        "hint": "The highlighted squares show White's pawns. They move upward.",
    },
    {
        "id":        3,
        "title":     "The Rook ♖",
        "position":  "castling_available",
        "highlights": [(7,0),(7,7)],
        "text": [
            "The Rook moves any number of squares horizontally OR vertically.",
            "It cannot jump over other pieces.",
            "Rooks are powerful in open files (no pawns blocking).",
            "Two rooks working together (doubled rooks) are very strong!",
            "Value: approximately 5 points.",
        ],
        "hint": "The Rooks are in the corners. They control entire rows and columns.",
    },
    {
        "id":        4,
        "title":     "The Knight ♘",
        "position":  "start",
        "highlights": [(7,1),(7,6)],
        "text": [
            "The Knight moves in an 'L' shape: 2 squares in one direction, then 1 square perpendicular.",
            "Knights are the ONLY pieces that can JUMP OVER other pieces!",
            "A knight always lands on the opposite color square from where it started.",
            "Knights are tricky — their movement is unique and hard to predict.",
            "Value: approximately 3 points.",
        ],
        "hint": "Knights start on b1 and g1 for White. They jump in L-shapes!",
    },
    {
        "id":        5,
        "title":     "The Bishop ♗",
        "position":  "start",
        "highlights": [(7,2),(7,5)],
        "text": [
            "The Bishop moves any number of squares DIAGONALLY.",
            "Each player has two Bishops — one on light squares, one on dark squares.",
            "A Bishop always stays on the same color throughout the game.",
            "Bishops are powerful when diagonals are open (few pawns blocking).",
            "Value: approximately 3 points.",
        ],
        "hint": "Bishops start on c1 and f1. They control long diagonal highways.",
    },
    {
        "id":        6,
        "title":     "The Queen ♕",
        "position":  "start",
        "highlights": [(7,3)],
        "text": [
            "The Queen is the most POWERFUL piece on the board!",
            "She combines the Rook and Bishop: moves any number of squares",
            "horizontally, vertically, OR diagonally.",
            "Keep the Queen safe — losing her is a huge disadvantage.",
            "Value: approximately 9 points.",
        ],
        "hint": "The Queen starts on d1 (White) and d8 (Black).",
    },
    {
        "id":        7,
        "title":     "The King ♔",
        "position":  "start",
        "highlights": [(7,4)],
        "text": [
            "The King is the most IMPORTANT piece — protect it at all costs!",
            "The King moves one square in any direction (horizontal, vertical, or diagonal).",
            "When your King is attacked, that's CHECK — you must escape immediately.",
            "If you cannot escape check, that's CHECKMATE — game over!",
            "You can never move your King into check.",
        ],
        "hint": "The King starts on e1 (White). Never let it get trapped!",
    },
    {
        "id":        8,
        "title":     "Special Move: Castling",
        "position":  "castling_available",
        "highlights": [(7,4),(7,0),(7,7)],
        "text": [
            "Castling is a special move to protect your King.",
            "The King slides 2 squares toward a Rook, and the Rook jumps to the other side.",
            "Requirements: King and Rook must not have moved, no pieces between them,",
            "King cannot be in check or pass through an attacked square.",
            "Castle EARLY — it gets your King to safety and activates your Rook!",
        ],
        "hint": "In this position, both sides can castle kingside or queenside.",
    },
    {
        "id":        9,
        "title":     "Special Move: En Passant",
        "position":  "en_passant",
        "highlights": [(3,4),(2,3)],
        "text": [
            "En passant is French for 'in passing' — a special pawn capture.",
            "It can ONLY happen immediately after an opponent's pawn moves 2 squares",
            "and lands beside your pawn.",
            "You can capture it AS IF it had only moved 1 square.",
            "This opportunity lasts for ONE move only — use it or lose it!",
        ],
        "hint": "White's e-pawn can capture the d-pawn 'en passant' right now!",
    },
    {
        "id":       10,
        "title":    "Checkmate & Winning",
        "position": "checkmate_in_1",
        "highlights": [(0,4)],
        "text": [
            "The goal of chess is CHECKMATE — trapping your opponent's King.",
            "Checkmate means the King is in check AND has no legal escape.",
            "In this position, White can deliver checkmate in 1 move!",
            "Think: Which piece can give check with no escape for the King?",
            "Hint: Move the Rook to e8 — that's checkmate! Re8#",
        ],
        "hint": "Try to find White's checkmate in 1 move! (Rook to e8)",
    },
]


class TutorialScreen:
    """Runs the interactive tutorial."""

    def __init__(self, surface: pygame.Surface):
        self.surface   = surface
        self.renderer  = Renderer(surface)
        self.board     = BoardState()
        self.lesson_idx = 0
        self._tick     = 0
        self._load_lesson()
        self._setup_fonts()
        self._setup_buttons()
        self.selected_rc    = None
        self.legal_targets  = []

    def _setup_fonts(self):
        self.font_title  = pygame.font.SysFont("arial", 22, bold=True)
        self.font_body   = pygame.font.SysFont("arial", 14)
        self.font_small  = pygame.font.SysFont("arial", 12)
        self.font_hint   = pygame.font.SysFont("arial", 13)
        self.font_num    = pygame.font.SysFont("arial", 36, bold=True)

    def _setup_buttons(self):
        bw, bh = 140, 42
        panel_x = BOARD_OFFSET_X + SQUARE_SIZE * 8 + 20
        panel_right = WINDOW_WIDTH - 20
        cy = WINDOW_HEIGHT - 60
        self.btn_prev = _TutBtn(pygame.Rect(panel_x, cy, bw, bh), "← Previous",
                                 self.font_body)
        self.btn_next = _TutBtn(pygame.Rect(panel_right - bw, cy, bw, bh), "Next →",
                                 self.font_body, accent=True)
        self.btn_menu = _TutBtn(pygame.Rect(panel_x, BOARD_OFFSET_Y - 50, bw, bh),
                                 "← Main Menu", self.font_body)

    def _load_lesson(self):
        lesson = LESSONS[self.lesson_idx]
        load_tutorial_position(self.board, lesson["position"])
        self.selected_rc   = None
        self.legal_targets = []

    # ── Per-frame ─────────────────────────────────────────────────────────────

    def update(self):
        self._tick += 1

    def draw(self):
        lesson = LESSONS[self.lesson_idx]
        self.surface.fill(BG_COLOR)

        # Board
        last_rcs = []
        check_rc = None
        if self.board.is_check:
            check_rc = self.board.king_square(self.board.turn)

        self.renderer.draw_board(
            selected_rc    = self.selected_rc,
            legal_targets  = self.legal_targets,
            last_move_rcs  = last_rcs,
            check_king_rc  = check_rc,
        )
        # Lesson highlights (pulsing)
        for (r, c) in lesson["highlights"]:
            alpha = int(80 + 60 * math.sin(self._tick * 0.08))
            x = BOARD_OFFSET_X + c * SQUARE_SIZE
            y = BOARD_OFFSET_Y + r * SQUARE_SIZE
            surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            surf.fill((99, 202, 183, alpha))
            self.surface.blit(surf, (x, y))

        self.renderer.draw_pieces(self.board.get_all_pieces(),
                                   legal_targets=self.legal_targets)

        # Side panel
        self._draw_panel(lesson)
        # Buttons
        mouse = pygame.mouse.get_pos()
        self.btn_prev.update(mouse); self.btn_prev.draw(self.surface)
        self.btn_next.update(mouse); self.btn_next.draw(self.surface)
        self.btn_menu.update(mouse); self.btn_menu.draw(self.surface)

        # Progress bar
        self._draw_progress()

    def _draw_panel(self, lesson: dict):
        px = BOARD_OFFSET_X + SQUARE_SIZE * 8 + 20
        pw = WINDOW_WIDTH - px - 20
        ph = BOARD_OFFSET_Y + SQUARE_SIZE * 8 - BOARD_OFFSET_Y
        panel = pygame.Rect(px, BOARD_OFFSET_Y, pw, ph)
        pygame.draw.rect(self.surface, PANEL_COLOR, panel, border_radius=12)
        pygame.draw.rect(self.surface, PANEL_BORDER, panel, 1, border_radius=12)

        y  = BOARD_OFFSET_Y + 16
        x  = px + 14

        # Lesson number badge
        num_txt = self.font_num.render(str(lesson["id"]), True, TEXT_ACCENT)
        self.surface.blit(num_txt, (x, y)); y += 44

        # Title
        title = self.font_title.render(lesson["title"], True, TEXT_PRIMARY)
        self.surface.blit(title, (x, y)); y += 30

        pygame.draw.line(self.surface, PANEL_BORDER,
                         (x, y), (px + pw - 14, y)); y += 10

        # Body text
        for line in lesson["text"]:
            # Word wrap
            words = line.split()
            current_line = ""
            for word in words:
                test = current_line + (" " if current_line else "") + word
                if self.font_body.size(test)[0] > pw - 28:
                    rendered = self.font_body.render(current_line, True, TEXT_SECONDARY)
                    self.surface.blit(rendered, (x, y)); y += 18
                    current_line = word
                else:
                    current_line = test
            if current_line:
                rendered = self.font_body.render(current_line, True, TEXT_SECONDARY)
                self.surface.blit(rendered, (x, y)); y += 22

        y += 10
        pygame.draw.line(self.surface, PANEL_BORDER,
                         (x, y), (px + pw - 14, y)); y += 10

        # Hint
        hint_lbl = self.font_small.render("💡 Tip:", True, TEXT_GOLD)
        self.surface.blit(hint_lbl, (x, y)); y += 18
        hint = self.font_hint.render(lesson["hint"], True, TEXT_GOLD)
        # Basic wrap
        words = lesson["hint"].split()
        cl = ""
        for w in words:
            t = cl + (" " if cl else "") + w
            if self.font_hint.size(t)[0] > pw - 28:
                r = self.font_hint.render(cl, True, TEXT_GOLD)
                self.surface.blit(r, (x, y)); y += 17
                cl = w
            else:
                cl = t
        if cl:
            r = self.font_hint.render(cl, True, TEXT_GOLD)
            self.surface.blit(r, (x, y))

    def _draw_progress(self):
        total  = len(LESSONS)
        bar_w  = BOARD_OFFSET_X + SQUARE_SIZE * 8
        bar_h  = 6
        bar_y  = BOARD_OFFSET_Y + SQUARE_SIZE * 8 + 20
        # Background
        pygame.draw.rect(self.surface, PANEL_BORDER,
                         (BOARD_OFFSET_X, bar_y, bar_w, bar_h), border_radius=3)
        # Fill
        fill_w = int(bar_w * (self.lesson_idx + 1) / total)
        pygame.draw.rect(self.surface, TEXT_ACCENT,
                         (BOARD_OFFSET_X, bar_y, fill_w, bar_h), border_radius=3)
        # Label
        lbl = self.font_small.render(
            f"Lesson {self.lesson_idx+1} of {total}", True, TEXT_SECONDARY)
        self.surface.blit(lbl, (BOARD_OFFSET_X, bar_y + 10))

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event) -> str | None:
        """Returns 'menu' or None."""
        if self.btn_menu.handle_click(event):
            return "menu"
        if self.btn_next.handle_click(event):
            if self.lesson_idx < len(LESSONS) - 1:
                self.lesson_idx += 1
                self._load_lesson()
            else:
                return "menu"
        if self.btn_prev.handle_click(event):
            if self.lesson_idx > 0:
                self.lesson_idx -= 1
                self._load_lesson()

        # Allow interacting with the board
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rc = Renderer.pixel_to_rc(event.pos)
            if rc:
                self._handle_board_click(rc)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                if self.lesson_idx < len(LESSONS) - 1:
                    self.lesson_idx += 1
                    self._load_lesson()
            elif event.key == pygame.K_LEFT:
                if self.lesson_idx > 0:
                    self.lesson_idx -= 1
                    self._load_lesson()
            elif event.key == pygame.K_ESCAPE:
                return "menu"
        return None

    def _handle_board_click(self, rc: tuple):
        if self.selected_rc is None:
            piece = self.board.piece_at(*rc)
            if piece and piece["color"] == self.board.turn:
                self.selected_rc   = rc
                self.legal_targets = self.board.legal_moves_from(*rc)
        else:
            if rc in self.legal_targets:
                self.board.push_move(self.selected_rc, rc)
            self.selected_rc   = None
            self.legal_targets = []


class _TutBtn:
    """Minimal tutorial button."""
    def __init__(self, rect, label, font, accent=False):
        self.rect    = rect
        self.label   = label
        self.font    = font
        self.accent  = accent
        self._hover  = False

    def update(self, mouse):
        self._hover = self.rect.collidepoint(mouse)

    def draw(self, surface):
        c = BTN_PRIMARY_HOVER if self._hover and self.accent else \
            BTN_PRIMARY if self.accent else \
            BTN_SECONDARY_HOVER if self._hover else BTN_SECONDARY
        pygame.draw.rect(surface, c, self.rect, border_radius=8)
        pygame.draw.rect(surface, PANEL_BORDER, self.rect, 1, border_radius=8)
        if self.font:
            txt = self.font.render(self.label, True, TEXT_PRIMARY)
            surface.blit(txt, txt.get_rect(center=self.rect.center))

    def handle_click(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and self.rect.collidepoint(event.pos))
