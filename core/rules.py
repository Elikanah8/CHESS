"""
core/rules.py
High-level rule queries (convenience wrappers around BoardState).
Also contains helpers for the tutorial mode to set up specific positions.
"""

import chess
from core.board import BoardState
from utils.constants import WHITE, BLACK


def get_game_status(board: BoardState) -> dict:
    """
    Returns a dict describing the current game status.

    Keys:
        over        : bool — is the game finished?
        winner      : 'white' | 'black' | 'draw' | None
        reason      : human-readable reason string
        check       : bool — is the side to move in check?
    """
    status = {
        "over":   False,
        "winner": None,
        "reason": "",
        "check":  board.is_check,
    }

    if board.is_checkmate:
        status["over"]   = True
        # The side that just moved wins (the OTHER side is in checkmate)
        status["winner"] = BLACK if board.turn == WHITE else WHITE
        status["reason"] = "Checkmate"

    elif board.is_stalemate:
        status["over"]   = True
        status["winner"] = "draw"
        status["reason"] = "Stalemate"

    elif board.is_draw:
        cb = board.get_chess_board()
        status["over"]   = True
        status["winner"] = "draw"
        if cb.is_insufficient_material():
            status["reason"] = "Insufficient material"
        elif cb.is_seventyfive_moves():
            status["reason"] = "75-move rule"
        elif cb.is_fivefold_repetition():
            status["reason"] = "Fivefold repetition"
        else:
            status["reason"] = "Draw"

    return status


def is_under_attack(board: BoardState, row: int, col: int, by_color: str) -> bool:
    """Check if square (row, col) is attacked by pieces of `by_color`."""
    cb    = board.get_chess_board()
    sq    = BoardState._rc_to_sq(row, col)
    color = chess.WHITE if by_color == WHITE else chess.BLACK
    return cb.is_attacked_by(color, sq)


# ── Tutorial position factory ─────────────────────────────────────────────────

TUTORIAL_POSITIONS = {
    "start": chess.STARTING_FEN,

    "scholars_mate_threat": (
        "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 4 4"
    ),

    "en_passant": (
        "rnbqkbnr/ppp2ppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"
    ),

    "castling_available": (
        "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"
    ),

    "promotion": (
        "8/P7/8/8/8/8/8/4K2k w - - 0 1"
    ),

    "simple_fork": (
        "r1bqkb1r/ppp2ppp/3p4/4n3/3PP3/2N5/PPP2PPP/R1BQKB1R b KQkq - 0 6"
    ),

    "checkmate_in_1": (
        "6k1/5ppp/8/8/8/8/8/4R2K w - - 0 1"
    ),

    "pin_example": (
        "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/3B1N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    ),

    "endgame_rook": (
        "8/8/8/8/8/4k3/8/4K2R w - - 0 1"
    ),
}


def load_tutorial_position(board: BoardState, name: str) -> bool:
    """
    Load a named tutorial position into the board.
    Returns True on success.
    """
    fen = TUTORIAL_POSITIONS.get(name)
    if fen is None:
        return False
    board.load_fen(fen)
    return True
