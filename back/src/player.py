"""Player file"""
import random
from enum import Enum
from typing import TYPE_CHECKING, Union, List, Dict

from back.src.deck import Card

if TYPE_CHECKING:
    from back.src.game import Game


class Role(Enum):
    """Role enumerator."""
    MORIARTY = 'moriarty'
    SHERLOCK = 'sherlock'


class Player:
    """Player class."""
    def __init__(self,
                 game: 'Game',
                 player_id: str,
                 player_name: str):
        self.id: str = player_id
        self.name: str = player_name
        self.role: Union[None, 'Role'] = None
        self.game: 'Game' = game
        self.hand: List['Card'] = []
        self.hand_history = dict()

    def assign_role(self,
                    role: 'Role'):
        """
        Assign a role to a player.

        Args:
            role: a role
        """
        self.role = role

    def get_role(self) -> str:
        """
        Get player's role.

        Returns: str
            The player's role.
        """
        if isinstance(self.role, Role):
            return self.role.value
        print("The player's role hasn't been created yet.")

    def get_cards(self) -> Dict[str, int]:
        """
        Get player's cards.

        Returns: str
            The player's cards.
        """
        return {
            card.value: self.hand.count(card) for card in Card
        }

    def deal_card(self,
                  card: 'Card'):
        """"""
        assert len(self.hand)+1 <= self.game.legal_cards_per_hand(), "Number of player cards at phase {} cannot " \
            "exceed {}.".format(self.game.phase, self.game.legal_cards_per_hand())
        self.hand.append(card)

    def _add_new_phase_into_hand_history(self):
        """"""
        self.hand_history[self.game.phase] = {self.game.step: list(self.hand)}

    def update_hand_history(self):
        """"""
        self.hand_history[self.game.phase][self.game.step] = list(self.hand)

    def shuffle_hand(self):
        """"""
        random.shuffle(self.hand)
        self._add_new_phase_into_hand_history()