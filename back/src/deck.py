"""Deck class"""
import random

from typing import List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from back.src.game import Game


class Card(Enum):
    """Card enumerator."""
    SECURE = 'secure'
    DEFUSE = 'defuse'
    BOMB = 'bomb'


class Deck:
    """Deck class."""
    def __init__(self,
                 game: 'Game'):
        self.game = game
        self.cards = self._initialize_cards(self.game.number_of_players)

    def _initialize_cards(self,
                          number_of_players: int) -> List[Card]:
        """Initialize deck cards.

        Args:
            number_of_players: The number of players in the game

        Returns: List[Card]
            A shuffled list of cards.
        """
        defuse_list = number_of_players*[Card.DEFUSE]
        secure_list = (4*number_of_players-1)*[Card.SECURE]
        card_list = defuse_list + secure_list + [Card.BOMB]
        random.shuffle(card_list)
        return card_list

    def deal_cards(self) -> None:
        """"""
        for _ in range(self.game.legal_cards_per_hand()):
            for player_id in self.game.players.keys():
                self.game.players[player_id].deal_card(self.cards.pop(0))
        self.game.shuffle_player_hands()

    def refill(self):
        """Refill deck of cards from players' hands."""
        for player_id in self.game.players.keys():
            self.cards.extend(self.game.players[player_id].hand)
            self.game.players[player_id].hand = []
