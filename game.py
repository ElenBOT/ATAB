"""
Chess Game 

This module serves as the core API of the game.

Classes:
--------
Board:
    Represents the chess board and manages game operations.

Functions:
----------
coord_to_readable(coord):
    Convert board coordinates to a readable format.

readable_to_coord(readable_coord):
    Convert readable format coordinates to board coordinates.

Example:
--------
board = Board()
"""

import numpy as np

__all__ = [
    "Board",
]


def coord_to_readable(coord):
    """
    Convert board coordinates to readable format.

    Parameters
    ----------
    coord : tuple of int
        A tuple representing board coordinates (x, y).

    Returns
    -------
    str
        Readable board coordinate.
    """
    return chr(ord('a') + coord[0]) + str(8 - coord[1])


def readable_to_coord(readable_coord):
    """
    Convert readable format coordinates to board coordinates.

    Parameters
    ----------
    readable_coord : str
        Readable board coordinate.

    Returns
    -------
    tuple of int
        A tuple representing board coordinates (x, y).
    """
    return ord(readable_coord[0]) - ord('a'), 8 - int(readable_coord[1])


class Board:
    """
    A chess game board.

    Piece types:
    - assassin (a)
    - sniper (s)
    - warrior (w)
    - defender (d)

    Empty square:
    - (n)
    """

    def __init__(self):
        """
        Initialize the chess board.
        """
        self.board = np.full((8, 8), 'n', dtype='U2')
        starting_positions = {
            'a': [(1, 0), (6, 0)],  # assassin
            's': [(2, 0), (5, 0)],  # sniper
            'd': [(2, 1), (5, 1)],  # warrior
            'w': [(0, 1), (1, 1), (3, 1), (4, 1), (6, 1), (7, 1)],  # defender
        }
        # Set initial positions for player 0
        for piece_code in starting_positions:
            for pos in starting_positions[piece_code]:
                self.board[pos] = f'{piece_code}0'
        # Set initial positions for player 1
        for piece_code in starting_positions:
            for pos in starting_positions[piece_code]:
                self.board[pos[0], 7 - pos[1]] = f'{piece_code}1'
        self.current_turn = 0  # Set initial turn to player 0
        self.move_log = []  # Initialize move history

    def get_piece_valid_moves(self, coord):
        """
        Get valid moves for a piece at a given position.

        Parameters
        ----------
        coord : tuple of int
            The position of the piece on the board.

        Returns
        -------
        tuple
            A tuple containing:
            - int: A code indicating the result of checking valid moves:
            - 0: Successful retrieval of valid moves.
            - 1: No piece exists at the given position.
            - 2: The piece does not belong to the current player.
            - 3: Is the current player piece, but no valid place to move.
            - np.array of bool
                A boolean array indicating valid moves.
        """
        movement = {
            'a0': np.array([[1, 0, 1], [0, 0, 0], [1, 0, 1]], dtype=bool),
            's0': np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=bool),
            'w0': np.array([[0, 0, 0], [0, 0, 0], [1, 1, 1]], dtype=bool),
            'd0': np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=bool),
            'a1': np.array([[1, 0, 1], [0, 0, 0], [1, 0, 1]], dtype=bool),
            's1': np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=bool),
            'w1': np.array([[1, 1, 1], [0, 0, 0], [0, 0, 0]], dtype=bool),
            'd1': np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=bool),
        }
        directions = {
            (0, 0): (-1, -1),  # Left Up
            (0, 1): (0, -1),  # Up
            (0, 2): (+1, -1),  # Right Up
            (1, 0): (-1, 0),  # Left
            (1, 2): (+1, 0),  # Right
            (2, 0): (-1, +1),  # Left Down
            (2, 1): (0, +1),  # Down
            (2, 2): (+1, +1),  # Right Down
        }

        def check_swap(piece):
            """Check if the piece can be swaps."""
            return piece[0] in ['s', 'a']

        piece_exists = (
            self.board != 'n'
        )  # Boolean array indicating if a piece exists at each position
        legal_moves = np.zeros((8, 8), dtype=bool)  # Initialize legal moves array
        selected_piece = self.board[coord]  # Get the piece at the given position

        # Check if no piece is at the position
        if not piece_exists[coord]:
            return 1, legal_moves  # no piece
        # Check if the piece belongs to the current player
        if selected_piece[1] != str(self.current_turn):
            return 2, legal_moves  # not the player turn

        # Determine maximum move length based on piece type
        # Assassins and snipers can move up to 7 spaces away; warriors and defenders can move 1 step away
        if selected_piece[0] in ('w', 'd'):
            max_length = 1
        else:
            max_length = 7

        # Calculate basic valid moves for the piece
        for a in range(3):  # Run through all available directions
            for b in range(3):
                if a == 1 and b == 1:  # Skip the piece's own position
                    continue
                if not movement[selected_piece][
                    a, b
                ]:  # Skip invalid movement directions
                    continue
                direction = directions[a, b]
                for i in range(1, max_length + 1):  # Run through all move length
                    row = coord[0] + direction[0] * i
                    col = coord[1] + direction[1] * i
                    if (row < 0 or row > 7) or (
                        col < 0 or col > 7
                    ):  # Check if out of bounds
                        break
                    if piece_exists[row, col]:  # Check if a piece exists in the square
                        if self.board[row, col][1] == str(
                            self.current_turn
                        ):  # Check if the piece belongs to the current player
                            if check_swap(
                                selected_piece
                            ):  # Check if the piece can swap
                                legal_moves[row, col] = True
                        else:
                            legal_moves[row, col] = True
                        break
                    else:
                        legal_moves[row, col] = True

        # Calculate valid moves from the bottom line rule
        if (self.current_turn == 0 and coord[1] == 0) or (
            self.current_turn == 1 and coord[1] == 7
        ):
            for direction in [-1, 1]:
                for i in range(1, 8):
                    row = coord[0] + direction * i
                    col = coord[1]
                    if row < 0 or row > 7:
                        break
                    if piece_exists[row, col]:
                        if self.board[row, col][1] == str(self.current_turn):
                            # check piece level
                            if check_swap(selected_piece):
                                legal_moves[row, col] = True
                        break
                    else:
                        legal_moves[row, col] = True

        # Check top line rule
        if self.current_turn == 0:
            buff_row = 0
        else:
            buff_row = 7
        for i in range(8):
            if piece_exists[i, buff_row]:
                if self.board[i, buff_row][1] == str(
                    1 - self.current_turn
                ):  # Check if the piece belongs to the opponent
                    legal_moves[i, buff_row] = False

        if legal_moves.any():
            return 0, legal_moves
        else:
            return 3, legal_moves

    def get_all_valid_moves(self):
        """
        Get all valid moves for the current player.
        """
        pass

    def make_move(self, start_position, end_position):
        """
        Make a move on the board.

        Parameters
        ----------
        start_position : tuple of int
            The starting position of the piece (row, col).
        end_position : tuple of int
            The destination position (row, col).

        Returns
        -------
        bool
            True if the move is valid and made, False otherwise.
        bool
            True if the current player has won the game after this move, False otherwise.
        """
        # Check if the start position has the player piece, and end position is valid
        if self.board[start_position] == 'n':
            return False, False
        if not self.get_piece_valid_moves(start_position)[1][end_position]:
            return False, False
        
        selected_piece = self.board[start_position]
        target_piece = self.board[end_position]
        self.move_log.append(
            (start_position, end_position, selected_piece, target_piece)
        )
        # Move the piece
        if target_piece == 'n':
            self.board[end_position] = selected_piece
            self.board[start_position] = 'n'
        elif target_piece[1] == str(self.current_turn):
            self.board[end_position] = selected_piece
            self.board[start_position] = target_piece
        else:
            self.board[end_position] = selected_piece
            self.board[start_position] = 'n'

        is_win = self.check_is_win(self.current_turn)
        self.current_turn = 1 - self.current_turn  # Switch the turn
        return True, is_win
    
    def check_is_win(self, player):
        """
        Check if the specified player has won the game.

        A player wins if they have at least two pieces on the opponent's bottom line.
        The top line for player 0 is row 7, and for player 1, it is row 0.

        Args:
            player (int): The player to check for a win condition. 0 or 1.

        Returns:
            bool: True if the player has won, False otherwise.
        """
        counts = 0
        if player == 0:
            top_line = 7
        else:
            top_line = 0
        for i in range(8):
            piece = self.board[i, top_line]
            if piece != 'n':
                if piece[1] == str(player):
                    counts += 1
                if counts == 2:
                    return True
        return False

    def undo(self):
        """
        Undo the last move made on the board.

        Returns
        -------
        bool
            True if the last move was successfully undone, False if there are no moves to undo.
        """
        if len(self.move_log) != 0:
            self.current_turn = 1 - self.current_turn
            start_position, end_position, piece, target_piece = self.move_log.pop()
            self.board[start_position] = piece
            self.board[end_position] = target_piece
            return True
        else:
            return False

    def print_board(self):
        """
        Print the current state of the board.
        """
        print('|  a |  b |  c |  d |  e |  f |  g |  h |')
        print('=' * 44)
        for row in range(8):
            print('| ', end='')
            for col in range(8):
                piece = self.board[col, row]
                if piece == 'n':
                    print('..', end='')
                else:
                    print(piece, end='')
                print(' | ', end='')
            print(8 - row)
            print('-' * 44)
