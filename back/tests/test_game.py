"""Regression tests for the core game engine."""
import random
import unittest

from back.src.deck import Card
from back.src.game import Game


def _new_game(n_players):
    game = Game()
    for i in range(n_players):
        game.create_player(f'P{i}')
    game.start()
    return game


def _legal_targets(game, pincher_id):
    return [
        pid for pid, player in game.players.items()
        if pid != pincher_id and len(player.hand) > 0
    ]


def _play_randomly(game, rng):
    n_pinches = 0
    while not game.game_over and n_pinches < 1000:
        pincher_id = game.pincher
        target_id = rng.choice(_legal_targets(game, pincher_id))
        card_id = rng.randrange(len(game.players[target_id].hand))
        game.pinch_card(pincher_id, game.players[target_id].name, card_id)
        n_pinches += 1
    return n_pinches


class TestDeck(unittest.TestCase):

    def test_deck_size_matches_five_per_player(self):
        for n in range(4, 9):
            game = _new_game(n)
            total = len(game.deck.cards) + sum(
                len(p.hand) for p in game.players.values()
            )
            self.assertEqual(total, 5 * n, f'deck size mismatch for {n} players')


class TestRandomPlaythrough(unittest.TestCase):

    def test_random_games_terminate_for_every_player_count(self):
        for n in range(4, 9):
            for seed in range(20):
                random.seed(seed * 1000 + n)
                game = _new_game(n)
                n_pinches = _play_randomly(game, random)
                self.assertTrue(game.game_over, f'game did not finish for n={n}, seed={seed}')
                self.assertLess(n_pinches, 1000)
                self.assertIn(game.get_winning_team(), ('sherlock', 'moriarty'))
                # board never exceeds the total number of cards in the deck.
                board_total = sum(game.board.values())
                self.assertLessEqual(board_total, 5 * n)


class TestPinchCard(unittest.TestCase):

    def test_illegal_pinch_raises(self):
        game = _new_game(4)
        with self.assertRaises(ValueError):
            # a player cannot pinch themself.
            game.pinch_card(game.pincher, game.players[game.pincher].name, 0)

    def test_pinch_after_game_over_raises(self):
        game = _new_game(4)
        while not game.game_over:
            pincher_id = game.pincher
            target_id = random.choice(_legal_targets(game, pincher_id))
            game.pinch_card(pincher_id, game.players[target_id].name, 0)

        target_id = next(iter(game.players))
        with self.assertRaises(ValueError):
            game.pinch_card(game.pincher, game.players[target_id].name, 0)


if __name__ == '__main__':
    unittest.main()
