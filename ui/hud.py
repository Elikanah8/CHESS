"""
ui/hud.py
Heads-Up Display — side panel with timer, move history, captured pieces, status.
"""

import pygame
import time
from utils.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, BOARD_OFFSET_X, BOARD_OFFSET_Y,
    SQUARE_SIZE, PANEL_COLOR, PANEL_BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT, TEXT_GOLD,
    BTN_DANGER, BTN_DANGER_HOVER, BTN_SECONDARY, BTN_SECONDARY_HOVER,
    WHITE, BLACK,
    PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING,
)

# Panel sits to the right of the board
PANEL_X = BOARD_OFFSET_X + SQUARE_SIZE * 8 + 20
PANEL_W = WINDOW_WIDTH - PANEL_X - 20
PANEL_Y = BOARD_OFFSET_Y
PANEL_H = SQUARE_SIZE * 8

# Piece unicode for captured display
_CAP_SYMBOL = {
    (WHITE, PAWN): "♙", (WHITE, KNIGHT): "♘", (WHITE, BISHOP): "♗",
    (WHITE, ROOK): "♖", (WHITE, QUEEN):  "♕", (WHITE, KING):   "♔",
    (BLACK, PAWN): "♟", (BLACK, KNIGHT): "♞", (BLACK, BISHOP): "♝",
    (BLACK, ROOK): "♜", (BLACK, QUEEN):  "♛", (BLACK, KING):   "♚",
}


class Button:
    """A simple, animated UI button."""

    def __init__(self, rect: pygame.Rect, label: str,
                 color=BTN_SECONDARY, hover_color=BTN_SECONDARY_HOVER,
                 text_color=TEXT_PRIMARY, font=None, border_radius=8):
        self.rect         = rect
        self.label        = label
        self.color        = color
        self.hover_color  = hover_color
        self.text_color   = text_color
        self.font         = font
        self.border_radius= border_radius
        self._hovered     = False

    def draw(self, surface: pygame.Surface):
        color = self.hover_color if self._hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, PANEL_BORDER, self.rect, 1, border_radius=self.border_radius)
        if self.font:
            txt = self.font.render(self.label, True, self.text_color)
            r   = txt.get_rect(center=self.rect.center)
            surface.blit(txt, r)

    def handle_event(self, event) -> bool:
        """Returns True if this button was clicked."""
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def update(self, mouse_pos):
        self._hovered = self.rect.collidepoint(mouse_pos)


class HUD:
    """Renders the side panel HUD."""

    def __init__(self, surface: pygame.Surface):
        self.surface     = surface
        self.start_time  = time.time()
        self.white_time  = 0.0
        self.black_time  = 0.0
        self._last_tick  = time.time()
        self.paused      = False

        self._init_fonts()
        self._init_buttons()

    def _init_fonts(self):
        self.font_title   = pygame.font.SysFont("arial", 18, bold=True)
        self.font_body    = pygame.font.SysFont("arial", 14)
        self.font_small   = pygame.font.SysFont("arial", 12)
        self.font_timer   = pygame.font.SysFont("arial", 28, bold=True)
        self.font_piece   = pygame.font.SysFont("segoeuisymbol", 16) or \
                            pygame.font.SysFont("arial", 16)

    def _init_buttons(self):
        bw, bh = PANEL_W - 10, 36
        bx = PANEL_X + 5
        self.btn_undo    = Button(pygame.Rect(bx, PANEL_Y + PANEL_H - 130, bw, bh),
                                  "⟵ Undo",  BTN_SECONDARY, BTN_SECONDARY_HOVER,
                                  font=self.font_body)
        self.btn_resign  = Button(pygame.Rect(bx, PANEL_Y + PANEL_H - 88,  bw, bh),
                                  "🏳 Resign", BTN_DANGER, BTN_DANGER_HOVER,
                                  font=self.font_body)
        self.btn_menu    = Button(pygame.Rect(bx, PANEL_Y + PANEL_H - 46,  bw, bh),
                                  "☰ Menu",   BTN_SECONDARY, BTN_SECONDARY_HOVER,
                                  font=self.font_body)
        self.buttons = [self.btn_undo, self.btn_resign, self.btn_menu]

    # ── Update ────────────────────────────────────────────────────────────────

    def tick(self, current_turn: str):
        """Call every frame to update the active player's clock."""
        if self.paused:
            self._last_tick = time.time()
            return
        now   = time.time()
        delta = now - self._last_tick
        self._last_tick = now
        if current_turn == WHITE:
            self.white_time += delta
        else:
            self.black_time += delta

    def reset(self):
        self.white_time = 0.0
        self.black_time = 0.0
        self._last_tick = time.time()
        self.paused     = False

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, current_turn: str, move_history_san: list,
             captured: dict, status_msg: str = "", player_color: str = WHITE,
             ai_thinking: bool = False, difficulty: str = ""):
        """Full HUD draw call."""
        # Panel background
        panel = pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
        pygame.draw.rect(self.surface, PANEL_COLOR, panel, border_radius=12)
        pygame.draw.rect(self.surface, PANEL_BORDER, panel, 1, border_radius=12)

        y = PANEL_Y + 14
        x = PANEL_X + 12

        # ── Title ──────────────────────────────────────────────────────────
        title = self.font_title.render("♟  CHESS", True, TEXT_ACCENT)
        self.surface.blit(title, (x, y));  y += 28

        if difficulty:
            diff_txt = self.font_small.render(f"AI: {difficulty.upper()}", True, TEXT_SECONDARY)
            self.surface.blit(diff_txt, (x, y));  y += 20

        pygame.draw.line(self.surface, PANEL_BORDER, (x, y), (PANEL_X + PANEL_W - 12, y)); y += 10

        # ── Timers ─────────────────────────────────────────────────────────
        self._draw_timer("Black", self.black_time,
                         current_turn == BLACK, x, y)
        y += 50

        # ── Move history ───────────────────────────────────────────────────
        pygame.draw.line(self.surface, PANEL_BORDER, (x, y), (PANEL_X + PANEL_W - 12, y)); y += 8
        hist_label = self.font_small.render("Move History", True, TEXT_SECONDARY)
        self.surface.blit(hist_label, (x, y));  y += 18

        # Show last 12 half-moves
        moves_to_show = move_history_san[-20:]
        for i in range(0, len(moves_to_show), 2):
            move_num = (len(move_history_san) - len(moves_to_show) + i) // 2 + 1
            w_move   = moves_to_show[i]
            b_move   = moves_to_show[i + 1] if i + 1 < len(moves_to_show) else ""
            line     = f"{move_num:>2}. {w_move:<8} {b_move}"
            color    = TEXT_PRIMARY if i >= len(moves_to_show) - 2 else TEXT_SECONDARY
            rendered = self.font_small.render(line, True, color)
            self.surface.blit(rendered, (x, y))
            y += 16
            if y > PANEL_Y + PANEL_H - 230:
                break

        # ── Captured pieces ────────────────────────────────────────────────
        pygame.draw.line(self.surface, PANEL_BORDER, (x, y), (PANEL_X + PANEL_W - 12, y)); y += 8
        cap_label = self.font_small.render("Captured", True, TEXT_SECONDARY)
        self.surface.blit(cap_label, (x, y)); y += 16

        # White captured (black pieces taken)
        w_caps = captured.get(WHITE, [])
        b_caps = captured.get(BLACK, [])
        self._draw_captured_row(w_caps, BLACK, x, y); y += 22
        self._draw_captured_row(b_caps, WHITE, x, y); y += 22

        # ── Status / AI thinking ───────────────────────────────────────────
        if ai_thinking:
            txt = self.font_body.render("🤖 AI is thinking...", True, TEXT_GOLD)
            self.surface.blit(txt, (x, y)); y += 24
        elif status_msg:
            col = TEXT_ACCENT if "check" in status_msg.lower() else TEXT_PRIMARY
            txt = self.font_body.render(status_msg, True, col)
            self.surface.blit(txt, (x, y)); y += 24

        # ── White timer (bottom) ───────────────────────────────────────────
        pygame.draw.line(self.surface, PANEL_BORDER,
                         (x, PANEL_Y + PANEL_H - 175),
                         (PANEL_X + PANEL_W - 12, PANEL_Y + PANEL_H - 175))
        self._draw_timer("White", self.white_time,
                         current_turn == WHITE, x, PANEL_Y + PANEL_H - 168)

        # ── Buttons ────────────────────────────────────────────────────────
        mouse = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update(mouse)
            btn.draw(self.surface)

    def _draw_timer(self, label: str, seconds: float, active: bool, x: int, y: int):
        color = TEXT_GOLD if active else TEXT_SECONDARY
        mins  = int(seconds) // 60
        secs  = int(seconds) % 60
        timer_str = f"{mins:02}:{secs:02}"
        lbl   = self.font_small.render(label, True, TEXT_SECONDARY)
        timer = self.font_timer.render(timer_str, True, color)
        # Active indicator
        if active:
            ind_rect = pygame.Rect(PANEL_X + 5, y - 2, 4, 42)
            pygame.draw.rect(self.surface, TEXT_ACCENT, ind_rect, border_radius=2)
        self.surface.blit(lbl,  (x + 8, y))
        self.surface.blit(timer,(x + 8, y + 14))

    def _draw_captured_row(self, pieces: list, color: str, x: int, y: int):
        sym_x = x
        for p in pieces[:14]:
            sym = _CAP_SYMBOL.get((color, p), "")
            if sym:
                txt = self.font_piece.render(sym, True, TEXT_SECONDARY)
                self.surface.blit(txt, (sym_x, y))
                sym_x += 16

    def handle_event(self, event) -> str | None:
        """
        Returns 'undo', 'resign', 'menu', or None.
        """
        for btn, action in [(self.btn_undo, "undo"),
                            (self.btn_resign, "resign"),
                            (self.btn_menu, "menu")]:
            if btn.handle_event(event):
                return action
        return None
