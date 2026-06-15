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

- "Informed" strategies (InformedSherlockStrategy, InformedMoriartyStrategy):
  a middle ground modelling table-talk about a single piece of information,
  "who currently holds the bomb card". Sherlock players always announce it
  truthfully if it is them. Moriarty players hide it with probability
  `lie_rate`. There is no private Moriarty channel: a Moriarty player who
  hides the bomb keeps it secret from everyone, including their own team.

- "Defuse announcement" strategies (DefuseAnnouncementStrategy,
  TrustWeightedStrategy, SuspicionWeightedStrategy): at the start of every
  phase, each player announces how many DEFUSE cards they currently hold.
  Sherlock players are truthful; Moriarty players may shift their claim by
  `GameState.moriarty_bluff` cards (see `back/src/simulation.py`) - a
  positive value over-claims (looks like a juicy target), a negative value
  under-claims (hides DEFUSE cards to avoid being pinched and stall the
  game). `TrustWeightedStrategy` weighs these claims by a per-player "trust"
  score that drops whenever a player's claim is later proven wrong by the
  cards actually revealed from their hand. `SuspicionWeightedStrategy` goes
  further: once a player is caught lying, their (now unreliable, possibly
  under-claimed) announcement is blended with their remaining hand size.

All strategies receive a `GameState` (see `back/src/simulation.py`) as their
first argument. `GameState` transparently exposes the underlying `Game`'s
attributes (`players`, `pincher`, ...), so strategies that only need the raw
game state can keep treating it like a `Game`.
"""
import random
from typing import List, Optional, Sequence, Tuple

from back.src.deck import Card
from back.src.player import Role


def legal_targets(state, pincher_id: str) -> List[str]:
    """Return the ids of players that can legally be targeted by `pincher_id`."""
    return [
        player_id for player_id, player in state.players.items()
        if player_id != pincher_id and len(player.hand) > 0
    ]


class Strategy:
    """Base class for pinch strategies."""

    name = 'strategy'

    def choose(self,
               state: 'GameState',
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


def find_bomb_holder(state) -> Optional[str]:
    """Return the id of the player currently holding the BOMB card, if any."""
    for player_id, player in state.players.items():
        if Card.BOMB in player.hand:
            return player_id
    return None


def _announced_bomb_holder(state,
                            rng: 'random.Random',
                            lie_rate: float) -> Optional[str]:
    """Return the id of the player publicly believed to hold the bomb.

    Sherlock players always tell the truth: if they hold the bomb, it is
    announced. Moriarty players hide it with probability `lie_rate`; there is
    no private channel, so a hidden bomb is unknown to everyone, including
    other Moriarty players.
    """
    holder_id = find_bomb_holder(state)
    if holder_id is None:
        return None
    holder = state.players[holder_id]
    if holder.role == Role.SHERLOCK:
        return holder_id
    if rng.random() >= lie_rate:
        return holder_id
    return None


class InformedSherlockStrategy(Strategy):
    """Avoid the player publicly known to hold the bomb, if any."""

    def __init__(self, lie_rate: float):
        self.lie_rate = lie_rate
        self.name = f'informed_sherlock(lie={lie_rate:.2f})'

    def choose(self, state, pincher_id, rng):
        targets = legal_targets(state, pincher_id)
        suspect = _announced_bomb_holder(state, rng, self.lie_rate)
        safe_targets = [t for t in targets if t != suspect] or targets
        target_id = rng.choice(safe_targets)
        card_id = rng.randrange(len(state.players[target_id].hand))
        return state.players[target_id].name, card_id


class InformedMoriartyStrategy(Strategy):
    """Target the player known to hold the bomb, if any, to expose it."""

    def __init__(self, lie_rate: float):
        self.lie_rate = lie_rate
        self.name = f'informed_moriarty(lie={lie_rate:.2f})'

    def choose(self, state, pincher_id, rng):
        targets = legal_targets(state, pincher_id)
        suspect = _announced_bomb_holder(state, rng, self.lie_rate)
        target_id = suspect if suspect in targets else rng.choice(targets)
        card_id = rng.randrange(len(state.players[target_id].hand))
        return state.players[target_id].name, card_id


class DefuseAnnouncementStrategy(Strategy):
    """Target whoever publicly claimed the most DEFUSE cards this phase."""

    name = 'defuse_announcement'

    def choose(self, state, pincher_id, rng):
        targets = legal_targets(state, pincher_id)
        best = max(state.claimed_defuse[t] for t in targets)
        best_targets = [t for t in targets if state.claimed_defuse[t] == best]
        target_id = rng.choice(best_targets)
        card_id = rng.randrange(len(state.players[target_id].hand))
        return state.players[target_id].name, card_id


class TrustWeightedStrategy(Strategy):
    """Target whoever has the highest (claimed DEFUSE x trust) score.

    A player's claim is discounted by their `trust` score (see
    `GameState`), which drops whenever that player was previously caught
    announcing a DEFUSE count that the revealed cards proved wrong.
    """

    name = 'trust_weighted'

    def choose(self, state, pincher_id, rng):
        targets = legal_targets(state, pincher_id)
        scores = {t: state.claimed_defuse[t] * state.trust[t] for t in targets}
        best = max(scores.values())
        best_targets = [t for t in targets if scores[t] == best]
        target_id = rng.choice(best_targets)
        card_id = rng.randrange(len(state.players[target_id].hand))
        return state.players[target_id].name, card_id


class SuspicionWeightedStrategy(Strategy):
    """Target whoever is most likely to still be hiding DEFUSE cards.

    For a fully trusted player (`trust == 1`), the score is just their
    claimed DEFUSE count, like `TrustWeightedStrategy`. For a player who has
    been caught lying at least once, `trust < 1` and the claim is no longer
    reliable: the score blends in their remaining hand size, on the
    assumption that a known liar could still be hiding up to a full hand of
    DEFUSE. This makes getting caught costly even for a player who
    under-claims down to 0.
    """

    name = 'suspicion_weighted'

    def choose(self, state, pincher_id, rng):
        targets = legal_targets(state, pincher_id)

        def score(t):
            trust = state.trust[t]
            return trust * state.claimed_defuse[t] + (1 - trust) * len(state.players[t].hand)

        scores = {t: score(t) for t in targets}
        best = max(scores.values())
        best_targets = [t for t in targets if scores[t] == best]
        target_id = rng.choice(best_targets)
        card_id = rng.randrange(len(state.players[target_id].hand))
        return state.players[target_id].name, card_id
