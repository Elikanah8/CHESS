"""
core/board.py
Manages the full chess board state.

Uses python-chess under the hood for reliable move-legality and special-move
handling, while exposing a clean API the rest of the game (UI, AI) can use.
"""

import chess
import chess.svg
from utils.constants import WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING


# ── Mapping between python-chess symbols and our constants ────────────────────
_PIECE_TYPE_MAP = {
    chess.PAWN:   PAWN,
    chess.KNIGHT: KNIGHT,
    chess.BISHOP: BISHOP,
    chess.ROOK:   ROOK,
    chess.QUEEN:  QUEEN,
    chess.KING:   KING,
}

_COLOR_MAP = {
    chess.WHITE: WHITE,
    chess.BLACK: BLACK,
}


class BoardState:
    """
    Wraps a python-chess Board and exposes the information the game needs.

    Coordinate system used by the UI:
        row 0  = rank 8  (black's back rank, top of the screen when playing as White)
        row 7  = rank 1  (white's back rank, bottom of the screen)
        col 0  = file a  (left side)
        col 7  = file h  (right side)
    """

    def __init__(self, fen: str = chess.STARTING_FEN):
        self._board = chess.Board(fen)
        self.move_history: list[chess.Move] = []          # list of moves played
        self.captured_pieces: dict[str, list[str]] = {    # colour → list of piece types
            WHITE: [],   # pieces captured BY white  (i.e. black pieces taken)
            BLACK: [],   # pieces captured BY black  (i.e. white pieces taken)
        }

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def turn(self) -> str:
        """Whose turn it is: 'white' or 'black'."""
        return WHITE if self._board.turn == chess.WHITE else BLACK

    @property
    def is_check(self) -> bool:
        return self._board.is_check()

    @property
    def is_checkmate(self) -> bool:
        return self._board.is_checkmate()

    @property
    def is_stalemate(self) -> bool:
        return self._board.is_stalemate()

    @property
    def is_draw(self) -> bool:
        return (
            self._board.is_insufficient_material()
            or self._board.is_seventyfive_moves()
            or self._board.is_fivefold_repetition()
        )

    @property
    def is_game_over(self) -> bool:
        return self._board.is_game_over()

    @property
    def result(self) -> str:
        """Returns '1-0', '0-1', or '1/2-1/2'."""
        return self._board.result()

    # ── Board reading helpers ─────────────────────────────────────────────────

    def piece_at(self, row: int, col: int):
        """
        Returns a dict with 'type' and 'color' for the piece at (row, col),
        or None if the square is empty.
        """
        sq = self._rc_to_sq(row, col)
        piece = self._board.piece_at(sq)
        if piece is None:
            return None
        return {
            "type":  _PIECE_TYPE_MAP[piece.piece_type],
            "color": _COLOR_MAP[piece.color],
        }

    def get_all_pieces(self) -> list[dict]:
        """
        Returns a list of dicts describing every piece on the board.
        Each dict: { 'row', 'col', 'type', 'color' }
        """
        pieces = []
        for sq, piece in self._board.piece_map().items():
            row, col = self._sq_to_rc(sq)
            pieces.append({
                "row":   row,
                "col":   col,
                "type":  _PIECE_TYPE_MAP[piece.piece_type],
                "color": _COLOR_MAP[piece.color],
            })
        return pieces

    def legal_moves_from(self, row: int, col: int) -> list[tuple[int, int]]:
        """
        Returns a list of (row, col) squares that the piece on (row, col)
        can legally move to.
        """
        sq = self._rc_to_sq(row, col)
        targets = []
        for move in self._board.legal_moves:
            if move.from_square == sq:
                r, c = self._sq_to_rc(move.to_square)
                targets.append((r, c))
        return targets

    def is_legal_move(self, from_rc: tuple, to_rc: tuple) -> bool:
        """Check if a move from (row,col) to (row,col) is legal."""
        from_sq = self._rc_to_sq(*from_rc)
        to_sq   = self._rc_to_sq(*to_rc)
        move = chess.Move(from_sq, to_sq)
        # Handle promotion (auto-queen)
        promo_move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)
        return move in self._board.legal_moves or promo_move in self._board.legal_moves

    def is_promotion_move(self, from_rc: tuple, to_rc: tuple) -> bool:
        """Returns True if this move requires a pawn promotion choice."""
        from_sq = self._rc_to_sq(*from_rc)
        to_sq   = self._rc_to_sq(*to_rc)
        piece = self._board.piece_at(from_sq)
        if piece is None or piece.piece_type != chess.PAWN:
            return False
        to_rank = chess.square_rank(to_sq)
        return to_rank in (0, 7)

    def king_square(self, color: str) -> tuple[int, int]:
        """Returns (row, col) of the king of the given color."""
        chess_color = chess.WHITE if color == WHITE else chess.BLACK
        sq = self._board.king(chess_color)
        return self._sq_to_rc(sq)

    # ── Move execution ────────────────────────────────────────────────────────

    def push_move(self, from_rc: tuple, to_rc: tuple, promotion: str = QUEEN) -> bool:
        """
        Attempts to push a move (from_rc → to_rc).
        Returns True on success, False if illegal.
        promotion: piece type constant (QUEEN default) for pawn promotion.
        """
        from_sq = self._rc_to_sq(*from_rc)
        to_sq   = self._rc_to_sq(*to_rc)

        promo_map = {QUEEN: chess.QUEEN, ROOK: chess.ROOK,
                     BISHOP: chess.BISHOP, KNIGHT: chess.KNIGHT}
        promo_piece = promo_map.get(promotion, chess.QUEEN)

        # Build candidate moves
        candidates = [
            chess.Move(from_sq, to_sq),
            chess.Move(from_sq, to_sq, promotion=promo_piece),
        ]
        for move in candidates:
            if move in self._board.legal_moves:
                # Track captured piece
                captured = self._board.piece_at(to_sq)
                if captured:
                    capturer_color = WHITE if self._board.turn == chess.WHITE else BLACK
                    self.captured_pieces[capturer_color].append(
                        _PIECE_TYPE_MAP[captured.piece_type]
                    )
                # En passant capture
                if self._board.is_en_passant(move):
                    ep_color = WHITE if self._board.turn == chess.WHITE else BLACK
                    self.captured_pieces[ep_color].append(PAWN)

                self._board.push(move)
                self.move_history.append(move)
                return True
        return False

    def push_uci_move(self, uci: str) -> bool:
        """Push a move given in UCI notation (e.g. 'e2e4', 'e7e8q')."""
        try:
            move = chess.Move.from_uci(uci)
            from_rc = self._sq_to_rc(move.from_square)
            to_rc   = self._sq_to_rc(move.to_square)
            promo   = QUEEN
            if move.promotion:
                promo = _PIECE_TYPE_MAP[move.promotion]
            return self.push_move(from_rc, to_rc, promo)
        except Exception:
            return False

    def undo_move(self) -> bool:
        """Undoes the last move. Returns True on success."""
        if not self.move_history:
            return False
        self._board.pop()
        self.move_history.pop()
        # Rebuild captured pieces from scratch (simple approach)
        self._rebuild_captured()
        return True

    # ── AI interface ──────────────────────────────────────────────────────────

    def get_chess_board(self) -> chess.Board:
        """Returns the underlying python-chess Board (used by the AI)."""
        return self._board

    def get_legal_moves(self) -> list[chess.Move]:
        """Returns all legal moves for the current position."""
        return list(self._board.legal_moves)

    # ── FEN / state ───────────────────────────────────────────────────────────

    def to_fen(self) -> str:
        return self._board.fen()

    def load_fen(self, fen: str):
        self._board.set_fen(fen)
        self.move_history.clear()
        self.captured_pieces = {WHITE: [], BLACK: []}

    def copy(self) -> "BoardState":
        """Returns a deep copy of the board state (for AI search)."""
        new = BoardState.__new__(BoardState)
        new._board = self._board.copy()
        new.move_history = self.move_history.copy()
        new.captured_pieces = {
            WHITE: self.captured_pieces[WHITE].copy(),
            BLACK: self.captured_pieces[BLACK].copy(),
        }
        return new

    # ── Move notation ─────────────────────────────────────────────────────────

    def last_move_san(self) -> str:
        """Returns the last move in Standard Algebraic Notation, or ''."""
        if not self.move_history:
            return ""
        # We need to replay from one step before
        temp_board = chess.Board()
        for m in self.move_history[:-1]:
            temp_board.push(m)
        try:
            return temp_board.san(self.move_history[-1])
        except Exception:
            return self.move_history[-1].uci()

    def move_history_san(self) -> list[str]:
        """Returns full move history as list of SAN strings."""
        temp = chess.Board()
        result = []
        for move in self.move_history:
            try:
                result.append(temp.san(move))
                temp.push(move)
            except Exception:
                result.append(move.uci())
                temp.push(move)
        return result

    # ── Coordinate helpers ────────────────────────────────────────────────────

    @staticmethod
    def _rc_to_sq(row: int, col: int) -> int:
        """Convert (row, col) UI coords to python-chess square index."""
        rank = 7 - row   # row 0 → rank 7 (8th rank)
        file = col
        return chess.square(file, rank)

    @staticmethod
    def _sq_to_rc(sq: int) -> tuple[int, int]:
        """Convert python-chess square index to (row, col) UI coords."""
        rank = chess.square_rank(sq)
        file = chess.square_file(sq)
        return (7 - rank, file)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _rebuild_captured(self):
        """Rebuild captured piece lists by replaying move history."""
        temp = chess.Board()
        self.captured_pieces = {WHITE: [], BLACK: []}
        for move in self.move_history:
            cap = temp.piece_at(move.to_square)
            if cap:
                color = WHITE if temp.turn == chess.WHITE else BLACK
                self.captured_pieces[color].append(_PIECE_TYPE_MAP[cap.piece_type])
            if temp.is_en_passant(move):
                color = WHITE if temp.turn == chess.WHITE else BLACK
                self.captured_pieces[color].append(PAWN)
            temp.push(move)
