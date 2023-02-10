import pygame
from pygame.locals import *

from random import randint, random
from math import *
from pygame.math import *

from Globals import *

import copy
import threading


class Othello(object):

    def __init__(self, world):

        self.world = world
        self.board = {}
        self.disks = {}
        self.currentPlayer = BLACK

        self.scores = [2, 2]
        self.timers = [TIME_LIMIT, TIME_LIMIT]
        self.started = False

        # generate the board
        self.square_image = pygame.image.load(
            "othello_square.png").convert_alpha()

        for i in range(1, 9):
            for j in range(1, 9):
                square = Square(world, self.square_image)
                square.coordinates = (i, j)
                square.position = Vector2(getPosition(square.coordinates))
                self.board[square.coordinates] = square

        self.disks[(4, 4)] = BLACK
        self.disks[(5, 5)] = BLACK
        self.disks[(5, 4)] = WHITE
        self.disks[(4, 5)] = WHITE

        self.labelfont = pygame.font.SysFont("arial", 24, True)
        self.playerfont = pygame.font.SysFont("arial", 40, True)

        self.black_disk_image = pygame.image.load(
            "black_disk.png").convert_alpha()
        self.black_w, self.black_h = self.black_disk_image.get_size()

        self.white_disk_image = pygame.image.load(
            "white_disk.png").convert_alpha()
        self.white_w, self.white_h = self.white_disk_image.get_size()

        self.cursor_image = pygame.image.load(
            "cursor_disk.png").convert_alpha()
        self.cursor_w, self.cursor_h = self.cursor_image.get_size()

        self.legal_moves = self.getMoves()

    def getCopy(self):
        newcopy = Othello(self.world)
        for disk in self.disks.items():
            newcopy.disks[disk[0]] = copy.copy(disk[1])

        newcopy.currentPlayer = copy.copy(self.currentPlayer)
        newcopy.scores = copy.copy(self.scores)
        newcopy.timers = copy.copy(self.timers)
        newcopy.legal_moves = copy.copy(self.legal_moves)

        return newcopy

    def render(self, surface):

        for square in self.board.items():
            square[1].render(surface)

        for disk in list(self.disks.items()):
            if disk[1] == BLACK:
                surface.blit(self.black_disk_image, Vector2(getPosition(
                    disk[0]) - Vector2(self.black_w/2, self.black_h/2)))
            elif disk[1] == WHITE:
                surface.blit(self.white_disk_image, Vector2(getPosition(
                    disk[0]) - Vector2(self.white_w/2, self.white_h/2)))

        # === Q1 START ===
        self.legal_moves = self.getMoves()
        for disks in self.legal_moves:
            surface.blit(self.cursor_image, Vector2(getPosition(
                disks) - Vector2(self.cursor_w/2, self.cursor_h/2)))
        # === Q1 END ===

        # Render the labels
        side_margin = LEFT_BORDER + TILE_SIZE/2
        column_label_y = TOP_BORDER + TILE_SIZE * 8 + 8
        for i in range(0, 8):
            label = self.labelfont.render(
                str(chr(ord('a') + i)).replace("'", ""), True, (255, 255, 255))
            w, h = label.get_size()
            surface.blit(
                label, (side_margin + TILE_SIZE * i - w/2, column_label_y))

        row_label_x = LEFT_BORDER + TILE_SIZE * 8 + 12
        for i in range(0, 8):
            label = self.labelfont.render(str(8 - i), True, (255, 255, 255))
            w, h = label.get_size()
            surface.blit(label, (row_label_x, TOP_BORDER +
                         TILE_SIZE/2 + TILE_SIZE * i - h/2))

        # Show the player to move
        if not self.gameOver():
            if self.currentPlayer == BLACK:
                label = self.playerfont.render("BLACK's turn", True, (0, 0, 0))
            else:
                label = self.playerfont.render(
                    "WHITE's turn", True, (255, 255, 255))

            surface.blit(label, (410, 50))

    def makeMove(self, move):

        if move is None:
            return None

        disks_to_flip = []
        opposing_disks = []

        for x_offset in range(-1, 2):
            for y_offset in range(-1, 2):
                if x_offset == 0 and y_offset == 0:
                    continue

                current_x = move[0]
                current_y = move[1]
                del opposing_disks[:]

                while True:
                    current_x += x_offset
                    current_y += y_offset

                    # look for first opposing disk
                    if len(opposing_disks) == 0:
                        if (current_x, current_y) in self.disks.keys() and self.disks[(current_x, current_y)] != self.currentPlayer:
                            opposing_disks.append((current_x, current_y))
                        else:
                            break

                    # follow line until own disk found
                    else:
                        if (current_x, current_y) in self.disks.keys():

                            # more opposing disks
                            if self.disks[(current_x, current_y)] != self.currentPlayer:
                                opposing_disks.append((current_x, current_y))

                            # own disk found - add to disks_to_flip
                            else:
                                disks_to_flip += opposing_disks
                                break

                        else:
                            break

        # Not a legal move
        if len(disks_to_flip) == 0:
            print("Illegal move!")
            return None

        # Legal move
        else:

            # Add new disk
            self.disks[move] = self.currentPlayer
            self.scores[self.currentPlayer] += 1

            # Flip disks
            for disk in disks_to_flip:
                self.disks[disk] = self.currentPlayer
                self.scores[self.currentPlayer] += 1
                self.scores[1 - self.currentPlayer] -= 1

            # Change player
            self.currentPlayer = 1 - self.currentPlayer

            # Update set of legal moves
            self.legal_moves = self.getMoves()

            return self.getCopy()

    def getMoves(self):

        move_list = []
        opposing_disks = []

        for x_coord in range(1, 9):
            for y_coord in range(1, 9):

                # square occupied - skip
                if (x_coord, y_coord) in self.disks.keys():
                    continue

                for x_offset in range(-1, 2):
                    for y_offset in range(-1, 2):

                        if x_offset == 0 and y_offset == 0:
                            continue

                        current_x = x_coord
                        current_y = y_coord
                        first_disk_found = False        # Is the adjacent disk the opponent's?
                        legal_move_found = False

                        while True:
                            current_x += x_offset
                            current_y += y_offset

                            # look for first opposing disk
                            if first_disk_found == False:
                                if (current_x, current_y) in self.disks.keys() and self.disks[(current_x, current_y)] != self.currentPlayer:
                                    first_disk_found = True
                                else:
                                    break

                            # follow line until own disk found
                            else:
                                if (current_x, current_y) in self.disks.keys():

                                    # more opposing disks
                                    if self.disks[(current_x, current_y)] != self.currentPlayer:
                                        continue

                                    # own disk found - add legal move to move_list
                                    else:
                                        move_list.append((x_coord, y_coord))
                                        legal_move_found = True
                                        break

                                else:
                                    break

                        if legal_move_found:
                            break

                    if legal_move_found:
                        break

        return move_list

    def gameOver(self):

        # === Q3 START ===

        # No legal moves, game ends
        self.legal_moves = self.getMoves()
        if len(self.legal_moves) == 0:
            return True
        # All positions filled - the game is over
        elif len(self.disks) == 64:
            return True
        # Time runs out
        elif self.world.othello.timers[self.world.othello.currentPlayer] <= 0:
            return True

        else:
            return False
        # === Q3 END ===


class World(object):

    def __init__(self):

        self.entities = {}
        self.entity_id = 0
        self.background = pygame.image.load(
            "grass_bkgrd_1024_768.png").convert_alpha()

        self.black_disk_image = pygame.image.load(
            "black_disk.png").convert_alpha()
        self.white_disk_image = pygame.image.load(
            "white_disk.png").convert_alpha()

        self.othello = Othello(self)

    def add_entity(self, entity):

        self.entities[self.entity_id] = entity
        entity.id = self.entity_id
        self.entity_id += 1

    def remove_entity(self, entity):

        del self.entities[entity.id]

    def get(self, entity_id):

        if entity_id in self.entities:
            return self.entities[entity_id]

        else:
            return None

    def process(self, time_passed):

        time_passed_seconds = time_passed / 1000.0
        for entity in list(self.entities.values()):
            entity.process(time_passed_seconds)

    def render(self, surface):

        # draw background and text
        surface.blit(self.background, (0, 0))

        # draw board
        self.othello.render(surface)

        # draw all entities
        for entity in self.entities.values():
            entity.render(surface)


class GameEntity(object):

    def __init__(self, world, name, image):

        self.world = world
        self.name = name
        self.image = image

        self.coordinates = (0, 0)
        self.position = Vector2(0, 0)

        self.id = 0

    def render(self, surface):

        x, y = self.position
        w, h = self.image.get_size()
        draw_pos = Vector2(self.position.x - w/2, self.position.y - h/2)

        surface.blit(self.image, draw_pos)


class Square(GameEntity):
    def __init__(self, world, image):

        GameEntity.__init__(self, world, "square", image)

    def render(self, surface):

        GameEntity.render(self, surface)


# Given coordinates, get the position of the centre of the tile corresponding to the coordinates
def getPosition(coordinates):

    return (LEFT_BORDER + (coordinates[0] - 1) * TILE_SIZE + TILE_SIZE / 2,
            (TOP_BORDER + TILE_SIZE * 8) - (coordinates[1] - 1) * TILE_SIZE - TILE_SIZE / 2)

# Given the position, get the coordinates of the tile at that positiom


def getCoordinates(position):
    return ((position[0] - LEFT_BORDER) // TILE_SIZE + 1, 8 - (position[1] - TOP_BORDER) // TILE_SIZE)


def evaluate(board, player):
    # === Q4 START -===
    eval = 0
    aiD = 0
    hD = 0
    aiC = 0
    hC = 0

    if board.gameOver():
        # current player lost
        if board.currentPlayer == player:
            eval = -10000 + len(board.disks)

        # current player won
        else:
            eval = 10000 - len(board.disks)

    for disk in board.disks:
        if board.disks.get(disk) == player:
            aiD += 1
            if disk == (1, 1) or disk == (1, 8) or disk == (8, 8) or disk == (8, 1):
                aiC += 1
        else:
            hD += 1
            if disk == (1, 1) or disk == (1, 8) or disk == (8, 8) or disk == (8, 1):
                hC += 1

    eval += (aiD+aiC*3) - (hD+hC*3)

    return eval

    # === Q4 END ===


def alphabeta(board, player, maxDepth, currentDepth, alpha, beta):

    # Check if we are done recursing
    if board.gameOver() or currentDepth == maxDepth:
        return evaluate(board, player), None

    # Otherwise bubble up values from below

    bestMove = None

    # Check each move
    for move in board.getMoves():

        newBoard = board.getCopy()
        newBoard.makeMove(move)

        # Recurse
        currentScore, currentMove = alphabeta(
            newBoard, 1 - player, maxDepth, currentDepth + 1, -beta, -alpha)

        # update alpha
        if -currentScore > alpha:
            alpha = -currentScore
            bestMove = move

        # If we are outside the bounds, then prune: exit immediately
        if alpha >= beta:
            return alpha, bestMove

    return alpha, bestMove


class AIThread (threading.Thread):
    def __init__(self, world, board):
        threading.Thread.__init__(self)
        self.world = world
        self.board = board

    def run(self):
        print("Starting thread")

        search_depth = 4
        ai_score = -inf
        ai_move = None

        ai_score, ai_move = alphabeta(
            self.board, self.world.othello.currentPlayer, search_depth, 0, -inf, inf)
        print("Score is ", ai_score)

        self.world.othello.makeMove(ai_move)

        print("Exiting thread")


def run():

    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE, 0)

    world = World()

    w, h = SCREEN_SIZE

    clock = pygame.time.Clock()

    game_started = False

    font = pygame.font.SysFont("arial", 24, True)

    while True:

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not world.othello.started:
                    global HUMAN
                    HUMAN = WHITE
                    world.othello.started = True
                    ai_thread = AIThread(world, world.othello)
                    ai_thread.start()

        if not world.othello.gameOver():

            mouse_coord = getCoordinates(pygame.mouse.get_pos())

            if pygame.mouse.get_pressed()[0] == True and world.othello.currentPlayer == HUMAN and mouse_coord in world.othello.legal_moves:
                world.othello.started = True
                newBoard = world.othello.makeMove(mouse_coord)
                if newBoard is not None:
                    ai_thread = AIThread(world, world.othello)
                    ai_thread.start()

            time_passed = clock.tick(30)

            if world.othello.started and not world.othello.gameOver():
                time_passed_seconds = time_passed / 1000
                # === Q2 START ===
                world.othello.timers[world.othello.currentPlayer] -= time_passed_seconds
                # === Q2 END ===

            world.render(screen)

        # Show scores
        black_score = font.render(
            "Black score: " + str(world.othello.scores[BLACK]), True, (0, 0, 0))
        screen.blit(black_score, (50, 50))
        white_score = font.render(
            "White score: " + str(world.othello.scores[WHITE]), True, (255, 255, 255))
        screen.blit(white_score, (840, 50))

        # Show timers
        black_timer = font.render(
            "Time Left: " + "{:.1f}".format(world.othello.timers[BLACK]), True, (0, 0, 0))
        screen.blit(black_timer, (50, 100))
        white_timer = font.render(
            "Time Left: " + "{:.1f}".format(world.othello.timers[WHITE]), True, (255, 255, 255))
        screen.blit(white_timer, (840, 100))

        if not world.othello.started:
            msg = world.othello.playerfont.render(
                "Hit <SPACE BAR> to play White", True, (255, 255, 0))
            w, h = msg.get_size()
            screen.blit(msg, (SCREEN_WIDTH/2 - w/2, SCREEN_HEIGHT - 80))

        if world.othello.gameOver():
            if world.othello.timers[WHITE] <= 0.:
                win_msg = world.othello.playerfont.render(
                    "BLACK WINS ON TIME! ", True, (0, 0, 0))
            elif world.othello.timers[BLACK] <= 0.:
                win_msg = world.othello.playerfont.render(
                    "WHITE WINS ON TIME! ", True, (255, 255, 255))
            elif world.othello.scores[BLACK] > world.othello.scores[WHITE]:
                win_msg = world.othello.playerfont.render(
                    "BLACK WINS! ", True, (0, 0, 0))
            elif world.othello.scores[BLACK] < world.othello.scores[WHITE]:
                win_msg = world.othello.playerfont.render(
                    "WHITE WINS!", True, (255, 255, 255))
            else:
                win_msg = world.othello.playerfont.render(
                    "DRAW", True, (127, 127, 127))

            w, h = win_msg.get_size()

            screen.blit(win_msg, (SCREEN_WIDTH/2 - w/2, 50))

        pygame.display.update()


if __name__ == "__main__":
    run()
