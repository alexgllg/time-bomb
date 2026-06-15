"""Headless simulation of Time Bomb games used to measure luck vs. skill.

A "pincher" strategy is chosen for each team (Sherlock / Moriarty). On every
turn, the strategy belonging to the current pincher's team picks the
`(target, card)` pinch. Running many games for a given pair of strategies
gives Sherlock's win rate, which can be compared across strategies and
player counts.
"""
import math
import random
from typing import Dict, Tuple

from back.src.game import Game
from back.src.player import Role
from back.src.strategies import Strategy


def play_game(n_players: int,
               sherlock_strategy: 'Strategy',
               moriarty_strategy: 'Strategy') -> Tuple[str, int]:
    """Play one full game.

    Returns:
        A tuple `(winning_team, number_of_pinches)`.
    """
    game = Game()
    for i in range(n_players):
        game.create_player(f'P{i}')
    game.start()

    n_pinches = 0
    while not game.game_over:
        pincher_id = game.pincher
        strategy = (
            sherlock_strategy if game.players[pincher_id].role == Role.SHERLOCK
            else moriarty_strategy
        )
        target_name, card_id = strategy.choose(game, pincher_id, random)
        game.pinch_card(pincher_id, target_name, card_id)
        n_pinches += 1

    return game.get_winning_team(), n_pinches


def wilson_interval(wins: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """95% Wilson score confidence interval for a binomial proportion."""
    if n == 0:
        return 0.0, 0.0
    p = wins / n
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    spread = (z * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2))) / denom
    return max(0.0, center - spread), min(1.0, center + spread)


def run_experiment(n_players: int,
                    sherlock_strategy: 'Strategy',
                    moriarty_strategy: 'Strategy',
                    n_games: int) -> Dict:
    """Run `n_games` games and summarize Sherlock's results."""
    sherlock_wins = 0
    total_pinches = 0
    for _ in range(n_games):
        winner, n_pinches = play_game(n_players, sherlock_strategy, moriarty_strategy)
        if winner == Role.SHERLOCK.value:
            sherlock_wins += 1
        total_pinches += n_pinches

    lo, hi = wilson_interval(sherlock_wins, n_games)
    return {
        'n_players': n_players,
        'sherlock_strategy': sherlock_strategy.name,
        'moriarty_strategy': moriarty_strategy.name,
        'n_games': n_games,
        'sherlock_win_rate': sherlock_wins / n_games,
        'sherlock_win_rate_ci': (lo, hi),
        'avg_pinches': total_pinches / n_games,
    }
