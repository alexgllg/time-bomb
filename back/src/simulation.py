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

from back.src.deck import Card
from back.src.game import Game
from back.src.player import Role
from back.src.strategies import Strategy


class GameState:
    """Wraps a `Game` with the "table-talk" extras used by some strategies.

    At the start of every phase, each player announces how many DEFUSE
    cards they currently hold (`claimed_defuse`). Sherlock players are
    truthful; Moriarty players shift their claim by `moriarty_bluff` cards
    (clamped to `[0, hand_size]`). A positive `moriarty_bluff` makes them
    over-claim (pretend to be a juicy target); a negative value makes them
    under-claim - hiding the DEFUSE cards they actually hold so pinchers
    look elsewhere, which can stall the count of revealed DEFUSE long enough
    for Moriarty to win by running out the clock. Each player also has a
    `trust` score (starting at 1.0) that is halved whenever the cards
    revealed from their hand during a phase contradict their claim - either
    because more DEFUSE cards were revealed than they admitted to having, or
    because their whole hand was emptied and the final DEFUSE count doesn't
    match their claim. Under-claiming is riskier: any DEFUSE revealed from
    their hand immediately exceeds their (low) claim and gets them caught.

    Any attribute not defined here (e.g. `players`, `pincher`, `phase`) is
    forwarded to the wrapped `Game`.
    """

    def __init__(self, game: 'Game', moriarty_bluff: int = 0):
        self.game = game
        self.moriarty_bluff = moriarty_bluff
        self.trust: Dict[str, float] = {pid: 1.0 for pid in game.players}
        self.claimed_defuse: Dict[str, int] = {}
        self._revealed_defuse: Dict[str, int] = {pid: 0 for pid in game.players}
        self._revealed_total: Dict[str, int] = {pid: 0 for pid in game.players}
        self._hand_size_at_phase_start: Dict[str, int] = {}
        self._caught_this_phase: Dict[str, bool] = {pid: False for pid in game.players}

    def __getattr__(self, name):
        return getattr(self.game, name)

    def start_phase(self) -> None:
        """Collect each player's DEFUSE-count announcement for the new phase."""
        for player_id, player in self.game.players.items():
            self._hand_size_at_phase_start[player_id] = len(player.hand)
            self._revealed_defuse[player_id] = 0
            self._revealed_total[player_id] = 0
            self._caught_this_phase[player_id] = False
            actual = sum(1 for card in player.hand if card == Card.DEFUSE)
            if player.role == Role.SHERLOCK:
                claim = actual
            else:
                claim = max(0, min(actual + self.moriarty_bluff, len(player.hand)))
            self.claimed_defuse[player_id] = claim

    def record_pinch(self, target_id: str, card: 'Card') -> None:
        """Update reveal counters for `target_id` and check for a caught lie."""
        self._revealed_total[target_id] += 1
        if card == Card.DEFUSE:
            self._revealed_defuse[target_id] += 1
        if (not self._caught_this_phase[target_id]
                and self._revealed_defuse[target_id] > self.claimed_defuse[target_id]):
            self._catch(target_id)

    def end_phase(self) -> None:
        """Catch players whose emptied hand contradicts their claim."""
        for player_id in self.game.players:
            if self._caught_this_phase[player_id]:
                continue
            hand_emptied = self._revealed_total[player_id] == self._hand_size_at_phase_start[player_id]
            if hand_emptied and self._revealed_defuse[player_id] != self.claimed_defuse[player_id]:
                self._catch(player_id)

    def _catch(self, player_id: str) -> None:
        self._caught_this_phase[player_id] = True
        self.trust[player_id] *= 0.5


def _win_reason(game: 'Game') -> str:
    """Classify how a finished `game` ended.

    Mirrors the priority order of `Game.is_game_over`: an all-DEFUSE board
    wins for Sherlock even if the bomb has (impossibly) also been seen.
    """
    if game.board[Card.DEFUSE] == game.number_of_players:
        return 'defuse_complete'
    if game.board[Card.BOMB] == 1:
        return 'bomb_revealed'
    return 'timeout'


def play_game(n_players: int,
               sherlock_strategy: 'Strategy',
               moriarty_strategy: 'Strategy',
               moriarty_bluff: int = 0) -> Tuple[str, int, str]:
    """Play one full game.

    Returns:
        A tuple `(winning_team, number_of_pinches, win_reason)`, where
        `win_reason` is one of `'defuse_complete'`, `'bomb_revealed'` or
        `'timeout'` (all DEFUSE not found within the 4 phases).
    """
    game = Game()
    for i in range(n_players):
        game.create_player(f'P{i}')
    game.start()

    state = GameState(game, moriarty_bluff=moriarty_bluff)
    state.start_phase()

    n_pinches = 0
    while not game.game_over:
        pincher_id = game.pincher
        previous_phase = game.phase
        strategy = (
            sherlock_strategy if game.players[pincher_id].role == Role.SHERLOCK
            else moriarty_strategy
        )
        target_name, card_id = strategy.choose(state, pincher_id, random)
        target_id = next(
            pid for pid, player in game.players.items() if player.name == target_name
        )
        revealed = Card(game.pinch_card(pincher_id, target_name, card_id))
        state.record_pinch(target_id, revealed)
        n_pinches += 1

        if not game.game_over and game.phase != previous_phase:
            state.end_phase()
            state.start_phase()

    return game.get_winning_team(), n_pinches, _win_reason(game)


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
                    n_games: int,
                    moriarty_bluff: int = 0) -> Dict:
    """Run `n_games` games and summarize Sherlock's results."""
    sherlock_wins = 0
    total_pinches = 0
    reason_counts = {'defuse_complete': 0, 'bomb_revealed': 0, 'timeout': 0}
    for _ in range(n_games):
        winner, n_pinches, reason = play_game(n_players, sherlock_strategy, moriarty_strategy, moriarty_bluff)
        if winner == Role.SHERLOCK.value:
            sherlock_wins += 1
        total_pinches += n_pinches
        reason_counts[reason] += 1

    lo, hi = wilson_interval(sherlock_wins, n_games)
    return {
        'n_players': n_players,
        'sherlock_strategy': sherlock_strategy.name,
        'moriarty_strategy': moriarty_strategy.name,
        'n_games': n_games,
        'sherlock_win_rate': sherlock_wins / n_games,
        'sherlock_win_rate_ci': (lo, hi),
        'avg_pinches': total_pinches / n_games,
        'bomb_revealed_rate': reason_counts['bomb_revealed'] / n_games,
        'timeout_rate': reason_counts['timeout'] / n_games,
    }
