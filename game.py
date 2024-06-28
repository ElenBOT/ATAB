"""game utilities"""

import numpy as np

__all__ = [
    'coord2ij',
    'ij2coord',
    'Piece',
    'Board',
    'put_assassin',
    'put_sniper',
    'put_warrior',
    'put_defender',
]

def coord2ij(coord) -> tuple[int, int]:
    """convert chess coordinate to np array index"""
    return 8 - int(coord[1]), ord(coord[0]) - ord('a')
def ij2coord(ij) -> str:
    """convert np array index to chess coordinate"""
    return chr(ord('a') + ij[1]) + str(8 - ij[0])


class Piece:
    """For a piece object that stores some information"""
    def __init__(self):
        self.side:str = None
        self.classtype:str = None
        self._movement:np.array = np.zeros([3, 3])
        self._movealong:np.array = np.zeros([3, 3])

    def __repr__(self) -> str:
        return self.side + self.classtype

    @property
    def movement(self):
        return self._movement
    @movement.setter
    def movement(self, movement):
        self._movement = movement
    
    @property
    def movealong(self):
        return self._movealong
    @movealong.setter
    def movealong(self, movealong):
        self._movealong = movealong

def put_assassin(side, board, coord) -> None:
    """put an assassin piece on the board, at a coordinate."""
    assassin = Piece()
    assassin.side = side
    assassin.classtype = 'A'
    assassin.movealong = np.array([
        [1, 0, 1],
        [0, 0, 0],
        [1, 0, 1]
    ])
    board.board[coord2ij(coord)] = assassin
def put_sniper(side, board, coord):
    """put a sniper piece on the board, at a coordinate."""
    sniper = Piece()
    sniper.side = side
    sniper.classtype = 'S'
    sniper.movealong = np.array([
        [0, 1, 0],
        [1, 0, 1],
        [0, 1, 0]
    ])
    board.board[coord2ij(coord)] = sniper
def put_warrior(side, board, coord):
    """put a warrior piece on the board, at a coordinate."""
    warrior = Piece()
    warrior.side = side
    warrior.classtype = 'W'
    if side == '-':
        warrior.movement = np.array([
            [1, 1, 1],
            [0, 0, 0],
            [0, 0, 0]
        ])
    if side == '+':
        warrior.movement = np.array([
            [0, 0, 0],
            [0, 0, 0],
            [1, 1, 1]
        ])
    board.board[coord2ij(coord)] = warrior
def put_defender(side, board, coord):
    """put a defender piece on the board, at a coordinate."""
    defender = Piece()
    defender.side = side
    defender.classtype = 'D'
    defender.movement = np.array([
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1]
    ])
    board.board[coord2ij(coord)] = defender

class Board:
    def __init__(self):
        self.board = np.full((8, 8), None, dtype=object)
        self.turn = 0
        self.move_history = []
    def get_legal_moves(self, coord):
        legal_moves = np.full((8, 8), False, dtype=bool)
        selecti, selectj = coord2ij(coord)
        piece = self.board[selecti, selectj]

        def has_piece(i, j):
            if self.board[i, j] != None:
                return True
            else:
                return False
        def is_teammate(i, j):
            if self.board[i, j].side == piece.side:
                return True
            else:
                return False
        def in_board(i, j):
            if i < 0 or i > 7 or j < 0 or j > 7:
                return False
            else:
                return True

        # movement
        for a in range(3):
            for b in range(3):
                if a == 1 and b == 1: continue
                i, j = selecti + a - 1, selectj + b - 1
                if i < 0 or i > 7 or j < 0 or j > 7: continue
                if piece.movement[a, b]:
                    if has_piece(i, j) and is_teammate(i, j):
                        legal_moves[i, j] = False
                    else:
                        legal_moves[i, j] = True
        # movealong
        def walk(i, j, dirc, step):
            """return `wall`, `teammate`, `enemy`, `empty`."""    
            desi, desj = i + dirc[0] * step, j + dirc[1] * step
            if desi < 0 or desi > 7 or desj < 0 or desj > 7:
                return 'wall'
            elif has_piece(desi, desj) and is_teammate(desi, desj):
                return 'teammate'
            elif has_piece(desi, desj) and not is_teammate(desi, desj):
                return 'enemy'
            else:
                return 'empty'
        dirc_along =  {
            (0, 0): (-1, -1), # LU
            (0, 1): (-1,  0), # U
            (0, 2): (-1, +1), # RU
            (1, 0): ( 0, -1), # L
            (1, 2): ( 0, +1), # R
            (2, 0): (+1, -1), # LD
            (2, 1): (+1,  0), # D
            (2, 2): (+1, +1), # RD
        }
        for a in range(3):
            for b in range(3):
                if piece.movealong[a, b]:
                    dirc = dirc_along[a, b]
                    for step in range(1, 8):
                        desi, desj = selecti + dirc[0]*step, selectj + dirc[1]*step
                        if not in_board(desi, desj): 
                            break
                        elif not has_piece(desi, desj):
                            legal_moves[desi, desj] = True
                        else:
                            legal_moves[desi, desj] = True
                            break

        # bottom line rule
        if (piece.side == '+' and coord[1] == '8') or\
            (piece.side == '-' and coord[1] == '1'):
            for dirc in [ (0, -1), (0, +1) ]:
                for step in range(1, 8):
                    desi, desj = selecti + dirc[0]*step, selectj + dirc[1]*step
                    if not in_board(desi, desj): 
                        break
                    elif not has_piece(desi, desj):
                        legal_moves[desi, desj] = True
                    elif is_teammate(desi, desj):
                        legal_moves[desi, desj] = True
                        break
                    else:
                        legal_moves[desi, desj] = False         
                           
        # top line rule
        for a in range(8):
            if (piece.side == '-' and 
                legal_moves[0, a] == True and
                has_piece(0, a) and 
                not is_teammate(0, a)
            ):
                legal_moves[0, a] = False
            if (piece.side == '+' and 
                legal_moves[7, a] == True and
                has_piece(7, a) and 
                not is_teammate(7, a)
            ):
                legal_moves[7, a] = False

        return legal_moves
    
    def make_move(self, coord1, coord2):
        # get piece object
        piece1 = self.board[coord2ij(coord1)]
        piece2 = self.board[coord2ij(coord2)]
        # store move history
        move = (coord1, coord2, piece2)
        self.move_history.append(move)
        # make move
        self.board[coord2ij(coord2)] = piece1
        if piece1.side == piece2.side:
            self.board[coord2ij(coord1)] = piece2
        else:
            self.board[coord2ij(coord1)] = None
        # update turn
        self.turn += 1
    def undo(self):
        self.turn -= 1
        coord1, coord2, piece2 = self.move_history[self.turn]
        piece1 = self.board[coord2ij(coord2)]
        self.board[coord2ij(coord1)] = piece1
        self.board[coord2ij(coord2)] = piece2

    def print_board(self, legal_moves = np.full((8, 8), False, dtype=bool)):
        print('|  a |  b |  c |  d |  e |  f |  g |  h |')
        print('--------------------------------------------')
        for row, a in zip(self.board, np.arange(8)):
            print('| ', end = '')
            for box, b in zip(row, np.arange(8)):
                if legal_moves[a, b]:
                    end = '*| '
                else:
                    end = ' | '
                if box == None:
                    print('..', end=end)
                else:
                    print(box, end=end)
            print(8-a, end = '')
            print('\n--------------------------------------------')