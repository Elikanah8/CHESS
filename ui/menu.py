"""
ui/menu.py
Main menu, mode selection, difficulty picker, color picker — all Pygame screens.
"""

import pygame
import math
from utils.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    BG_COLOR, PANEL_COLOR, PANEL_BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT, TEXT_GOLD,
    BTN_PRIMARY, BTN_PRIMARY_HOVER, BTN_SECONDARY, BTN_SECONDARY_HOVER,
    BTN_DANGER, BTN_DANGER_HOVER,
    WHITE, BLACK,
    EASY, MEDIUM, HARD,
    STATE_GAME_VS_AI, STATE_GAME_LOCAL, STATE_TUTORIAL,
    STATE_DIFFICULTY, STATE_COLOR_PICK, STATE_MULTIPLAYER,
)
from ai.difficulty import DIFFICULTY_LABELS, DIFFICULTY_DESCRIPTIONS


def _make_font(name, size, bold=False):
    return pygame.font.SysFont(name, size, bold=bold)


class MenuButton:
    """A polished menu button with hover animation."""

    def __init__(self, rect: pygame.Rect, label: str, subtitle: str = "",
                 color=BTN_SECONDARY, hover_color=BTN_SECONDARY_HOVER,
                 text_color=TEXT_PRIMARY, accent_color=TEXT_ACCENT,
                 font=None, sub_font=None, border_radius=12, icon=""):
        self.rect          = rect
        self.label         = label
        self.subtitle      = subtitle
        self.color         = color
        self.hover_color   = hover_color
        self.text_color    = text_color
        self.accent_color  = accent_color
        self.font          = font
        self.sub_font      = sub_font
        self.border_radius = border_radius
        self.icon          = icon
        self._hover        = False
        self._scale        = 1.0

    def update(self, mouse_pos):
        self._hover = self.rect.collidepoint(mouse_pos)
        target = 1.03 if self._hover else 1.0
        self._scale += (target - self._scale) * 0.2

    def draw(self, surface):
        color = self.hover_color if self._hover else self.color
        # Scale the rect for hover effect
        if self._scale != 1.0:
            w = int(self.rect.width  * self._scale)
            h = int(self.rect.height * self._scale)
            x = self.rect.centerx - w // 2
            y = self.rect.centery - h // 2
            r = pygame.Rect(x, y, w, h)
        else:
            r = self.rect

        pygame.draw.rect(surface, color, r, border_radius=self.border_radius)
        pygame.draw.rect(surface, self.accent_color if self._hover else PANEL_BORDER,
                         r, 1 if not self._hover else 2,
                         border_radius=self.border_radius)

        # Icon + label
        if self.font:
            full_label = f"{self.icon}  {self.label}" if self.icon else self.label
            txt = self.font.render(full_label, True,
                                   self.text_color if not self._hover else TEXT_GOLD)
            tr  = txt.get_rect(center=(r.centerx, r.centery - (8 if self.subtitle else 0)))
            surface.blit(txt, tr)

        # Subtitle
        if self.subtitle and self.sub_font:
            sub = self.sub_font.render(self.subtitle, True, TEXT_SECONDARY)
            sr  = sub.get_rect(center=(r.centerx, r.centery + 14))
            surface.blit(sub, sr)

    def is_clicked(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


class MenuScreen:
    """
    Manages all menu screens. Call `draw()` and `handle_event()` each frame.
    Returns a state string when a selection is made, or None to keep showing menu.
    """

    def __init__(self, surface: pygame.Surface):
        self.surface    = surface
        self.state      = "main"          # sub-state within menu
        self.difficulty = MEDIUM
        self.player_color = WHITE
        self._tick      = 0
        self._setup_fonts()
        self._build_main()
        self._build_difficulty()
        self._build_color_pick()

    def _setup_fonts(self):
        self.font_hero   = _make_font("arial", 72, bold=True)
        self.font_title  = _make_font("arial", 28, bold=True)
        self.font_btn    = _make_font("arial", 20, bold=True)
        self.font_sub    = _make_font("arial", 13)
        self.font_small  = _make_font("arial", 12)

    # ── Button builders ───────────────────────────────────────────────────────

    def _make_btn(self, x, y, w, h, label, subtitle="",
                  color=BTN_SECONDARY, hover=BTN_SECONDARY_HOVER,
                  icon="", accent=TEXT_ACCENT):
        return MenuButton(
            pygame.Rect(x, y, w, h), label, subtitle,
            color=color, hover_color=hover, text_color=TEXT_PRIMARY,
            accent_color=accent, font=self.font_btn, sub_font=self.font_sub,
            icon=icon,
        )

    def _build_main(self):
        cx = WINDOW_WIDTH // 2
        bw, bh, gap = 380, 64, 14
        y0 = 280

        self._main_buttons = [
            self._make_btn(cx - bw//2, y0,             bw, bh,
                           "Play vs Computer", "Challenge the AI",
                           color=(40,52,70), hover=(55,72,100),
                           icon="🤖", accent=TEXT_ACCENT),
            self._make_btn(cx - bw//2, y0 + (bh+gap),  bw, bh,
                           "Two Players", "Pass & play on same screen",
                           color=(40,52,70), hover=(55,72,100),
                           icon="👥"),
            self._make_btn(cx - bw//2, y0 + 2*(bh+gap),bw, bh,
                           "Online Multiplayer", "Play with a friend via code",
                           color=(40,52,70), hover=(55,72,100),
                           icon="🌐"),
            self._make_btn(cx - bw//2, y0 + 3*(bh+gap),bw, bh,
                           "Learn Chess", "Interactive tutorial for beginners",
                           color=(40,52,70), hover=(55,72,100),
                           icon="📚"),
            self._make_btn(cx - bw//2, y0 + 4*(bh+gap),bw, bh,
                           "Quit", "",
                           color=(60,30,30), hover=BTN_DANGER_HOVER,
                           icon="✖", accent=(220,80,80)),
        ]
        self._main_actions = [
            "vs_ai", "local", "multiplayer", "tutorial", "quit"
        ]

    def _build_difficulty(self):
        cx = WINDOW_WIDTH // 2
        bw, bh, gap = 380, 72, 12
        y0 = 220
        levels = [EASY, MEDIUM, HARD]
        colors = [
            ((30,70,40),(50,100,60)),
            ((70,60,20),(100,90,35)),
            ((70,25,25),(100,40,40)),
        ]
        self._diff_buttons = []
        for i, lvl in enumerate(levels):
            c, hc = colors[i]
            btn = MenuButton(
                pygame.Rect(cx - bw//2, y0 + i*(bh+gap), bw, bh),
                DIFFICULTY_LABELS[lvl],
                DIFFICULTY_DESCRIPTIONS[lvl],
                color=c, hover_color=hc,
                text_color=TEXT_PRIMARY, accent_color=TEXT_ACCENT,
                font=self.font_btn, sub_font=self.font_sub,
                border_radius=12,
            )
            self._diff_buttons.append((btn, lvl))

        self._diff_back = self._make_btn(cx - bw//2, y0 + 3*(bh+gap) + 10,
                                          bw, 46, "← Back")

    def _build_color_pick(self):
        cx = WINDOW_WIDTH // 2
        bw, bh, gap = 180, 72, 20
        y0 = 240

        self._color_buttons = [
            (self._make_btn(cx - bw - gap//2, y0, bw, bh,
                            "Play as White", "♔", color=(200,200,200),
                            hover=(230,230,230)), WHITE),
            (self._make_btn(cx + gap//2,       y0, bw, bh,
                            "Play as Black", "♚", color=(40,40,60),
                            hover=(60,60,90)), BLACK),
        ]
        self._color_back = self._make_btn(cx - bw//2, y0 + bh + 40, bw, 46, "← Back")

    # ── Per-frame update & draw ────────────────────────────────────────────────

    def update(self):
        self._tick += 1
        mouse = pygame.mouse.get_pos()
        if self.state == "main":
            for btn in self._main_buttons:
                btn.update(mouse)
        elif self.state == "difficulty":
            for btn, _ in self._diff_buttons:
                btn.update(mouse)
            self._diff_back.update(mouse)
        elif self.state == "color":
            for btn, _ in self._color_buttons:
                btn.update(mouse)
            self._color_back.update(mouse)

    def draw(self):
        self._draw_bg()
        if self.state == "main":
            self._draw_main()
        elif self.state == "difficulty":
            self._draw_difficulty()
        elif self.state == "color":
            self._draw_color()

    def _draw_bg(self):
        self.surface.fill(BG_COLOR)
        # Subtle animated grid pattern
        t = self._tick * 0.008
        for i in range(0, WINDOW_WIDTH, 60):
            alpha = int(12 + 6 * math.sin(t + i * 0.05))
            pygame.draw.line(self.surface, (*PANEL_BORDER[:3], alpha),
                             (i, 0), (i, WINDOW_HEIGHT))
        for j in range(0, WINDOW_HEIGHT, 60):
            alpha = int(12 + 6 * math.sin(t + j * 0.05))
            pygame.draw.line(self.surface, (*PANEL_BORDER[:3], alpha),
                             (0, j), (WINDOW_WIDTH, j))

    def _draw_main(self):
        cx = WINDOW_WIDTH // 2

        # Hero title
        t    = self._tick * 0.04
        glow = int(180 + 60 * math.sin(t))
        hero = self.font_hero.render("♟ CHESS", True, (glow, 210, 180))
        self.surface.blit(hero, hero.get_rect(centerx=cx, y=80))

        sub = self.font_sub.render(
            "Play · Learn · Compete", True, TEXT_SECONDARY)
        self.surface.blit(sub, sub.get_rect(centerx=cx, y=175))

        # Decorative line
        pygame.draw.line(self.surface, TEXT_ACCENT,
                         (cx - 120, 210), (cx + 120, 210), 1)

        for btn in self._main_buttons:
            btn.draw(self.surface)

        ver = self.font_small.render("v1.0  |  Python + Pygame", True, (60,65,80))
        self.surface.blit(ver, ver.get_rect(centerx=cx, y=WINDOW_HEIGHT - 24))

    def _draw_difficulty(self):
        cx = WINDOW_WIDTH // 2
        title = self.font_title.render("Select Difficulty", True, TEXT_ACCENT)
        self.surface.blit(title, title.get_rect(centerx=cx, y=130))
        sub = self.font_sub.render("How tough do you want the AI to be?", True, TEXT_SECONDARY)
        self.surface.blit(sub, sub.get_rect(centerx=cx, y=170))
        for btn, _ in self._diff_buttons:
            btn.draw(self.surface)
        self._diff_back.draw(self.surface)

    def _draw_color(self):
        cx = WINDOW_WIDTH // 2
        title = self.font_title.render("Choose Your Side", True, TEXT_ACCENT)
        self.surface.blit(title, title.get_rect(centerx=cx, y=130))
        sub = self.font_sub.render("Which color do you want to play?", True, TEXT_SECONDARY)
        self.surface.blit(sub, sub.get_rect(centerx=cx, y=170))
        for btn, _ in self._color_buttons:
            btn.draw(self.surface)
        self._color_back.draw(self.surface)

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event) -> tuple[str | None, dict]:
        """
        Returns (next_game_state, params) or (None, {}) to stay in menu.
        next_game_state is one of the STATE_* constants.
        params may contain 'difficulty', 'player_color'.
        """
        if self.state == "main":
            for btn, action in zip(self._main_buttons, self._main_actions):
                if btn.is_clicked(event):
                    if action == "vs_ai":
                        self.state = "difficulty"
                    elif action == "local":
                        return (STATE_GAME_LOCAL, {})
                    elif action == "multiplayer":
                        return (STATE_MULTIPLAYER, {})
                    elif action == "tutorial":
                        return (STATE_TUTORIAL, {})
                    elif action == "quit":
                        return ("quit", {})

        elif self.state == "difficulty":
            for btn, lvl in self._diff_buttons:
                if btn.is_clicked(event):
                    self.difficulty = lvl
                    self.state = "color"
            if self._diff_back.is_clicked(event):
                self.state = "main"

        elif self.state == "color":
            for btn, col in self._color_buttons:
                if btn.is_clicked(event):
                    self.player_color = col
                    return (STATE_GAME_VS_AI, {
                        "difficulty":    self.difficulty,
                        "player_color":  self.player_color,
                    })
            if self._color_back.is_clicked(event):
                self.state = "difficulty"

        return (None, {})


class GameOverScreen:
    """Overlay shown when the game ends."""

    def __init__(self, surface: pygame.Surface):
        self.surface   = surface
        self.font_big  = _make_font("arial", 48, bold=True)
        self.font_body = _make_font("arial", 22)
        self.font_btn  = _make_font("arial", 18, bold=True)
        self._visible  = False
        self.winner    = ""
        self.reason    = ""
        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2
        self.btn_menu    = MenuButton(pygame.Rect(cx-200, cy+70, 180, 50),
                                      "Main Menu",  font=self.font_btn)
        self.btn_restart = MenuButton(pygame.Rect(cx+20,  cy+70, 180, 50),
                                      "Play Again", color=(40,80,60),
                                      hover_color=(55,110,80), font=self.font_btn)

    def show(self, winner: str, reason: str):
        self.winner   = winner
        self.reason   = reason
        self._visible = True

    def hide(self):
        self._visible = False

    @property
    def visible(self):
        return self._visible

    def draw(self):
        if not self._visible:
            return
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.surface.blit(overlay, (0, 0))

        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2

        # Card
        card = pygame.Rect(cx - 260, cy - 130, 520, 240)
        pygame.draw.rect(self.surface, PANEL_COLOR, card, border_radius=20)
        pygame.draw.rect(self.surface, TEXT_ACCENT,  card, 2, border_radius=20)

        # Winner text
        if self.winner == "draw":
            msg   = "Draw!"
            color = TEXT_SECONDARY
        elif self.winner == WHITE:
            msg   = "White Wins! 🏆"
            color = (240, 230, 180)
        else:
            msg   = "Black Wins! 🏆"
            color = TEXT_ACCENT
        title = self.font_big.render(msg, True, color)
        self.surface.blit(title, title.get_rect(centerx=cx, y=cy - 110))

        reason_txt = self.font_body.render(self.reason, True, TEXT_SECONDARY)
        self.surface.blit(reason_txt, reason_txt.get_rect(centerx=cx, y=cy - 45))

        mouse = pygame.mouse.get_pos()
        self.btn_menu.update(mouse)
        self.btn_restart.update(mouse)
        self.btn_menu.draw(self.surface)
        self.btn_restart.draw(self.surface)

    def handle_event(self, event) -> str | None:
        """Returns 'menu', 'restart', or None."""
        if not self._visible:
            return None
        if self.btn_menu.is_clicked(event):
            return "menu"
        if self.btn_restart.is_clicked(event):
            return "restart"
        return None
