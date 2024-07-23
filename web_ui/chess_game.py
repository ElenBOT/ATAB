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

PLAYER_BLUE = "0"


def serialize_board_state():
    """Serialize the current board state into a list of piece positions."""

    def get_piece_color(player_id):
        return "blue" if player_id == PLAYER_BLUE else "red"

    global board
    piece_positions = []
    for row in range(8):
        for col in range(8):
            piece = board.board[col, row]
            if piece != "n":
                piece_positions.append(
                    ((row, col), get_piece_color(piece[1]), piece[0])
                )
    return piece_positions


def get_valid_moves(position):
    """Retrieve valid moves information for the piece at the given position."""
    global board
    status, valid_moves = board.get_piece_valid_moves(position)
    if status == 0:
        valid_positions = [
            (row, col) for row in range(8) for col in range(8) if valid_moves[col, row]
        ]
        return True, valid_positions, ""
    elif status == 1:
        return False, None, "No piece exists at the given position."
    elif status == 2:
        return False, None, "The piece does not belong to the current player."
    else:
        return False, None, "Is the current player piece, but no valid place to move."


def create_board_response(
    success,
    move_details=None,
    *,
    piece_positions=None,
    turn=None,
    is_win=False,
    win_message=None,
):
    """Create board response in JSON format."""
    start_position = move_details[0][::-1] if move_details[0] is not None else None
    destination_position = (
        move_details[1][::-1] if move_details[1] is not None else None
    )
    return {
        "type": "board",
        "success": success,
        "piece_positions": piece_positions,
        "is_win": is_win,
        "win_message": win_message,
        "action_type": move_details[4],
        "start_position": start_position,
        "destination_position": destination_position,
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


@app.route("/session", methods=["POST"])
def connect_session():
    """Initialize the board or recover its status if it exists."""
    global board
    if board is None:
        board = game.Board()
    return jsonify(
        create_board_response(
            True,
            board.latest_move_details,
            piece_positions=serialize_board_state(),
            turn=board.current_turn,
        )
    )


@app.route("/new_game", methods=["POST"])
def start_new_game():
    """Start a new game and return the initial board state."""
    global board
    board = game.Board()
    return jsonify(
        create_board_response(
            True,
            board.latest_move_details,
            piece_positions=serialize_board_state(),
            turn=board.current_turn,
        )
    )


@app.route("/undo", methods=["POST"])
def undo_last_move():
    """Undo the last move and return the updated board state."""
    global board
    if board is None:
        return jsonify(create_board_response(False))
    success = board.undo()
    return jsonify(
        create_board_response(
            success,
            board.latest_move_details,
            piece_positions=serialize_board_state(),
            turn=board.current_turn,
        )
    )


@app.route("/select_grid", methods=["POST"])
def handle_select_grid():
    """Handle selecting a grid position and return valid moves."""
    global board
    if board is None:
        return jsonify(create_valid_moves_response(False, None, "No board instance"))
    data = request.json
    return jsonify(create_valid_moves_response(tuple(data["position"][::-1])))


@app.route("/move_piece", methods=["POST"])
def handle_move_piece():
    """Handle moving a piece to a new position and return the updated board state."""
    data = request.json
    global board
    success = board.make_move(
        tuple(data["start_position"][::-1]), tuple(data["destination_position"][::-1])
    )
    is_win = board.is_win
    win_message = (
        "Blue Win!"
        if is_win and str(board.win_player) == PLAYER_BLUE
        else "Red Win!" if is_win else None
    )
    return jsonify(
        create_board_response(
            success,
            board.latest_move_details,
            turn=board.current_turn,
            is_win=is_win,
            win_message=win_message,
        )
    )


@app.route("/")
def index():
    """Serve the index page."""
    return render_template("index1.html")


@app.route("/download_log")
def download_log():
    json_string = json.dumps(format_game_log(), separators=(",", ":"))
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
