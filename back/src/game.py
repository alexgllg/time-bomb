"""Game file."""
import random
import uuid

from typing import Dict, List, Union

from back.src.deck import Card, Deck
from back.src.player import Player, Role
from back.src.rules import ROLE_MAPPING


def _is_player_creation_legal(
        player_name: str,
        number_of_players
) -> bool:
    """Check if player creation is possible.

    Args:
        player_name: A list of player names.

    Returns: bool
        `True` if game is possible. `False` otherwise.
    """
    assert isinstance(player_name, str)
    assert player_name != ''
    return 0 <= number_of_players < 8


class Game:
    """Game class."""

    def __init__(self):
        self.id = str(uuid.uuid4())
        self.players: Dict[str, 'Player'] = dict()
        self.player_names: List[str] = list()
        self.phase: int = 1
        self.step: int = 1
        self.board: Dict['Card', int] = {
            Card.SECURE: 0,
            Card.DEFUSE: 0,
            Card.BOMB: 0
        }
        self.deck: Union[None, 'Deck'] = None
        self.game_stared: bool = False
        self.game_over: bool = False
        self.winning_team: Union[None, 'Role'] = None
        self.pincher: Union[None, str] = None
        self.are_cards_shuffled = False

    def create_player(self,
                      player_name: str) -> str:
        """
        Create new player in the game.

        Args:
            player_name: the player's name.

        Returns: str
            The created player's id.
        """
        assert _is_player_creation_legal(
            player_name, self.number_of_players
        ), 'The number of possible players cannot exceed 8.'
        if player_name in self.player_names:
            raise ValueError(
                f'The player name {player_name} already exists in the current game.'
            )
        player_uuid = str(uuid.uuid4())
        self.players[player_uuid] = Player(self, player_uuid, player_name)
        self.player_names.append(player_name)
        return player_uuid

    def start(self):
        """
        Start game.
        """
        if not 4 <= self.number_of_players <= 8:
            raise AssertionError(
                'The number of players should be between 4 and 8.'
            )
        elif self.game_stared:
            raise AssertionError(
                'The game has already started.'
            )
        else:
            # dealing cards.
            self.deck = Deck(self)
            self.deck.deal_cards()
            self.are_cards_shuffled = True

            # generate roles.
            roles = self.generate_roles()
            for player_id in self.players.keys():
                self.players[player_id].assign_role(roles.pop(0))

            # selecting pincher
            self.pincher = random.choice(list(self.players.keys()))

            self.game_stared = True

    @property
    def number_of_players(self):
        return len(self.players)

    @property
    def phase(self):
        return self.__phase

    @phase.setter
    def phase(self, phase: int):
        assert 1 <= phase <= 4
        self.__phase = phase

    @property
    def step(self):
        return self.__step

    @step.setter
    def step(self, step: int):
        assert 1 <= step <= self.number_of_players + 1
        self.__step = step

    def get_winning_team(self) -> Union[None, str]:
        """
        Get the winning team.
        
        Returns: Union[None, str]
            the winning team
        """
        if isinstance(self.winning_team, Role):
            return self.winning_team.value
        return None

    def get_pincher_name(self) -> Union[None, str]:
        """
        Get the pincher's name.

        Returns: Union[None, str]
            the pincher's name if existent.
        """
        if self.pincher is not None:
            return self.players[self.pincher].name
        else:
            return None

    def get_player_cards(self,
                         player_id: str) -> Dict[str, int]:
        """
        Get the player's hand.

        Args:
            player_id: the player's id.

        Returns: Dict[str, int]
            the player's cards.
        """
        return self.players[player_id].get_cards()

    def generate_roles(self) -> List['Role']:
        """Generate player roles.

        Returns: List[Role]
             A list of shuffled roles.
        """
        roles = ROLE_MAPPING[self.number_of_players][Role.SHERLOCK] * [Role.SHERLOCK] + \
                ROLE_MAPPING[self.number_of_players][Role.MORIARTY] * [Role.MORIARTY]
        random.shuffle(roles)
        return roles

    def get_player_role(self,
                        player_id: str) -> str:
        """
        Get the player's role
        Args:
            player_id: the player's role.

        Returns: str
            the player's role.
        """
        assert player_id in self.players.keys()
        return self.players[player_id].get_role()

    def legal_cards_per_hand(self) -> int:
        """"""
        return 6 - self.phase

    def update_board(self, card: 'Card') -> None:
        """"""
        self.board[card] += 1

    def remaining_cards(self):
        """Get remaining cards."""
        return 5 * self.number_of_players - sum([self.board[card] for card in self.board.keys()])

    def is_game_over(self) -> Union[bool, 'Role']:
        """"""
        if self.board[Card.DEFUSE] == self.number_of_players:
            return Role.SHERLOCK
        elif self.board[Card.BOMB] == 1 or (
                self.board[Card.DEFUSE] < self.number_of_players and self.remaining_cards() == self.number_of_players
        ):
            return Role.MORIARTY
        return False

    def shuffle_player_hands(self):
        """"""
        for player_id in self.players.keys():
            self.players[player_id].shuffle_hand()

    def update_hand_history(self):
        """"""
        for player_id in self.players.keys():
            self.players[player_id].update_hand_history()

    def is_pinch_legal(self,
                       pincher: str,
                       target: str,
                       card_id: int) -> bool:
        """Check whether a pinch is legal.

        Args:
            pincher: the pincher's id.
            target: the pinchee's id.
            card_id: the card id.

        Returns: bool
            `True` if pinch is legal. `False` otherwise.
        """
        if self.pincher != target and self.pincher == pincher and target in self.players.keys() and (
                0 <= card_id < len(self.players[target].hand)) and not self.game_over:
            return True
        return False

    def pinch_card(self,
                   pincher: str,
                   target_name: str,
                   card_id: int) -> Union[Card, None]:
        """A pincher chooses to pinch another player's card.

        Args:
            pincher: the pincher's id.
            target_name: the pinchee's name.
            card_id: the card id.

        Returns:
            Union[Card, None]
        """
        target_id = None
        for player_id in self.players.keys():
            if target_name == self.players[player_id].name:
                target_id = self.players[player_id].id
        if target_id is None:
            raise ValueError("The target's name does not exist in the current game.")
        if self.is_pinch_legal(pincher, target_id, card_id):
            pinched_card = self.players[target_id].hand.pop(card_id)
            self.step += 1
            self.update_hand_history()
            self.update_board(pinched_card)
            self.pincher = target_id
            game_over = self.is_game_over()
            if game_over:
                self.game_over = True
                self.winning_team = game_over
            elif self.step == self.number_of_players + 1:
                self.deck.refill()
                self.phase += 1
                self.step = 1
                self.deck.deal_cards()
            return pinched_card.value
        elif self.game_over:
            raise ValueError('The game is over!')
        else:
            raise ValueError('The demanded pinch move is illegal!')

    def state(self) -> Dict:
        """
        Export game state.
        Returns:
            Dict
        """
        state = {
            "gameStarted": self.game_stared,
            "numberOfPlayers": self.number_of_players,
            "phase": self.phase,
            "step": self.step,
            "board": {
                "secure": self.board[Card.SECURE],
                "defuse": self.board[Card.DEFUSE],
                "bomb": self.board[Card.BOMB]
            },
            "playerNames": self.player_names,
            "playerCards": {
                player.name: len(player.hand) for player in self.players.values()
            },
            "pincher": self.get_pincher_name(),
            "winningTeam": self.get_winning_team()
        }
        return state

def main():
    game = Game()
    game.create_player('Fabien')
    game.create_player('Oussama')
    game.create_player('Rémi')
    game.create_player('Lucas')
    game.create_player('Fanny')
    game.start()
    game.state()


if __name__ == '__main__':
    main()
