"""
ai/evaluation.py
Static board evaluation for the chess AI.
Returns a score in centipawns (positive = good for white).
"""

import chess
from utils.constants import PIECE_VALUE, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING

# ── Piece-Square Tables (white's perspective, a1=index 0, h8=index 63) ────────
# Values encourage good piece placement. Mirrored for black.

PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_MIDDLE_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]

KING_END_TABLE = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50,
]

_PIECE_TYPE_MAP = {
    chess.PAWN:   PAWN,
    chess.KNIGHT: KNIGHT,
    chess.BISHOP: BISHOP,
    chess.ROOK:   ROOK,
    chess.QUEEN:  QUEEN,
    chess.KING:   KING,
}

_PST = {
    chess.PAWN:   PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK:   ROOK_TABLE,
    chess.QUEEN:  QUEEN_TABLE,
    chess.KING:   KING_MIDDLE_TABLE,
}


def _is_endgame(board: chess.Board) -> bool:
    """Simple endgame detection: queens gone or very few pieces."""
    queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + \
             len(board.pieces(chess.QUEEN, chess.BLACK))
    total  = len(board.piece_map())
    return queens == 0 or total <= 10


def _piece_square_value(piece_type: int, sq: int, color: bool, endgame: bool) -> int:
    """Returns the positional bonus for a piece on a given square."""
    if piece_type == chess.KING and endgame:
        table = KING_END_TABLE
    else:
        table = _PST.get(piece_type, [0] * 64)

    # For white, square index matches table directly (a1=0).
    # For black, mirror vertically (flip rank).
    if color == chess.WHITE:
        # table is from white's view, rank 8 first → we need to flip
        rank = chess.square_rank(sq)
        file = chess.square_file(sq)
        idx  = (7 - rank) * 8 + file
    else:
        rank = chess.square_rank(sq)
        file = chess.square_file(sq)
        idx  = rank * 8 + file
    return table[idx]


def evaluate(board: chess.Board) -> int:
    """
    Returns a static evaluation of `board` in centipawns.
    Positive  = good for White.
    Negative  = good for Black.
    """
    if board.is_checkmate():
        return -30000 if board.turn == chess.WHITE else 30000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    endgame = _is_endgame(board)
    score   = 0

    for sq, piece in board.piece_map().items():
        mat = PIECE_VALUE[_PIECE_TYPE_MAP[piece.piece_type]]
        pst = _piece_square_value(piece.piece_type, sq, piece.color, endgame)
        val = mat + pst
        if piece.color == chess.WHITE:
            score += val
        else:
            score -= val

    return score
