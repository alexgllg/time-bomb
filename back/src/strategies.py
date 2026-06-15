"""Pinch strategies used by the simulation to evaluate luck vs. skill.

Each strategy decides, on behalf of the current pincher, which player to
target and which card of that player's hand to reveal. Strategies are split
into two families:

- "Blind" strategies (RANDOM, ROUND_ROBIN, MAX_HAND, MIN_HAND, FIRST_CARD):
  they only use information that is available to a player in the real game
  (whose turn it is, public hand sizes). They never look at the actual
  identity of a card before it is revealed.

- "Oracle" strategies (ORACLE_SHERLOCK, ORACLE_MORIARTY): they cheat by
  looking at the real `Card` value behind every legal choice. They model the
  theoretical best case where table-talk/bluffing has fully revealed where
  the bomb and the defuse cards are, and therefore represent the *skill
  ceiling* of the game.
"""
import random
from typing import List, Sequence, Tuple

from back.src.deck import Card
from back.src.game import Game


def legal_targets(game: 'Game', pincher_id: str) -> List[str]:
    """Return the ids of players that can legally be targeted by `pincher_id`."""
    return [
        player_id for player_id, player in game.players.items()
        if player_id != pincher_id and len(player.hand) > 0
    ]


class Strategy:
    """Base class for pinch strategies."""

    name = 'strategy'

    def choose(self,
               game: 'Game',
               pincher_id: str,
               rng: 'random.Random') -> Tuple[str, int]:
        """Return `(target_name, card_id)` for the current pincher to play."""
        raise NotImplementedError


class RandomStrategy(Strategy):
    """Pick a random legal target and a random card in their hand."""

    name = 'random'

    def choose(self, game, pincher_id, rng):
        target_id = rng.choice(legal_targets(game, pincher_id))
        card_id = rng.randrange(len(game.players[target_id].hand))
        return game.players[target_id].name, card_id


class RoundRobinStrategy(Strategy):
    """Always target the next player (in seating order) with cards left."""

    name = 'round_robin'

    def choose(self, game, pincher_id, rng):
        order = list(game.players.keys())
        start = order.index(pincher_id)
        for offset in range(1, len(order)):
            candidate = order[(start + offset) % len(order)]
            if len(game.players[candidate].hand) > 0:
                card_id = rng.randrange(len(game.players[candidate].hand))
                return game.players[candidate].name, card_id
        raise RuntimeError('No legal target available.')


class ExtremeHandSizeStrategy(Strategy):
    """Target whoever currently holds the most (or fewest) cards."""

    def __init__(self, prefer_max: bool):
        self.prefer_max = prefer_max
        self.name = 'max_hand_size' if prefer_max else 'min_hand_size'

    def choose(self, game, pincher_id, rng):
        targets = legal_targets(game, pincher_id)
        sizes = [len(game.players[t].hand) for t in targets]
        best = max(sizes) if self.prefer_max else min(sizes)
        best_targets = [t for t, size in zip(targets, sizes) if size == best]
        target_id = rng.choice(best_targets)
        card_id = rng.randrange(len(game.players[target_id].hand))
        return game.players[target_id].name, card_id


class FirstCardStrategy(Strategy):
    """Pick a random target but always reveal their first card."""

    name = 'first_card'

    def choose(self, game, pincher_id, rng):
        target_id = rng.choice(legal_targets(game, pincher_id))
        return game.players[target_id].name, 0


class OracleStrategy(Strategy):
    """Cheat: pick the best legal (target, card) pair given a priority list.

    `priority` lists `Card` values from most to least desirable. The first
    `Card` type in `priority` that exists among all legal choices is
    revealed (ties broken randomly).
    """

    def __init__(self, priority: Sequence['Card'], name: str):
        self.priority = priority
        self.name = name

    def choose(self, game, pincher_id, rng):
        candidates = [
            (target_id, card_index, card)
            for target_id in legal_targets(game, pincher_id)
            for card_index, card in enumerate(game.players[target_id].hand)
        ]
        for wanted in self.priority:
            matches = [(t, i) for (t, i, c) in candidates if c == wanted]
            if matches:
                target_id, card_id = rng.choice(matches)
                return game.players[target_id].name, card_id
        # Should not happen: every card type is covered by `priority`.
        target_id, card_id, _ = rng.choice(candidates)
        return game.players[target_id].name, card_id


RANDOM = RandomStrategy()
ROUND_ROBIN = RoundRobinStrategy()
MAX_HAND = ExtremeHandSizeStrategy(prefer_max=True)
MIN_HAND = ExtremeHandSizeStrategy(prefer_max=False)
FIRST_CARD = FirstCardStrategy()

# Sherlock wants to surface every DEFUSE card without ever exposing the BOMB.
ORACLE_SHERLOCK = OracleStrategy((Card.DEFUSE, Card.SECURE, Card.BOMB), 'oracle_sherlock')
# Moriarty wants to surface the BOMB, or otherwise stall with SECURE cards.
ORACLE_MORIARTY = OracleStrategy((Card.BOMB, Card.SECURE, Card.DEFUSE), 'oracle_moriarty')

BLIND_STRATEGIES = (RANDOM, ROUND_ROBIN, MAX_HAND, MIN_HAND, FIRST_CARD)
