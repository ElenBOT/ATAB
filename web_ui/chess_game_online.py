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
from flask_socketio import ConnectionRefusedError, SocketIO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import game

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = os.urandom(24)
board = None
player_sid = {}


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


def log_format():
    """
    Formats the game log into a structured JSON format for download.
    """
    metadata = {
        "description": "Chess game log",
        "data_format": {
            "name": "game_log",
            "type": "array",
            "description": "An array of game log entries",
            "value": {
                "name": "log_entry",
                "type": "array",
                "description": "A movement, each entry is a list of 4 items.",
                "value": [
                    {
                        "name": "start_position",
                        "type": "string",
                        "description": "Starting position of the piece on the board in chess notation (e.g., a1)",
                    },
                    {
                        "name": "end_position",
                        "type": "string",
                        "description": "Ending position of the piece on the board in chess notation (e.g., a1)",
                    },
                    {
                        "name": "selected_piece",
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
                        "name": "target_piece",
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
                ],
            },
        },
    }
    global board
    game_log = []
    for start_position, end_position, selected_piece, target_piece in board.move_log:
        game_log.append(
            (
                game.coord_to_readable(start_position),
                game.coord_to_readable(end_position),
                selected_piece,
                target_piece,
            )
        )
    return {"meta": metadata, "game_log": game_log}


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
    json_string = json.dumps(log_format(), separators=(",", ":"))
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
        session["player"] = 0
        return jsonify(success=True, token=auth.user_token["player1"])
    elif auth.verify_password(password, auth.user_passwords["player2"]):
        session["player"] = 1
        return jsonify(success=True, token=auth.user_token["player2"])
    else:
        return jsonify(success=False, message="Wrong password.")


@app.route("/send_sid", methods=["POST"])
def get_sid():
    """
    Route to receive and store Socket.IO session ID and associate it with player.
    """
    data = request.json
    sid = data["sid"]
    session["sid"] = sid
    player_sid[session["player"]] = sid
    if len(player_sid) == 2:
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
    """
    Initialize the board. Recover the board status if it exists; otherwise,
    create a new board.
    """
    global board
    if board is None:
        board = game.Board()
    return format_board_response(serialize_board(session["player"]))


@socketio.on("new_game")
def start_new_game():
    """Start a new game and return the initial board state."""
    global board
    board = game.Board()
    update_board()


@socketio.on("undo")
def undo_last_move():
    """Undo the last move and return the updated board state."""
    global board
    if board is None:
        return {"success": False}
    success = board.undo()
    if success:
        update_board()
        return {"success": True}
    else:
        return {"success": False}


@socketio.on("select_grid")
def handle_select_grid(data):
    """Handle selecting a grid position and return valid moves."""
    global board
    if board is None:
        return format_valid_moves_response(False, None, "No board instance")
    valid, valid_moves, message = get_valid_moves_info(tuple(data["pos"][::-1]))
    return format_valid_moves_response(valid, valid_moves, message)


@socketio.on("move_piece")
def handle_move_piece(data):
    """Handle moving a piece to a new position and return the updated board state."""
    if session["player"] == 0:
        selected_pos = player0_coord_transform(data["selected_pos"][::-1])
        target_pos = player0_coord_transform(tuple(data["target_pos"][::-1]))
    else:
        selected_pos = tuple(data["selected_pos"][::-1])
        target_pos = tuple(data["target_pos"][::-1])
    global board
    success, is_win = board.make_move(selected_pos, target_pos)
    if is_win:
        if board.current_turn == 1:
            win_msg = "Blue Win!"
        else:
            win_msg = "Red Win!"
    else:
        win_msg = None

    if success:
        update_board(is_win, win_msg)
    return {"success": success}


def player0_coord_transform(coord):
    """
    Transform coordinates for Player 0.
    """
    return 7 - coord[0], 7 - coord[1]


def serialize_board(player):
    """Serialize the current board state into a list of piece positions."""

    def piece_color(n):
        if n == "0":
            return "blue"
        else:
            return "red"

    global board
    pieces_pos = []
    if player == 0:
        board_view = np.rot90(board.board, 2)
    else:
        board_view = board.board
    for i in range(8):
        for j in range(8):
            piece = board_view[i, j]
            if piece != "n":
                pieces_pos.append(((j, i), piece_color(piece[1]), piece[0]))
    return pieces_pos


def update_board(is_win=False, win_msg=None):
    """
    Emit board update events to players with the current board state.
    """
    socketio.emit(
        "board-update",
        format_board_response(serialize_board(0), is_win, win_msg),
        to=player_sid[0],
    )
    socketio.emit(
        "board-update",
        format_board_response(serialize_board(1), is_win, win_msg),
        to=player_sid[1],
    )


def get_valid_moves_info(coord):
    """Retrieve valid moves information for the piece at the given position."""
    global board
    print("player:", session["player"], f", coord: {coord}")
    if board.current_turn != session["player"]:
        return False, None, "Not your turn."
    if session["player"] == 0:
        coord = player0_coord_transform(coord)
    status, valid_moves = board.get_piece_valid_moves(coord)
    if status == 0:
        pieces_pos = []
        if session["player"] == 0:
            valid_moves_view = np.rot90(valid_moves, 2)
        else:
            valid_moves_view = valid_moves
        for i in range(8):
            for j in range(8):
                if valid_moves_view[i, j]:
                    pieces_pos.append((j, i))
        return True, pieces_pos, ""
    elif status == 1:
        return False, None, "No piece exists at the given position."
    elif status == 2:
        return False, None, "The piece does not belong to the current player."
    elif status == 3:
        return False, None, "Is the current player piece, but no valid place to move."
    else:
        pass


def format_board_response(piece_pos, is_win=False, win_msg=None):
    """Format board response in JSON format."""
    return {
        "type": "board",
        "piece_pos": piece_pos,
        "is_win": is_win,
        "win_msg": win_msg,
    }


def format_valid_moves_response(valid, valid_moves, message):
    """Format valid moves response in JSON format."""
    return {
        "type": "valid_moves",
        "valid": valid,
        "valid_moves": valid_moves,
        "message": message,
    }


def open_browser():
    """Open the web browser to the chess game."""
    webbrowser.open_new("http://127.0.0.1:5000/")


if __name__ == "__main__":
    threading.Timer(1, open_browser).start()
    socketio.run(app, port=5000)
