"""
====T Block====

     #
    ###

    0 1 0
    1 1 1

    1 0
    1 1
    1 0

    1 1 1
    0 1 0

    0 1
    1 1
    0 1

====I Block====

    ####

    1 1 1 1

    1
    1
    1
    1

====O Block====

    ##
    ##

    1 1
    1 1

====S Block=====

     ##
    ##

    0 1 1
    1 1 0

    1 0
    1 1
    0 1

====L Block=====

    #
    #
    ##

    1 0
    1 0
    1 1
"""

import math
import random
import os
import itertools

BEST_SCORE_FILE_NAME = "best_score"

block_shapes = [
    # T Block
    [[0, 1, 0],
     [1, 1, 1]],
    # L Block
    [[1, 0],
     [1, 0],
     [1, 1]],
    # S Block
    [[0, 1, 1],
     [1, 1, 0]],
    # O Block
    [[1, 1],
     [1, 1]],
    # I Block
    [[1], [1], [1], [1]]
]


class Board:
    """Board representation"""

    def __init__(self, height, width, random=None):
        self.height = height
        self.width = width
        self.random = random
        self.board = self._get_new_board()

        self.current_block_pos = None
        self.current_block = None
        self.next_block = None

        self.game_over = False
        self.score = None
        self.lines = None
        self.best_score = None
        self.level = None

    def start(self):
        """Start game"""

        self.board = self._get_new_board()

        self.current_block_pos = None
        self.current_block = None
        self.next_block = None

        self.game_over = False
        self.score = 0
        self.lines = 0
        self.level = 1
        self.best_score = 0#self._read_best_score()

        self._place_new_block()

    def is_game_over(self):
        """Is game over"""

        return self.game_over

    def rotate_block(self):
        rotated_shape = list(map(list, zip(*self.current_block.shape[::-1])))

        # if self._can_move(self.current_block_pos, rotated_shape):
        self.current_block.shape = rotated_shape
        self.current_block.rotation += 1
        self.current_block.rotation %= 4

    def move_block(self, direction, fejk=False):
        """Try to move block"""

        pos = self.current_block_pos
        if direction == "left":
            new_pos = [pos[0], pos[1] - 1]
        elif direction == "right":
            new_pos = [pos[0], pos[1] + 1]
        elif direction == "down":
            new_pos = [pos[0] + 1, pos[1]]
        else:
            raise ValueError("wrong directions")

        if self._can_move(new_pos, self.current_block.shape):
            self.current_block_pos = new_pos
            return True
        elif not fejk and direction == "down":
            self._land_block()
            self._burn()
            self._place_new_block()
        return False

    def drop(self, fejk=False):
        """Move to very very bottom"""

        while self.move_block("down", fejk):
            pass

    def drop_at(self, pos, rot, fejk=False):
        # TODO: gör ingenting om det är illegal för att slippa göra samma sak flera ggr
        # place in top mid
        size = Block.get_size(self.current_block.shape)
        col_pos = math.floor((self.width - size[1]) / 2)
        self.current_block_pos = [0, col_pos]

        # rotate rot times
        for _ in range(rot):
            self.rotate_block()

        # place at pos
        size = Block.get_size(self.current_block.shape)
        xpos = min(pos, self.width - size[1])
        self.current_block_pos = [0, xpos]

        self.drop(fejk=fejk)

    def _evaluate(self):
        self._land_block(remove=False)

        # rows eliminated
        rows_eliminated_index = self._burn(fejk=True)

        # landing height
        landing_height = self._landing_height(rows_eliminated_index)

        # transitions
        row_trans = self._row_transitions(rows_eliminated_index)
        col_trans = self._column_transitions(rows_eliminated_index)

        holes = self._holes(rows_eliminated_index)
        wells = self._well(rows_eliminated_index)

        self._land_block(remove=True)

        return (landing_height, len(rows_eliminated_index), row_trans, col_trans, holes, wells)

    def play_with_network(self, net, round_limit=1000):
        i = 0
        while not self.is_game_over() and i < round_limit:
            i += 1
            best_rot = None
            best_pos = None
            best_fit = None
            for pos in range(self.width):
                for rot in range(1, 5):
                    self.drop_at(pos, 1, fejk=True)
                    net_inp = self._evaluate()
                    fit = net.activate(net_inp)
                    if best_fit is None or fit[0] > best_fit:
                        best_fit = fit[0]
                        best_rot = rot
                        best_pos = pos

            self.drop_at(best_pos, best_rot, fejk=False)

        if i >= round_limit:
            print("--------round limit reached--------")

        return self.score

    def _landing_height(self, rows_eliminated_index):
        height_reduce = 0
        height_index = self.current_block_pos[0]
        for r in rows_eliminated_index:
            if r > height_index:
                height_reduce += 1
        return self.height - (height_reduce + height_index)

    def _row_transitions(self, rows_eliminated_index):
        transitions = 0
        for r in range(self.height):
            if r in rows_eliminated_index:
                continue
            row = self.board[r]
            for c in row[1:]:
                if row[c-1] != row[c]:
                    transitions += 1
        return transitions

    def _column_transitions(self, rows_eliminated_index):
        transitions = 0
        for c in range(self.width):
            for r in range(5, self.height):
                if r in rows_eliminated_index:
                    continue
                elif r-1 in rows_eliminated_index and self.board[r-2][c] != self.board[r][c]:
                    transitions += 1
                elif self.board[r-1][c] != self.board[r][c]:
                    transitions += 1
        return transitions

    def _holes(self, rows_eliminated_index):
        # TODO: definitionen av hole?
        holes = 0
        for c in range(self.width):
            found = False
            for r in range(4, self.height):
                if r in rows_eliminated_index:
                    continue
                elif self.board[r][c] == 1:
                    found = True
                elif found and self.board[r][c] == 0:
                    holes += 1
        return holes


    def _well(self, rows_eliminated_index):
        well = 0
        for c in range(self.width):
            for r in range(4, self.height):
                row = self.board[r]
                if r in rows_eliminated_index:
                    continue
                if row[c] is 1:
                    break
                if c is 0 and row[c] is 0 and row[c+1] is 1:
                    well += 1
                elif c is self.width -1 and row[c-1] is 1 and row[c] is 0:
                    well += 1
                elif row[c-1] is 1 and row[c] is 0 and row[c+1] is 1:
                    well += 1
        return well


    def get_heights(self):
        heights = [0]*self.width
        for i in range(self.width):
            for j in range(4, self.height):
                if self.board[j][i] == 1:
                    heights[i] = self.height - j
                    break
        return heights

    def _get_new_board(self):
        """Create new empty board"""

        return [[0 for _ in range(self.width)] for _ in range(self.height)]

    def _print_board(self):
        from pprint import pprint
        pprint(self.board)

    def _any_block_in_top_section(self):
        return any(x == 1 for x in itertools.chain.from_iterable(self.board[:4]))

    def _place_new_block(self):
        """Place new block and generate the next one"""

        if self.next_block is None:
            self.current_block = self._get_new_block()
            self.next_block = self._get_new_block()
        else:
            self.current_block = self.next_block
            self.next_block = self._get_new_block()

        size = Block.get_size(self.current_block.shape)
        col_pos = math.floor((self.width - size[1]) / 2)
        self.current_block_pos = [0, col_pos]

        if self._check_overlapping(self.current_block_pos, self.current_block.shape) or self._any_block_in_top_section():
            self.game_over = True
            # self._save_best_score()
        else:
            self.score += 5

    def _land_block(self, remove=False):
        """Put block to the board and generate a new one"""

        size = Block.get_size(self.current_block.shape)
        for row in range(size[0]):
            for col in range(size[1]):
                if self.current_block.shape[row][col] == 1:
                    self.board[self.current_block_pos[0] + row][self.current_block_pos[1] + col] = 0 if remove else 1

    def _burn(self, fejk=False):
        """Remove matched lines"""

        line_index = []
        for row in range(self.height):
            if all(col != 0 for col in self.board[row]):
                line_index.append(row)
                if not fejk:
                    for r in range(row, 0, -1):
                        self.board[r] = self.board[r - 1]
                    self.board[0] = [0 for _ in range(self.width)]
                    self.score += 100
                    self.lines += 1
                    if self.lines % 10 == 0:
                        self.level += 1
        return line_index

    def _check_overlapping(self, pos, shape):
        """If current block overlaps any other on the board"""

        size = Block.get_size(shape)
        for row in range(size[0]):
            for col in range(size[1]):
                if shape[row][col] == 1:
                    if self.board[pos[0] + row][pos[1] + col] == 1:
                        return True
        return False

    def _can_move(self, pos, shape):
        """Check if move is possible"""

        size = Block.get_size(shape)
        if pos[1] < 0 or pos[1] + size[1] > self.width \
                or pos[0] + size[0] > self.height:
            return False

        return not self._check_overlapping(pos, shape)

    def _save_best_score(self):
        """Save best score to file"""

        if self.best_score < self.score:
            with open(BEST_SCORE_FILE_NAME, "w") as file:
                file.write(str(self.score))

    @staticmethod
    def _read_best_score():
        """Read best score from file"""

        if os.path.exists(f"./{BEST_SCORE_FILE_NAME}"):
            with open(BEST_SCORE_FILE_NAME) as file:
                return int(file.read())
        return 0

    def _get_new_block(self):
        """Get random block"""

        r = self.random if self.random else random
        block = Block(r.randint(0, len(block_shapes) - 1))
        # block = Block(0)

        # flip it randomly
        if random.getrandbits(1):
            block.flip()

        return block


class Block:
    """Block representation"""

    def __init__(self, block_type):
        self.shape = block_shapes[block_type]
        self.color = block_type + 1
        self.block_type = block_type
        self.rotation = 0

    def flip(self):
        self.shape = list(map(list, self.shape[::-1]))

    def size(self):
        """Get size of the block"""

        return self.get_size(self.shape)

    @staticmethod
    def get_size(shape):
        """Get size of a shape"""

        return [len(shape), len(shape[0])]
