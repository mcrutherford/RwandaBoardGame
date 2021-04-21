"""
File: game.py
Author: Mark Rutherford
Created: 4/16/2021 8:32 PM
"""
import random
from typing import Type

from tokens import *


WALL_CHANCE = .2
VILLAGE_CHANCE = .1
HUTU_PLACEABLE_OBJECTS = [Roadblock, Roadblock, RadioStation]

MESSAGE_WAITING_FOR_TURN = 'Waiting for the other player to make their move'
MESSAGE_TUTSI_MAKE_TURN = 'Choose a location to move to'


class Game:
    def __init__(self, player_tutsi, player_hutu, board_size=25):
        self.player_tutsi = player_tutsi
        self.player_hutu = player_hutu
        self.board = []
        self.board_size = board_size
        self.is_done = False
        self.tutsi_game_message = MESSAGE_TUTSI_MAKE_TURN
        self.hutu_game_message = MESSAGE_WAITING_FOR_TURN
        self.days_remaining = 100
        self.turn = self.player_tutsi
        self.hutu_placing = Cell(-1, -1, Roadblock, self)

        for row in range(self.board_size):
            this_row = []
            for col in range(self.board_size):
                if random.random() < WALL_CHANCE:
                    this_row.append(Cell(row, col, Wall, self))
                elif random.random() < VILLAGE_CHANCE:
                    this_row.append(Cell(row, col, Village, self))
                else:
                    this_row.append(Cell(row, col, Empty, self))
            self.board.append(this_row)

        tutsi_location = random.randint(1, self.board_size**2)
        while tutsi_location > 0:
            for row in self.board:
                for cell in row:
                    if isinstance(cell.token, Empty):
                        tutsi_location -= 1
                    if tutsi_location == 0:
                        cell.token = TutsiPlayer(cell)
                        tutsi_location = -1

        self.refresh_board_visuals()

    def surrender_game(self, surrendering_person):
        if not self.is_done:
            self.is_done = True
            if surrendering_person == self.player_tutsi:
                self.tutsi_game_message = f"{surrendering_person.username} surrendered, realizing they were going to die anyways."
                self.hutu_game_message = f"{surrendering_person.username} surrendered, realizing they were going to die anyways."
            else:
                self.tutsi_game_message = f"{surrendering_person.username} gave up hunting {self.player_tutsi.username}. Someone else will kill them."
                self.hutu_game_message = f"{surrendering_person.username} gave up hunting {self.player_tutsi.username}. Someone else will kill them."
            self.refresh_board_visuals()

    def get_cell(self, row, col):
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            return self.board[row][col]
        return None

    def refresh_board_visuals(self):
        for row in self.board:
            for cell in row:
                cell.refresh_visuals()
                cell.can_move_here = []
        if not self.is_game_over():
            for move in self.hutu_placing.token.get_moves():
                if move.hutu_color is None:
                    if self.turn == self.player_hutu:
                        move.hutu_color = VALID_MOVE_COLOR
                move.can_move_here.append(self.hutu_placing)

            for row in self.board:
                for cell in row:
                    for move in cell.token.get_moves():
                        if cell.token.faction == 'tutsi' and move.tutsi_color is None:
                            if self.turn == self.player_tutsi:
                                move.tutsi_color = VALID_MOVE_COLOR
                        elif cell.token.faction == 'hutu' and move.hutu_color is None:
                            if self.turn == self.player_hutu:
                                move.hutu_color = VALID_MOVE_COLOR
                        move.can_move_here.append(cell)

            for row in self.board:
                for cell in row:
                    for influenced_cell in cell.token.get_influence():
                        if cell.token.faction == 'tutsi':
                            if influenced_cell.tutsi_color == VALID_MOVE_COLOR:
                                influenced_cell.tutsi_color = FRIENDLY_VALID_MOVE
                            elif influenced_cell.tutsi_color is None:
                                influenced_cell.tutsi_color = FRIENDLY_INFLUENCE_COLOR

                            if influenced_cell.hutu_color == VALID_MOVE_COLOR:
                                influenced_cell.hutu_color = ENEMY_VALID_MOVE
                            elif influenced_cell.hutu_color is None:
                                influenced_cell.hutu_color = ENEMY_INFLUENCE_COLOR
                        elif cell.token.faction == 'hutu':
                            if influenced_cell.tutsi_color == VALID_MOVE_COLOR:
                                influenced_cell.tutsi_color = ENEMY_VALID_MOVE
                            elif influenced_cell.tutsi_color is None:
                                influenced_cell.tutsi_color = ENEMY_INFLUENCE_COLOR

                            if influenced_cell.hutu_color == VALID_MOVE_COLOR:
                                influenced_cell.hutu_color = FRIENDLY_VALID_MOVE
                            if influenced_cell.hutu_color is None:
                                influenced_cell.hutu_color = FRIENDLY_INFLUENCE_COLOR

    def get_game_message(self, user):
        if user == self.player_tutsi:
            return self.tutsi_game_message
        else:
            return self.hutu_game_message

    def switch_turn(self):
        if not self.is_done:
            if self.turn == self.player_tutsi:
                self.turn = self.player_hutu
                self.hutu_placing = Cell(-1, -1, random.choice(HUTU_PLACEABLE_OBJECTS), self)
                self.hutu_game_message = f"Choose a location to place a {str(self.hutu_placing.token)}"
                self.tutsi_game_message = MESSAGE_WAITING_FOR_TURN
            else:
                self.turn = self.player_tutsi
                self.hutu_game_message = MESSAGE_WAITING_FOR_TURN
                self.tutsi_game_message = MESSAGE_TUTSI_MAKE_TURN
                for row in self.board:
                    for cell in row:
                        cell.token.tick_turn()

            self.days_remaining -= 1
            self.is_game_over()
        self.refresh_board_visuals()

    def make_move(self, user, row, col):
        user_faction = 'tutsi' if user == self.player_tutsi else 'hutu'
        if user == self.turn:
            cell = self.get_cell(row, col)
            if cell and isinstance(cell.token, Empty) or isinstance(cell.token, TutsiPlayer) or isinstance(cell.token, Village):
                for mover in cell.can_move_here:
                    if user_faction == mover.token.faction:
                        mover.token.make_move(row, col)
                        break

    def is_game_over(self):
        if self.is_done:
            return True
        elif self.days_remaining == 0:
            self.is_done = True
            self.tutsi_game_message = f'{self.player_tutsi.username} was one of the few survivors of the Rwandan Genocide'
            self.hutu_game_message = f'{self.player_tutsi.username} was one of the few survivors of the Rwandan Genocide'
            return True
        for row in self.board:
            for cell in row:
                if isinstance(cell.token, TutsiPlayer):
                    if len(cell.token.get_moves()) > 0:
                        return False
        self.is_done = True
        self.tutsi_game_message = f'{self.player_tutsi.username} was mercilessly slaughtered'
        self.hutu_game_message = f'{self.player_tutsi.username} was mercilessly slaughtered'
        return True


class Cell:
    def __init__(self, row, col, cell_token: Type[Token], game):
        self.row = row
        self.col = col
        self.game = game
        self.tutsi_color = None
        self.tutsi_image = None
        self.hutu_color = None
        self.hutu_image = None
        self.can_move_here = []
        self.token = cell_token(self)

    def refresh_visuals(self):
        self.tutsi_image = self.token.get_tutsi_image()
        self.tutsi_color = self.token.get_tutsi_color()
        self.hutu_image = self.token.get_hutu_image()
        self.hutu_color = self.token.get_hutu_color()

    def get_image(self, user):
        if user == self.game.player_tutsi:
            return self.tutsi_image
        else:
            return self.hutu_image

    def get_color(self, user):
        if user == self.game.player_tutsi:
            return self.tutsi_color or '#FFFFFF'
        else:
            return self.hutu_color or '#FFFFFF'


def main():
    pass


if __name__ == '__main__':
    main()
