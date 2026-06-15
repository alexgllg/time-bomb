import os

import flask
from flask import abort, jsonify, request
from flask_cors import CORS

from typing import Dict, Optional

from back.src.game import Game

app = flask.Flask(__name__)
CORS(app)
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False') == 'True'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())

ROOMS: Dict[str, 'Game'] = dict()
GAME_ERROR_MESSAGE = 'Error: The provided game id does not correspond to any game.'
PLAYER_ERROR_MESSAGE = 'Error: The given player id does not exist in the requested game.'


def _is_request_valid(
        game_id: str,
        player_id: Optional[str] = None
):
    """
    Check whether the game and player ids are valid.

    Args:
        game_id: the game id.
        player_id: the player id.

    Returns:
        Abort if request is not valid i.e. game id and/or player id does not exist.
    """
    if game_id not in ROOMS:
        abort(400, GAME_ERROR_MESSAGE)
    elif player_id is not None and player_id not in ROOMS[game_id].players:
        abort(400, PLAYER_ERROR_MESSAGE)


@app.route('/api/games', methods=['POST'])
def api_create_game():
    """
    Create a game.
    Returns: str
        the game id.
    """
    game = Game()
    ROOMS[game.id] = game
    return game.id


@app.route('/api/games', methods=['GET'])
def api_games():
    return jsonify({
        'gameIDs': [game.id for game in ROOMS.values()]
    })


@app.route('/api/games/<string:game_id>/players', methods=['POST'])
def api_create_player(
        game_id: str
):
    player_name = request.json['playerName']
    _is_request_valid(game_id)
    try:
        player_id = ROOMS[game_id].create_player(player_name)
        return player_id
    except Exception as exception_message:
        abort(400, str(exception_message))


@app.route('/api/games/<string:game_id>/players', methods=['GET'])
def api_get_players(
        game_id: str
):
    return jsonify({
        'players': {
            player.id: player.name for player in ROOMS[game_id].players.values()
        }
    })


@app.route('/api/games/<string:game_id>/start', methods=['POST'])
def api_start_game(
        game_id: str
):
    _is_request_valid(game_id)
    try:
        ROOMS[game_id].start()
        return 'started'
    except Exception as exception_message:
        abort(400, str(exception_message))


@app.route('/api/games/<string:game_id>/players/<string:player_id>/role', methods=['GET'])
def api_get_player_role(
        game_id: str,
        player_id: str
):
    _is_request_valid(game_id, player_id)
    role = ROOMS[game_id].get_player_role(player_id)
    if role is None:
        abort(400, 'Error: The roles have not been generated yet.')
    else:
        return role


@app.route('/api/games/<string:game_id>/players/<string:player_id>/cards', methods=['GET'])
def api_get_player_cards(
        game_id: str,
        player_id: str
):
    _is_request_valid(game_id, player_id)
    return ROOMS[game_id].get_player_cards(player_id)


@app.route('/api/games/<string:game_id>/players/<string:player_id>/pinch', methods=['POST'])
def api_pinch_card(
        game_id: str,
        player_id: str
):
    _is_request_valid(game_id, player_id)
    target_name = request.json['targetName']
    card_id = request.json['cardId']
    try:
        pinched_card = ROOMS[game_id].pinch_card(player_id, target_name, card_id)
        return pinched_card
    except Exception as exception_message:
        abort(400, str(exception_message))


@app.route('/api/games/<string:game_id>/state', methods=['GET'])
def api_get_game_state(
        game_id: str
):
    _is_request_valid(game_id)
    return jsonify(
        ROOMS[game_id].state()
    )


if __name__ == '__main__':
    app.run()
