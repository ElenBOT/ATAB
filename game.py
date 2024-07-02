"""game utilities"""

import numpy as np

__all__ = [
    "Board",
]


def coord2readable(coord):
    return chr(ord("a") + coord[0]) + str(8 - coord[1])


def readable2coord(readable_coord):
    return ord(readable_coord[0]) - ord("a"), 8 - int(readable_coord[1])


class Board:
    """A chess game board

    | Piece name | code |
    | --- | --- |
    | assassin | a |
    | sniper | s |
    | warrior | w |
    | defender | d |
    """

    def __init__(self):
        self.board = np.full((8, 8), "n", dtype="U2")
        starting_positions = {
            "a": [(1, 0), (6, 0)],  # assassin
            "s": [(2, 0), (5, 0)],  # sniper
            "d": [(2, 1), (5, 1)],  # warrior
            "w": [(0, 1), (1, 1), (3, 1), (4, 1), (6, 1), (7, 1)],  # defender
        }
        for piece_code in starting_positions:
            for pos in starting_positions[piece_code]:
                self.board[pos] = f"{piece_code}0"
        for piece_code in starting_positions:
            for pos in starting_positions[piece_code]:
                self.board[pos[0], 7 - pos[1]] = f"{piece_code}1"
        self.turn = 0
        self.move_history = []

    def get_piece_valid_moves(self, coord):
        """Get piece valid moves"""
        movement = {
            "a0": np.array([[1, 0, 1], [0, 0, 0], [1, 0, 1]], dtype=bool),
            "s0": np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=bool),
            "w0": np.array([[0, 0, 0], [0, 0, 0], [1, 1, 1]], dtype=bool),
            "d0": np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=bool),
            "a1": np.array([[1, 0, 1], [0, 0, 0], [1, 0, 1]], dtype=bool),
            "s1": np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=bool),
            "w1": np.array([[1, 1, 1], [0, 0, 0], [0, 0, 0]], dtype=bool),
            "d1": np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=bool),
        }
        directions = {
            (0, 0): (-1, -1),  # LU
            (0, 1): (0, -1),  # U
            (0, 2): (+1, -1),  # RU
            (1, 0): (-1, 0),  # L
            (1, 2): (+1, 0),  # R
            (2, 0): (-1, +1),  # LD
            (2, 1): (0, +1),  # D
            (2, 2): (+1, +1),  # RD
        }
        def check_swap_level(p1):
            return p1[0] in ['s', 'a']
        
        has_piece = self.board != "n"
        legal_moves = np.zeros((8, 8), dtype=bool)
        selected_piece = self.board[coord]

        # No piece in the coordinate
        if not has_piece[coord]:
            return "no piece", legal_moves
        # The pieces that do not belong to the current player's turn
        if selected_piece[1] != str(self.turn):
            return "not the player turn", legal_moves

        # Assassins and snipers can move up to 7 spaces away; warriors and defenders can move 1 step away
        if selected_piece[0] in ("w", "d"):
            max_length = 1
        else:
            max_length = 7
        # Basic rules for piece movement
        for a in range(3): # Run through all available directions
            for b in range(3):
                if a == 1 and b == 1:
                    continue
                if not movement[selected_piece][a, b]:
                    continue
                direction = directions[a, b]
                for i in range(1, max_length + 1):
                    row = coord[0] + direction[0] * i
                    col = coord[1] + direction[1] * i
                    if (row < 0 or row > 7) or (col < 0 or col > 7):
                        break
                    if has_piece[row, col]:
                        if self.board[row, col][1] == str(self.turn):
                            # check piece level
                            if check_swap_level(selected_piece):
                                legal_moves[row, col] = True
                        else:
                            legal_moves[row, col] = True
                        break
                    else:
                        legal_moves[row, col] = True

        # bottom line rule
        if (self.turn == 0 and coord[1] == 7) or (self.turn == 1 and coord[1] == 0):
            for direction in [-1, 1]:
                for i in range(1, 8):
                    row = coord[0] + direction * i
                    col = coord[1]
                    if row < 0 or row > 7:
                        break
                    if has_piece[row, col]:
                        if self.board[row, col][1] == str(self.turn):
                            # check piece level
                            if check_swap_level(selected_piece):
                                legal_moves[row, col] = True
                        break
                    else:
                        legal_moves[row, col] = True

        # top line rule
        if self.turn == 0:
            buff_row = 7
        else:
            buff_row = 0
        for i in range(8):
            if has_piece[i, buff_row]:
                if self.board[i, buff_row][1] == str(1 - self.turn):
                    legal_moves[i, buff_row] = False

        return "", legal_moves

    def get_all_valid_moves(self):
        pass

    def make_move(self, selected, destination):
        if not self.get_piece_valid_moves(selected)[destination]:
            return False
        selected_piece = self.board[selected]
        destination_piece = self.board[destination]
        self.move_history.append(
            selected, destination, selected_piece, destination_piece
        )
        if destination_piece[1] == str(self.turn):
            self.board[destination] = selected_piece
            self.board[selected] = destination_piece
        else:
            self.board[destination] = selected_piece
        self.turn = 1 - self.turn

    def undo(self):
        self.turn = 1 - self.turn
        selected_coord, destination_coord, selected_piece, destination_piece = (
            self.move_history.pop()
        )
        self.board[selected_coord] = selected_piece
        self.board[destination_coord] = destination_piece

    def print_board(self):
        print("|  a |  b |  c |  d |  e |  f |  g |  h |")
        print("=" * 44)
        for row in range(8):
            print("| ", end="")
            for col in range(8):
                piece = self.board[col, row]
                if piece == "n":
                    print("..", end="")
                else:
                    print(piece, end="")
                print(" | ", end="")
            print(8 - row)
            print("-" * 44)
