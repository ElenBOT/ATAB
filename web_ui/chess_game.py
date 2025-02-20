import json
import os
import sys
import threading
import webbrowser
from datetime import datetime

from flask import Flask, Response, jsonify, render_template, request

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import game

app = Flask(__name__)
board = None


def serialize_board():
    """Serialize the current board state into a list of piece positions."""

    def piece_color(n):
        if n == "0":
            return "blue"
        else:
            return "red"

    global board
    pieces_pos = []
    for i in range(8):
        for j in range(8):
            piece = board.board[i, j]
            if piece != "n":
                pieces_pos.append(((j, i), piece_color(piece[1]), piece[0]))
    return pieces_pos


def get_valid_moves_info(coord):
    """Retrieve valid moves information for the piece at the given position."""
    global board
    status, valid_moves = board.get_piece_valid_moves(coord)
    if status == 0:
        pieces_pos = []
        for i in range(8):
            for j in range(8):
                if valid_moves[i, j]:
                    pieces_pos.append((j, i))
        return True, pieces_pos, ""
    elif status == 1:
        return False, None, "No piece exists at the given position."
    elif status == 2:
        return False, None, "The piece does not belong to the current player."
    else:
        return False, None, "Is the current player piece, but no valid place to move."


def format_board_response(success, piece_pos, is_win=False, win_msg=None):
    """Format board response in JSON format."""
    return {
        "type": "board",
        "success": success,
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


def log_format():
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


@app.route("/session", methods=["POST"])
def connect_session():
    """
    Initialize the board. Recover the board status if it exists; otherwise,
    create a new board.
    """
    global board
    if board is None:
        board = game.Board()
        return jsonify(format_board_response(True, serialize_board()))
    else:
        return jsonify(format_board_response(True, serialize_board()))


@app.route("/new_game", methods=["POST"])
def start_new_game():
    """Start a new game and return the initial board state."""
    global board
    board = game.Board()
    return jsonify(format_board_response(True, serialize_board()))


@app.route("/undo", methods=["POST"])
def undo_last_move():
    """Undo the last move and return the updated board state."""
    global board
    if board is None:
        return jsonify(format_board_response(False, None))
    success = board.undo()
    return jsonify(format_board_response(success, serialize_board()))


@app.route("/select_grid", methods=["POST"])
def handle_select_grid():
    """Handle selecting a grid position and return valid moves."""
    global board
    if board is None:
        return jsonify(format_valid_moves_response(False, None, "No board instance"))
    data = request.json
    valid, valid_moves, message = get_valid_moves_info(tuple(data["pos"][::-1]))
    return jsonify(format_valid_moves_response(valid, valid_moves, message))


@app.route("/move_piece", methods=["POST"])
def handle_move_piece():
    """Handle moving a piece to a new position and return the updated board state."""
    data = request.json
    global board
    success, is_win = board.make_move(
        tuple(data["selected_pos"][::-1]), tuple(data["target_pos"][::-1])
    )
    if is_win:
        if board.current_turn == 1:
            win_msg = "Blue Win!"
        else:
            win_msg = "Red Win!"
    else:
        win_msg = None
    return jsonify(format_board_response(success, serialize_board(), is_win, win_msg))


@app.route("/")
def index():
    """Serve the index page."""
    return render_template("index1.html")


@app.route("/download_log")
def download_log():
    json_string = json.dumps(log_format(), separators=(",", ":"))
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"game_log_{timestamp}.json"
    response = Response(json_string, mimetype="application/json")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


# @app.after_request
# def after_request(response):
#     """Add CORS headers to every response."""
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
#     # response.headers.add('Access-Control-Allow-Credentials', 'true')
#     return response


def open_browser():
    """Open the web browser to the chess game."""
    webbrowser.open_new("http://127.0.0.1:5000/")


if __name__ == "__main__":
    threading.Timer(1, open_browser).start()
    app.run(port=5000)
