"""
ai/engine.py
Chess AI using Minimax with Alpha-Beta pruning.
Runs on a python-chess Board directly for maximum speed.
"""

import chess
import random
import threading
from ai.evaluation import evaluate
from ai.difficulty import get_depth, apply_difficulty_filter


# ── Move ordering helpers (improves alpha-beta pruning efficiency) ─────────────

def _move_score(board: chess.Board, move: chess.Move) -> int:
    """Heuristic score for move ordering (higher = search first)."""
    score = 0
    # Prioritize captures (MVV-LVA: Most Valuable Victim, Least Valuable Attacker)
    if board.is_capture(move):
        victim    = board.piece_at(move.to_square)
        attacker  = board.piece_at(move.from_square)
        v_val     = _piece_val(victim.piece_type)  if victim   else 0
        a_val     = _piece_val(attacker.piece_type) if attacker else 0
        score    += 10 * v_val - a_val
    # Promotions
    if move.promotion:
        score += 900
    # Checks
    board.push(move)
    if board.is_check():
        score += 50
    board.pop()
    return score


def _piece_val(piece_type: int) -> int:
    vals = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
            chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000}
    return vals.get(piece_type, 0)


def _ordered_moves(board: chess.Board) -> list:
    """Returns legal moves sorted by heuristic score (best first)."""
    moves = list(board.legal_moves)
    moves.sort(key=lambda m: _move_score(board, m), reverse=True)
    return moves


# ── Minimax with Alpha-Beta pruning ───────────────────────────────────────────

def _minimax(board: chess.Board, depth: int,
             alpha: int, beta: int, maximizing: bool) -> tuple[int, chess.Move | None]:
    """
    Returns (score, best_move).
    Maximizing = white trying to maximize, minimizing = black.
    """
    if depth == 0 or board.is_game_over():
        return evaluate(board), None

    best_move = None

    if maximizing:
        max_eval = -100000
        for move in _ordered_moves(board):
            board.push(move)
            score, _ = _minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if score > max_eval:
                max_eval = score
                best_move = move
            alpha = max(alpha, score)
            if beta <= alpha:
                break  # β-cutoff
        return max_eval, best_move
    else:
        min_eval = 100000
        for move in _ordered_moves(board):
            board.push(move)
            score, _ = _minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if score < min_eval:
                min_eval = score
                best_move = move
            beta = min(beta, score)
            if beta <= alpha:
                break  # α-cutoff
        return min_eval, best_move


# ── Public interface ──────────────────────────────────────────────────────────

def get_best_move(board: chess.Board, difficulty: str) -> chess.Move | None:
    """
    Synchronous: Compute and return the best move for the current position.
    `difficulty` is one of EASY | MEDIUM | HARD.
    Returns None if no legal moves exist.
    """
    legal = list(board.legal_moves)
    if not legal:
        return None

    depth = get_depth(difficulty)
    is_white = board.turn == chess.WHITE

    _, best = _minimax(board.copy(), depth, -100000, 100000, is_white)

    if best is None:
        best = random.choice(legal)

    return apply_difficulty_filter(legal, best, difficulty)


class AIWorker:
    """
    Runs the AI computation on a background thread so the UI stays responsive.

    Usage:
        worker = AIWorker(board, difficulty)
        worker.start()
        # later, in your game loop:
        if worker.done:
            move = worker.result
    """

    def __init__(self, board: chess.Board, difficulty: str):
        self._board      = board.copy()
        self._difficulty = difficulty
        self.result: chess.Move | None = None
        self.done   = False
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.done = False
        self._thread.start()

    def _run(self):
        self.result = get_best_move(self._board, self._difficulty)
        self.done   = True
