"""
File: tokens.py
Author: Mark Rutherford
Created: 4/20/2021 2:22 PM
"""
from flask import url_for
import math
import random


FRIENDLY_COLOR = '#00AA00'
ENEMY_COLOR = '#AA0000'
ENEMY_INFLUENCE_COLOR = '#F79E9E'
FRIENDLY_INFLUENCE_COLOR = '#9EF79E'
VALID_MOVE_COLOR = '#74C3ED'
ENEMY_VALID_MOVE = '#CDC3ED'
FRIENDLY_VALID_MOVE = '#74EDED'

RADIO_CAN_KILL_PLAYER = False


class Token:
    def __init__(self, cell):
        self.cell = cell
        self.move_deltas = ()
        self.influence_deltas = ()
        self.faction = None
        self.is_village = False
    
    def get_moves(self):
        if self.cell.game.is_done:
            return []
        row = self.cell.row
        col = self.cell.col
        possible_moves = []

        for move_delta_row, move_delta_col in self.move_deltas:
            loc_row = row + move_delta_row
            loc_col = col + move_delta_col
            move_cell = self.cell.game.get_cell(loc_row, loc_col)
            if move_cell is not None and (isinstance(move_cell.token, Empty) or isinstance(move_cell.token, TutsiPlayer) or isinstance(move_cell.token, Village)):
                possible_moves.append(move_cell)
        return possible_moves

    def get_influence(self):
        row = self.cell.row
        col = self.cell.col
        influence = []

        if self.influence_deltas == 'any':
            for row in self.cell.game.board:
                for cell in row:
                    influence.append(cell)
        else:
            for delta_row, delta_col in self.influence_deltas:
                loc_row = row + delta_row
                loc_col = col + delta_col
                loc_cell = self.cell.game.get_cell(loc_row, loc_col)
                if loc_cell is not None:
                    influence.append(loc_cell)
        return influence

    def tick_turn(self):
        pass

    def make_move(self, row, col):
        pass

    def get_hutu_image(self):
        return None

    def get_tutsi_image(self):
        return None

    def get_hutu_color(self):
        return None

    def get_tutsi_color(self):
        return None


class TutsiPlayer(Token):
    def __init__(self, cell):
        super().__init__(cell)
        self.move_deltas = ((-1, 0), (0, -1), (1, 0), (0, 1))
        self.faction = 'tutsi'

    def get_tutsi_image(self):
        return url_for('static', filename='images/player.png')

    def get_hutu_image(self):
        if self.cell.game.is_done:
            return url_for('static', filename='images/player.png')
        elif self.is_village:
            return url_for('static', filename='images/village.png')
        else:
            return None

    def get_tutsi_color(self):
        return FRIENDLY_COLOR

    def get_hutu_color(self):
        if self.cell.game.is_done:
            return ENEMY_COLOR
        else:
            return None

    def make_move(self, row, col):
        target_cell = self.cell.game.get_cell(row, col)
        if target_cell and target_cell in self.get_moves():
            become_village = target_cell.token.is_village
            is_organized_village = False
            if isinstance(target_cell.token, Village):
                is_organized_village = target_cell.token.is_organized
            target_cell.token = self
            if self.is_village:
                self.cell.token = Village(self.cell)
                self.is_village = False
            else:
                self.cell.token = Empty(self.cell)
            self.cell = target_cell
            if become_village:
                self.is_village = True

            if is_organized_village:
                self.cell.game.is_done = True
                self.cell.game.tutsi_game_message = f'{self.cell.game.player_tutsi.username} perished in a village engaging in organized violence'
                self.cell.game.hutu_game_message = f'{self.cell.game.player_tutsi.username} perished in a village engaging in organized violence'

            self.cell.game.switch_turn()


class Wall(Token):
    def __init__(self, cell):
        super().__init__(cell)

    def get_hutu_color(self):
        return '#000000'

    def get_tutsi_color(self):
        return '#000000'


class Empty(Token):
    def __init__(self, cell):
        super().__init__(cell)


class Roadblock(Token):
    def __init__(self, cell, can_move=True):
        super().__init__(cell)
        self.can_move = can_move
        self.faction = 'hutu'

    def __str__(self):
        return 'roadblock'

    def get_moves(self):
        if self.cell.game.is_done or not self.can_move:
            return []
        possible_moves = []
        for row in self.cell.game.board:
            for cell in row:
                if isinstance(cell.token, Empty) or isinstance(cell.token, TutsiPlayer):
                    possible_moves.append(cell)
        return possible_moves

    def make_move(self, row, col):
        target_cell = self.cell.game.get_cell(row, col)
        if target_cell and target_cell in self.get_moves():
            target_cell.token = Roadblock(target_cell, False)
            self.cell.game.switch_turn()

    def get_hutu_color(self):
        return FRIENDLY_COLOR

    def get_tutsi_color(self):
        return ENEMY_COLOR


class RadioStation(Token):
    def __init__(self, cell, can_move=True):
        super().__init__(cell)
        self.can_move = can_move
        self.faction = 'hutu'
        self.influence_deltas = []
        influence_range = 4.5
        for delta_x in range(-math.ceil(influence_range), math.ceil(influence_range)+1):
            for delta_y in range(-math.ceil(influence_range), math.ceil(influence_range)+1):
                if math.sqrt(delta_x**2 + delta_y**2) <= influence_range:
                    self.influence_deltas.append((delta_x, delta_y))

    def __str__(self):
        return 'radio station'

    def get_moves(self):
        if self.cell.game.is_done or not self.can_move:
            return []
        possible_moves = []
        for row in self.cell.game.board:
            for cell in row:
                possible_moves.append(cell)
        return possible_moves

    def make_move(self, row, col):
        target_cell = self.cell.game.get_cell(row, col)
        if target_cell and target_cell in self.get_moves():
            target_cell.token = RadioStation(target_cell, False)
            self.cell.game.switch_turn()

    def tick_turn(self):
        empty_influence = []
        for cell in self.get_influence():
            if isinstance(cell.token, Empty) or (isinstance(cell.token, TutsiPlayer) or (isinstance(cell.token, Village)) and RADIO_CAN_KILL_PLAYER):
                empty_influence.append(cell)

        if empty_influence:
            chosen_cell = random.choice(empty_influence)
            chosen_cell.token = Roadblock(chosen_cell, False)

    def get_hutu_image(self):
        return url_for('static', filename='images/radiostation.png')

    def get_tutsi_image(self):
        return url_for('static', filename='images/radiostation.png')

    def get_hutu_color(self):
        return FRIENDLY_COLOR

    def get_tutsi_color(self):
        return ENEMY_COLOR


class Village(Token):
    def __init__(self, cell):
        super().__init__(cell)
        self.move_deltas = [(0, 0)]
        self.is_organized = False
        self.is_village = True
        self.faction = 'hutu'

    def __str__(self):
        return "village"

    def make_move(self, row, col):
        target_cell = self.cell.game.get_cell(row, col)
        if target_cell == self.cell and not self.is_organized:
            self.is_organized = True
            self.cell.game.switch_turn()

    def get_moves(self):
        return [self.cell]

    def get_hutu_image(self):
        return url_for('static', filename='images/village.png')

    def get_tutsi_image(self):
        return url_for('static', filename='images/village.png')

    def get_hutu_color(self):
        if self.is_organized:
            return FRIENDLY_COLOR
        else:
            return None

    def get_tutsi_color(self):
        if self.is_organized and self.cell.game.is_done:
            return ENEMY_COLOR
        else:
            return None


def main():
    pass


if __name__ == '__main__':
    main()
