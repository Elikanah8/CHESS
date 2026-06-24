"""
ai/difficulty.py
Difficulty configuration for the chess AI.
"""

import random
import chess
from utils.constants import EASY, MEDIUM, HARD, AI_DEPTH, AI_RANDOM_FACTOR


def get_depth(difficulty: str) -> int:
    return AI_DEPTH.get(difficulty, 3)


def get_random_factor(difficulty: str) -> float:
    return AI_RANDOM_FACTOR.get(difficulty, 0.0)


def apply_difficulty_filter(moves: list, best_move: chess.Move,
                             difficulty: str) -> chess.Move:
    """
    Potentially returns a random move instead of the best move,
    based on the difficulty's random factor.
    """
    if not moves:
        return best_move
    rand = get_random_factor(difficulty)
    if rand > 0 and random.random() < rand:
        return random.choice(moves)
    return best_move


DIFFICULTY_LABELS = {
    EASY:   "Easy   🟢",
    MEDIUM: "Medium 🟡",
    HARD:   "Hard   🔴",
}

DIFFICULTY_DESCRIPTIONS = {
    EASY:   "Makes occasional mistakes — great for beginners.",
    MEDIUM: "Plays solid chess with minor slip-ups.",
    HARD:   "Full strength — good luck!",
}
