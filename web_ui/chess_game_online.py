import hashlib
import json
import os
import secrets
import string
import sys
import threading
import webbrowser
from datetime import datetime

import numpy as np
from flask import Flask, Response, abort, jsonify, render_template, request, session
from flask_socketio import ConnectionRefusedError, SocketIO, join_room

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import game

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = os.urandom(24)
board = None
player_sid = [set(), set()]

PLAYER_BLUE_STR = "0"
PLAYER_BLUE_INT = 0
PLAYER_RED_STR = "1"
PLAYER_RED_INT = 1

class Authentication:
    """
    Handles user authentication including password hashing, verification,
    and token management.
    """

    def __init__(self):
        """
        Initializes two users with randomly generated passwords and tokens.
        """
        pwd1 = self.generate_password(8)
        pwd2 = self.generate_password(8)
        print(f"Player 1 password: {pwd1}\nPlayer 2 password: {pwd2}")
        self.user_passwords = {
            "player1": self.hash_password(pwd1),
            "player2": self.hash_password(pwd2),
        }
        self.user_token = {
            "player1": secrets.token_hex(8),
            "player2": secrets.token_hex(8),
        }

    def generate_password(self, pwd_len):
        """
        Generates a random password of specified length.
        """
        alphabet = string.ascii_letters + string.digits + "!#$%&*+<=>?@~"
        return "".join(secrets.choice(alphabet) for _ in range(pwd_len))

    def hash_password(self, password):
        """
        Hashes the provided password using PBKDF2 algorithm with SHA-256.
        """
        salt = secrets.token_bytes(16)
        hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return salt + hash

    def verify_password(self, password, stored_password):
        """
        Verifies if the provided password matches the stored hashed password.
        """
        salt = stored_password[:16]
        stored_password = stored_password[16:]
        hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return hash == stored_password

    def verify_token(self, token):
        """
        Verifies if the provided token is valid for any user.
        """
        for user, stored_token in self.user_token.items():
            if token == stored_token:
                return True
        return False


auth = Authentication()


def token_required(func):
    """
    Decorator function to enforce token authentication for specific routes.
    """

    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").split("Bearer ")[-1]
        if "null" == token or not auth.verify_token(token):
            abort(401, "Unauthorized")
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


def format_game_log():
    """
    Formats the game log into a structured JSON format for download.
    """
    metadata = {
        "title": "Chess Game Log",
        "description": "Representing the game log of a chess game, including move logs and final game state.",
        "data_format": {
            "game_log": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": [
                        {
                            "type": "string",
                            "description": "Starting position of the piece on the board in chess notation (e.g., a1)",
                        },
                        {
                            "type": "string",
                            "description": "Ending position of the piece on the board in chess notation (e.g., a1)",
                        },
                        {
                            "type": "string",
                            "description": (
                                "Type of the piece being moved, formatted as 'type_player'.\n"
                                "Type values:\n"
                                "  'a' - assassin\n"
                                "  'w' - warrior\n"
                                "  's' - sniper\n"
                                "  'd' - defender\n"
                                "Player values:\n"
                                "  '0' - Player 1\n"
                                "  '1' - Player 2\n"
                                "Example: 'a0' represents a Bishop of Player 1"
                            ),
                        },
                        {
                            "type": "string",
                            "description": (
                                "Type of the piece at the target position, formatted as 'type_player' or 'n' if no piece.\n"
                                "Type values:\n"
                                "  'a' - assassin\n"
                                "  'w' - warrior\n"
                                "  's' - sniper\n"
                                "  'd' - defender\n"
                                "Player values:\n"
                                "  '0' - Player 1\n"
                                "  '1' - Player 2\n"
                                "Example: 's1' represents a Rook of Player 2, 'n' represents an empty square"
                            ),
                        },
                        {
                            "type": "string",
                            "description": (
                                "The type of action taken by the piece.\n"
                                "Possible values:\n"
                                "  'move' - The piece moved to an empty square.\n"
                                "  'swap' - The piece swapped positions with another piece of the same player.\n"
                                "  'capture' - The piece captured an opponent's piece."
                            ),
                        },
                    ],
                    "additionalItems": False,
                },
            },
            "final_state": {
                "type": "object",
                "properties": {
                    "board": {
                        "type": "array",
                        "description": "The final configuration of the board",
                        "items": {"type": "array", "items": {"type": "string"}},
                    },
                    "is_win": {
                        "type": "boolean",
                        "description": "Indicates if a win condition has been met",
                    },
                    "win_player": {
                        "type": ["integer", "null"],
                        "description": "Specifies the player who won the game, if any",
                    },
                },
                "required": ["board", "is_win", "win_player"],
            },
        },
    }
    global board
    game_log = [
        (
            game.coord_to_readable(start_position),
            game.coord_to_readable(destination_position),
            start_piece,
            destination_piece,
            action_type,
        )
        for start_position, destination_position, start_piece, destination_piece, action_type in board.move_log
    ]
    final_state = {
        "board": board.board.tolist(),  # Convert the numpy array to a list for JSON serialization
        "is_win": board.is_win,
        "win_player": board.win_player,
    }
    return {"meta": metadata, "game_log": game_log, "final_state": final_state}


@app.route("/")
def index():
    """Serve the index page."""
    return render_template("index3.html")


@app.route("/download_log")
@token_required
def download_log():
    """
    Route to download the game log as a JSON file.
    """
    json_string = json.dumps(format_game_log(), separators=(",", ":"))
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"game_log_{timestamp}.json"
    response = Response(json_string, mimetype="application/json")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@app.route("/login", methods=["POST"])
def login():
    """
    Route to authenticate users based on provided password and issue tokens.
    """
    data = request.json
    password = data["password"]
    if auth.verify_password(password, auth.user_passwords["player1"]):
        session["player"] = PLAYER_BLUE_INT
        session["login"] = True
        return jsonify(success=True, token=auth.user_token["player1"])
    elif auth.verify_password(password, auth.user_passwords["player2"]):
        session["player"] = PLAYER_RED_INT
        session["login"] = True
        return jsonify(success=True, token=auth.user_token["player2"])
    else:
        return jsonify(success=False, message="Wrong password.")


@app.route("/check-login", methods=["GET"])
def check_login():
    if not session.get("login"):
        return jsonify(success=False)
    if session["player"] == PLAYER_BLUE_INT:
        return jsonify(success=True, token=auth.user_token["player1"])
    else:
        return jsonify(success=True, token=auth.user_token["player2"])


@app.route("/send-sid", methods=["POST"])
def get_sid():
    """
    Route to receive and store Socket.IO session ID and associate it with player.
    """
    data = request.json
    sid = data["sid"]
    session["sid"] = sid
    player_sid[session["player"]].add(sid)
    join_room(str(session["player"]), sid, "/")
    if (len(player_sid[PLAYER_BLUE_INT]) >= 1) and (len(player_sid[PLAYER_RED_INT]) >= 1):
        socketio.emit("player-ready", True)
    return "", 204


@socketio.on("connect")
def handle_connect():
    """
    Event handler for handling Socket.IO connection.
    """
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise ConnectionRefusedError("unauthorized!")

    token_ = token.split(" ")[1]
    if "null" == token_ or not auth.verify_token(token_):
        raise ConnectionRefusedError("unauthorized!")


@socketio.on("initialize_session")
def initialize_session():
    """Initialize the board or recover its status if it exists."""
    global board
    if board is None:
        board = game.Board()
    details = board.latest_move_details
    start_position, destination_position = coord_transform(
        details[0], details[1], session["player"]
    )
    return create_board_response(
        serialize_board_state(session["player"]),
        start_position,
        destination_position,
        board.current_turn,
    )


@socketio.on("new_game")
def start_new_game():
    """Start a new game and return the initial board state."""
    global board
    board = game.Board()
    update_board(board.current_turn)


@socketio.on("undo")
def undo_last_move():
    """Undo the last move and return the updated board state."""
    global board
    if board is None:
        return {"success": False}
    success = board.undo()
    if success:
        update_board(board.current_turn)
        return {"success": True}
    else:
        return {"success": False}


@socketio.on("select_grid")
def handle_select_grid(data):
    """Handle selecting a grid position and return valid moves."""
    global board
    if board is None:
        return create_valid_moves_response(False, None, "No board instance")
    return create_valid_moves_response(tuple(data["position"][::-1]))


@socketio.on("move_piece")
def handle_move_piece(data):
    """Handle moving a piece to a new position and return the updated board state."""
    if session["player"] == PLAYER_BLUE_INT:
        start_position = player0_coord_transform(data["start_position"][::-1])
        destination_position = player0_coord_transform(
            tuple(data["destination_position"][::-1])
        )
    else:
        start_position = tuple(data["start_position"][::-1])
        destination_position = tuple(data["destination_position"][::-1])
    global board
    success = board.make_move(start_position, destination_position)
    is_win = board.is_win
    win_message = (
        "Blue Win!" if is_win and board.win_player == PLAYER_BLUE_INT else "Red Win!" if is_win else None
    )

    if success:
        move_piece(board.current_turn, is_win, win_message)
    return {"success": success}


def player0_coord_transform(coord):
    """
    Transform coordinates for Player 0.
    """
    return 7 - coord[0], 7 - coord[1]


def coord_transform(start_position, destination_position, player):
    start_position_ = None if start_position is None else player0_coord_transform(start_position[::-1]) if player == PLAYER_BLUE_INT else start_position[::-1]
    destination_position_ = None if destination_position is None else player0_coord_transform(destination_position[::-1]) if player == PLAYER_BLUE_INT else destination_position[::-1]
    return start_position_, destination_position_


def serialize_board_state(player):
    """Serialize the current board state into a list of piece positions."""

    def get_piece_color(player_id):
        return "blue" if player_id == PLAYER_BLUE_STR else "red"

    global board
    piece_positions = []
    board_view = np.rot90(board.board, 2) if player == PLAYER_BLUE_INT else board.board

    for row in range(8):
        for col in range(8):
            piece = board_view[col, row]
            if piece != "n":
                piece_positions.append(
                    ((row, col), get_piece_color(piece[1]), piece[0])
                )
    return piece_positions


def update_board(turn):
    """
    Emit board update events to players with the current board state.
    """
    details = board.latest_move_details
    start_position0, destination_position0 = coord_transform(details[0], details[1], PLAYER_BLUE_INT)
    start_position1, destination_position1 = coord_transform(details[0], details[1], PLAYER_RED_INT)
    socketio.emit(
        "board-update",
        create_board_response(
            serialize_board_state(PLAYER_BLUE_INT), start_position0, destination_position0, turn
        ),
        to=PLAYER_BLUE_STR,
    )
    socketio.emit(
        "board-update",
        create_board_response(
            serialize_board_state(PLAYER_RED_INT), start_position1, destination_position1, turn
        ),
        to=PLAYER_RED_STR,
    )


def move_piece(turn, is_win, win_message):
    """
    Emit move piece events to players.
    """
    details = board.latest_move_details
    details_0 = coord_transform(details[0], details[1], PLAYER_BLUE_INT) + details[2:]
    details_1 = coord_transform(details[0], details[1], PLAYER_RED_INT) + details[2:]
    socketio.emit(
        "move-piece",
        create_move_response(details_0, turn, is_win, win_message),
        to=PLAYER_BLUE_STR,
    )
    socketio.emit(
        "move-piece",
        create_move_response(details_1, turn, is_win, win_message),
        to=PLAYER_RED_STR,
    )


def get_valid_moves(position):
    """Retrieve valid moves information for the piece at the given position."""
    global board
    if board.current_turn != session["player"]:
        return False, None, "Not your turn."
    if session["player"] == PLAYER_BLUE_INT:
        position = player0_coord_transform(position)
    status, valid_moves = board.get_piece_valid_moves(position)
    if status == 0:
        valid_moves_view = (
            np.rot90(valid_moves, 2) if session["player"] == PLAYER_BLUE_INT else valid_moves
        )
        valid_positions = [
            (row, col)
            for row in range(8)
            for col in range(8)
            if valid_moves_view[col, row]
        ]
        return True, valid_positions, ""
    elif status == 1:
        return False, None, "No piece exists at the given position."
    elif status == 2:
        return False, None, "The piece does not belong to the current player."
    elif status == 3:
        return False, None, "Is the current player piece, but no valid place to move."
    else:
        pass


def create_board_response(piece_positions, start_position, destination_position, turn):
    """Format board details response in JSON format."""
    return {
        "type": "board",
        "piece_positions": piece_positions,
        "start_position": start_position,
        "destination_position": destination_position,
        "turn": turn,
    }


def create_move_response(move_details, turn, is_win, win_message):
    """Format move response in JSON format."""
    return {
        "type": "move_details",
        "move_details": move_details,
        "is_win": is_win,
        "win_message": win_message,
        "turn": turn,
    }


def create_valid_moves_response(position):
    """Format valid moves response in JSON format."""
    valid, valid_positions, message = get_valid_moves(position)
    return {
        "type": "valid_moves",
        "valid": valid,
        "valid_moves": valid_positions,
        "message": message,
    }


def open_browser():
    """Open the web browser to the chess game."""
    webbrowser.open_new("https://127.0.0.1:5000/")


if __name__ == "__main__":
    threading.Timer(1, open_browser).start()
    socketio.run(app, host="0.0.0.0", ssl_context="adhoc")
    # socketio.run(app, host="0.0.0.0", port=5000)
    # socketio.run(app, host="0.0.0.0", port=5000, ssl_context=("cert.pem", "key.pem"))
    # socketio.run(app, host="0.0.0.0", port=5000, ssl_context=("cert.crt", "cert-key.key"))
