"""
main.py
Entry point for the Chess Game.
Manages the top-level game loop and routes between menu, game, and tutorial.
"""

import sys
import pygame
import chess

from utils.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, WINDOW_TITLE,
    BG_COLOR, PANEL_COLOR, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_ACCENT, TEXT_GOLD, PANEL_BORDER,
    BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE,
    STATE_MENU, STATE_GAME_VS_AI, STATE_GAME_LOCAL,
    STATE_TUTORIAL, STATE_MULTIPLAYER,
    WHITE, BLACK, MEDIUM,
)
from core.board import BoardState
from core.rules import get_game_status
from ai.engine import AIWorker
from ui.renderer import Renderer
from ui.menu import MenuScreen, GameOverScreen
from ui.hud import HUD
from ui.tutorial import TutorialScreen


# ── Multiplayer placeholder screen ────────────────────────────────────────────

class MultiplayerPlaceholder:
    """Shown until the full multiplayer module is built."""

    def __init__(self, surface):
        self.surface  = surface
        self.font_big = pygame.font.SysFont("arial", 36, bold=True)
        self.font_sub = pygame.font.SysFont("arial", 18)
        self.font_btn = pygame.font.SysFont("arial", 16, bold=True)
        btn_w, btn_h  = 200, 46
        self.btn_back = pygame.Rect(WINDOW_WIDTH//2 - btn_w//2,
                                    WINDOW_HEIGHT//2 + 80, btn_w, btn_h)

    def draw(self):
        self.surface.fill(BG_COLOR)
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2

        title = self.font_big.render("🌐 Online Multiplayer", True, TEXT_ACCENT)
        self.surface.blit(title, title.get_rect(centerx=cx, y=cy - 120))

        lines = [
            "Coming in the next build!",
            "Players will connect using a shared 6-character room code.",
            "The server will relay moves in real time.",
        ]
        for i, line in enumerate(lines):
            t = self.font_sub.render(line, True, TEXT_SECONDARY)
            self.surface.blit(t, t.get_rect(centerx=cx, y=cy - 60 + i * 32))

        hover = self.btn_back.collidepoint(pygame.mouse.get_pos())
        c = (60, 66, 90) if hover else (45, 50, 70)
        pygame.draw.rect(self.surface, c, self.btn_back, border_radius=8)
        pygame.draw.rect(self.surface, PANEL_BORDER, self.btn_back, 1, border_radius=8)
        bt = self.font_btn.render("← Back to Menu", True, TEXT_PRIMARY)
        self.surface.blit(bt, bt.get_rect(center=self.btn_back.center))

    def handle_event(self, event) -> str | None:
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.btn_back.collidepoint(event.pos)):
            return "menu"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "menu"
        return None


# ── Game session ──────────────────────────────────────────────────────────────

class GameSession:
    """
    A single chess game — vs AI or local 2-player.
    Call update() and draw() every frame.
    """

    def __init__(self, surface: pygame.Surface,
                 mode: str = STATE_GAME_VS_AI,
                 difficulty: str = MEDIUM,
                 player_color: str = WHITE):
        self.surface      = surface
        self.mode         = mode
        self.difficulty   = difficulty
        self.player_color = player_color

        self.board     = BoardState()
        self.renderer  = Renderer(surface)
        self.hud       = HUD(surface)
        self.game_over = GameOverScreen(surface)

        self.selected_rc   = None
        self.legal_targets = []
        self.last_move_rcs = []

        self.ai_worker: AIWorker | None = None
        self.ai_thinking = False

        # Flipped if player chose Black
        self.flipped = (player_color == BLACK)

        # If AI plays white, trigger AI first move immediately
        if mode == STATE_GAME_VS_AI and player_color == BLACK:
            self._start_ai()

    # ── AI handling ───────────────────────────────────────────────────────────

    def _is_ai_turn(self) -> bool:
        if self.mode != STATE_GAME_VS_AI:
            return False
        return self.board.turn != self.player_color

    def _start_ai(self):
        if self.ai_thinking:
            return
        self.ai_worker  = AIWorker(self.board.get_chess_board(), self.difficulty)
        self.ai_thinking = True
        self.ai_worker.start()

    def _check_ai_done(self):
        if self.ai_worker and self.ai_worker.done:
            move = self.ai_worker.result
            self.ai_worker   = None
            self.ai_thinking = False
            if move:
                from_sq = move.from_square
                to_sq   = move.to_square
                from_rc = BoardState._sq_to_rc(from_sq)
                to_rc   = BoardState._sq_to_rc(to_sq)
                self.board.push_move(from_rc, to_rc,
                                     promotion="Q" if move.promotion else "Q")
                self.last_move_rcs = [from_rc, to_rc]
            self._check_game_over()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self):
        if self.game_over.visible:
            return
        if self.ai_thinking:
            self._check_ai_done()
            self.hud.tick(self.board.turn)
        elif not self._is_ai_turn():
            self.hud.tick(self.board.turn)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self):
        self.surface.fill(BG_COLOR)

        status = get_game_status(self.board)
        check_rc = self.board.king_square(self.board.turn) if self.board.is_check else None

        self.renderer.draw_board(
            selected_rc   = self.selected_rc,
            legal_targets = self.legal_targets,
            last_move_rcs = self.last_move_rcs,
            check_king_rc = check_rc,
            flipped       = self.flipped,
        )
        self.renderer.draw_pieces(
            self.board.get_all_pieces(),
            flipped       = self.flipped,
            legal_targets = self.legal_targets,
        )

        # Status message
        status_msg = ""
        if status["check"] and not status["over"]:
            status_msg = f"⚠  {'White' if self.board.turn==WHITE else 'Black'} is in CHECK!"

        self.hud.draw(
            current_turn      = self.board.turn,
            move_history_san  = self.board.move_history_san(),
            captured          = self.board.captured_pieces,
            status_msg        = status_msg,
            player_color      = self.player_color,
            ai_thinking       = self.ai_thinking,
            difficulty        = self.difficulty if self.mode == STATE_GAME_VS_AI else "",
        )

        if self.game_over.visible:
            self.game_over.draw()

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event) -> str | None:
        """Returns 'menu', 'restart', or None."""
        # Game-over screen first
        if self.game_over.visible:
            result = self.game_over.handle_event(event)
            if result:
                self.game_over.hide()
            return result

        # HUD buttons
        hud_action = self.hud.handle_event(event)
        if hud_action == "menu":
            return "menu"
        if hud_action == "resign":
            winner = BLACK if self.board.turn == WHITE else WHITE
            self.game_over.show(winner, "Resignation")
            return None
        if hud_action == "undo":
            self._do_undo()
            return None

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "menu"
            if event.key == pygame.K_u:
                self._do_undo()

        # Board clicks
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and not self.ai_thinking):
            rc = Renderer.pixel_to_rc(event.pos, self.flipped)
            if rc:
                self._handle_board_click(rc)

        return None

    def _handle_board_click(self, rc: tuple):
        if self.game_over.visible:
            return

        # If a piece is already selected
        if self.selected_rc is not None:
            if rc in self.legal_targets:
                # Execute move
                success = self.board.push_move(self.selected_rc, rc)
                if success:
                    self.last_move_rcs = [self.selected_rc, rc]
                    self._check_game_over()
                    # Trigger AI
                    if not self.game_over.visible and self._is_ai_turn():
                        self._start_ai()
                self.selected_rc   = None
                self.legal_targets = []
                return
            else:
                # Click on own piece — re-select
                piece = self.board.piece_at(*rc)
                if piece and piece["color"] == self.board.turn:
                    self.selected_rc   = rc
                    self.legal_targets = self.board.legal_moves_from(*rc)
                    return
                self.selected_rc   = None
                self.legal_targets = []
                return

        # Select a piece
        piece = self.board.piece_at(*rc)
        if piece and piece["color"] == self.board.turn:
            # In vs-AI mode, only allow selecting player's own color
            if self.mode == STATE_GAME_VS_AI and piece["color"] != self.player_color:
                return
            self.selected_rc   = rc
            self.legal_targets = self.board.legal_moves_from(*rc)

    def _do_undo(self):
        if self.ai_thinking:
            return
        # Undo twice in vs-AI mode (player move + AI move)
        self.board.undo_move()
        if self.mode == STATE_GAME_VS_AI:
            self.board.undo_move()
        self.selected_rc   = None
        self.legal_targets = []
        self.last_move_rcs = []

    def _check_game_over(self):
        status = get_game_status(self.board)
        if status["over"]:
            self.game_over.show(status["winner"] or "draw", status["reason"])


# ── Main application ──────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock  = pygame.time.Clock()

    app_state  = STATE_MENU
    menu       = MenuScreen(screen)
    tutorial   = None
    game       = None
    mp_screen  = None

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

            # ── Menu ─────────────────────────────────────────────────────────
            if app_state == STATE_MENU:
                next_state, params = menu.handle_event(event)
                if next_state == "quit":
                    running = False
                elif next_state == STATE_GAME_VS_AI:
                    game      = GameSession(screen,
                                            mode         = STATE_GAME_VS_AI,
                                            difficulty   = params["difficulty"],
                                            player_color = params["player_color"])
                    app_state = STATE_GAME_VS_AI

                elif next_state == STATE_GAME_LOCAL:
                    game      = GameSession(screen, mode=STATE_GAME_LOCAL)
                    app_state = STATE_GAME_LOCAL

                elif next_state == STATE_TUTORIAL:
                    tutorial  = TutorialScreen(screen)
                    app_state = STATE_TUTORIAL

                elif next_state == STATE_MULTIPLAYER:
                    mp_screen = MultiplayerPlaceholder(screen)
                    app_state = STATE_MULTIPLAYER

            # ── Game (vs AI or local) ─────────────────────────────────────
            elif app_state in (STATE_GAME_VS_AI, STATE_GAME_LOCAL):
                result = game.handle_event(event)
                if result == "menu":
                    app_state = STATE_MENU
                    menu      = MenuScreen(screen)
                elif result == "restart":
                    game = GameSession(screen,
                                       mode         = game.mode,
                                       difficulty   = game.difficulty,
                                       player_color = game.player_color)

            # ── Tutorial ──────────────────────────────────────────────────
            elif app_state == STATE_TUTORIAL:
                result = tutorial.handle_event(event)
                if result == "menu":
                    app_state = STATE_MENU
                    menu      = MenuScreen(screen)

            # ── Multiplayer ───────────────────────────────────────────────
            elif app_state == STATE_MULTIPLAYER:
                result = mp_screen.handle_event(event)
                if result == "menu":
                    app_state = STATE_MENU
                    menu      = MenuScreen(screen)

        # ── Update ─────────────────────────────────────────────────────────
        if app_state == STATE_MENU:
            menu.update()
        elif app_state in (STATE_GAME_VS_AI, STATE_GAME_LOCAL):
            game.update()
        elif app_state == STATE_TUTORIAL:
            tutorial.update()

        # ── Draw ───────────────────────────────────────────────────────────
        if app_state == STATE_MENU:
            menu.draw()
        elif app_state in (STATE_GAME_VS_AI, STATE_GAME_LOCAL):
            game.draw()
        elif app_state == STATE_TUTORIAL:
            tutorial.draw()
        elif app_state == STATE_MULTIPLAYER:
            mp_screen.draw()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
