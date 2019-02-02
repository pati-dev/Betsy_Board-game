#!/usr/bin/env python3
# betsy.py: "Modest" Betsy Player
# Ankit Mathur, Nitesh Jaswal, and Nishant Jain, October 2018


# Formulation of the Minimax problem:
# The heuristic of this function computes the maximum number of pieces aligned for each player and returns:
# +n if the max player is winning (as per the  rules of betsy game)
# -n if the min player is winning (as per the  rules of betsy game)
# +x, where x is the number of pieces aligned for max player provided that max player has equal or more number of pieces aligned than min player
# -x, where x is the number of pieces aligned for min player provided that min player has more number of pieces aligned than max player
# We have created a separate function to account for wrapping of columns such that the heuristic for columns is calculated after accounting for the rotating moves

from random import shuffle
from time import time
import sys

# rotate board
def rotate(board, col):
    change_col = board[col::n]
    s = list(board)

    # account for empty pieces on the board when rotating
    empty_places = change_col.count('.')
    s[col::n] = change_col[:empty_places] + change_col[-1:] + change_col[empty_places:-1]
    s= ''.join(s)

    return s

# drop a piece to the board
def drop(board, col, player):
    change_col = board[col::n]
    s = list(board)

    # account for empty pieces on the board when dropping
    empty_places = change_col.count('.')
    if empty_places > 0:
        s[col::n] = change_col[:(empty_places-1)] + player + change_col[empty_places:]
    s= ''.join(s)

    return s

def print_board(board):
    for row in range(0, n*(n+3), n):
        print(*board[row:row+n] )
    return None

# calculate alignment score for the given row/col/diagonal
def cal_score(ls, piece):
    s = []
    score = 0
    for i in range(len(ls)):
        if ls[i] == piece:
            score += 1
        elif ls[i] != '.':
            s += [score]
            score = 0
    s += [score]

    return max(s)

# extract top n rows from the board
def row_score(board, piece):
    s = []
    for row in range(0, n*n, n):
        start = row
        end = row + n
        step = 1
        current_row = board[start:end:step]

        # calculate score for each row
        s += [ cal_score(current_row, piece) ]
    return s

# extract top n columns from the board
def col_score(board, piece):
    s = []
    for col in range(0, n):
        start = col
        end = n * (n-1) + col + 1
        step = n
        current_col = board[start:end:step]

        # calculate score for each column
        s += [ cal_score(current_col, piece) ]
    return s

# extract both diagonals from the board
def diag_score(board, piece):
    s = []
    start = 0
    end = n * n
    step = n + 1
    d1 = board[start:end:step]

    # calculate score for first diagonal
    s += [ cal_score(d1, piece) ]

    start = n - 1
    end = n * (n-1) + 1
    step = n - 1
    d2 = board[start:end:step]

    # calculate score for second diagonal
    s += [ cal_score(d2, piece) ]
    return s

# wrap around the columns to account for rotating and calculate alignment scores
def wrapped_col_score(board, piece):
    s = []

    for col in range(0, n):

        # extract bottom 4 elements of the column
        start = n * (n-1) + col
        end = n * (n+3) + col
        step = n
        bottom_col = board[start:end:step]

        # extract top n elements of the column
        start = col
        end = n * (n-1) + col + 1
        step = n
        top_col = board[start:end:step]

        # verify if the column is eligible for wrapping
        if top_col.count('.') == n:
            current_col = top_col
        else:
            current_col = bottom_col + top_col + bottom_col[1:]

        # Calculate wrapped alignment score for the column
        s += [ cal_score(current_col, piece) ]

    return s

def heuristic(node):
    board, move, opponent = node
    player = 'o' if opponent == 'x' else 'x'

    # store row/wrapped_column/diagonal alignment scores for both players
    score = {'x': [], 'o': []}

    for piece in ['x', 'o']:
        score[piece] += row_score(board, piece)
        score[piece] += wrapped_col_score(board, piece)
        score[piece] += diag_score(board, piece)

    # extract the best alignment score among rows/wrapped_columns/diagonals
    # check for goal states and return suitable heuristic in favor of the max_player
    if max(score[opponent]) == n:
        if opponent == max_player:
            h = n
        else:
            h = -n
    elif max(score[player]) == n:
        if player == max_player:
            h = n
        else:
            h = -n
    # return an underestimated score in favor of max_player
    elif max(score[max_player]) >= max(score[min_player]):
        return max(score[max_player])
    else:
        return -max(score[min_player])

    # account for number of moves
    h += 1 / sum(i.isdigit() for i in move)

    return h

def is_goal(board):
    for piece in ['x', 'o']:
        if max(row_score(board, piece) + col_score(board, piece) + diag_score(board, piece)) == n:
            return 1
    return 0

def successors(node):
    (board, moves, opponent) = node
    player = 'x' if opponent == 'o' else 'o'
    succ = []

    # store all possible moves in a list and randomize to account for best possible gain from alpha-beta pruning
    possible_moves = []

    for move in ['drop', 'rotate']:
        for col in range(n):
            possible_moves += [ [move, col] ]
    shuffle(possible_moves)

    # generate successors based on each move
    for move, col in possible_moves:
        if move == 'drop':
            # verify if the player has enough pieces to make a drop move
            if board.count(player) < 0.5*n*(n+3):
                succ += [ ( drop(board, col, player), moves + ' ' + str(col+1), player ) ]
        else:
            # check if the column has more than one piece and then rotate
            if sum( [ board[col::n].count(player), board[col::n].count(opponent) ] ) > 1:
                succ += [ ( rotate(board, col), moves + ' ' + str( -(col+1) ), player ) ]
    return succ

def min_val(node, alpha, beta):
    global visited
    global board_count
    global depth

    (board, moves, opponent) = node
    player = 'x' if opponent == 'o' else 'o'

    # store the board and the number of moves taken to reach the board in the visited array
    visited[0] += [ board ]
    visited[1] += [ sum(i.isdigit() for i in moves) ]

    # check for terminal node based on time spent, goal state, and depth limit
    if (time() - t0 >= (time_limit * path) / (2.1 * n) ) or (is_goal(board)) or ( sum(i.isdigit() for i in moves) > depth_limit ):
        # increment number of boards checked on this branch
        board_count += 1
        return heuristic(node)
    else:
        for succ in successors(node):
            succ_board, succ_moves, succ_opponent = succ
            # check if successor is in visited state; if yes, then check if the current node reaches the visited board in lesser number of moves
            if ( succ_board not in visited[0] ) or ( ( succ_board in visited[0] ) and ( sum(i.isdigit() for i in succ_moves) < visited[1][ visited[0].index(succ_board) ] ) ):
                # increment the depth for current branch
                depth = max( ( sum(i.isdigit() for i in succ_moves ), depth ) )
                beta = min(beta, max_val(succ, alpha, beta))
                if alpha >= beta: return beta
        return beta

def max_val(node, alpha, beta):
    global visited
    global alpha_val
    global path
    global board_count
    global depth

    (board, moves, opponent) = node
    player = 'x' if opponent == 'o' else 'o'

    # store the board and the number of moves taken to reach the board in the visited array
    visited[0] += [ board ]
    visited[1] += [ sum(i.isdigit() for i in moves) ]

    # check for terminal node based on time spent, goal state, and depth limit
    if (time() - t0 >= (time_limit * path) / (2.1 * n) ) or (is_goal(board)) or ( sum(i.isdigit() for i in moves) > depth_limit ):
        # increment number of boards checked on this branch
        board_count += 1
        return heuristic(node)
    else:
        for succ in successors(node):
            succ_board, succ_moves, succ_opponent = succ
            # check if successor is in visited state; if yes, then check if the current node reaches the visited board in lesser number of moves
            if ( succ_board not in visited[0] ) or ( ( succ_board in visited[0] ) and ( sum(i.isdigit() for i in succ_moves) < visited[1][ visited[0].index(succ_board) ] ) ):
                # increment the depth for current branch
                depth = max( ( sum(i.isdigit() for i in succ_moves ), depth ) )
                alpha = max(alpha, min_val(succ, alpha, beta))
                if alpha >= beta: return alpha

            # check if the max function is returning back to the origin
            if ( sum(i.isdigit() for i in succ_moves) == 1 ):
                print("\nFinished checking successor number", path, "with move", int(succ_moves), "\nDuration:", time()- t0, "\n# of future states checked:", board_count, "\nMax depth checked:", depth)
                # increment number of branches checked
                path += 1
                # reset the number of boards checked for next branch
                board_count = 0
                # reset dpeth for next branch
                depth = 1
                # store current board if it has the largest alpha value
                if alpha > alpha_val[0]:
                    alpha_val = [ alpha, succ_board, int(succ_moves) ]

        return alpha

def alpha_beta_decision(initial_board):
    global visited
    global alpha_val
    global path
    global board_count
    global depth_limit
    global depth

    # initialize visited array
    visited = [[], []]

    # initialize a variable to store largest alpha values corresponding to each successor
    alpha_val = [-100, initial_board, '']
    # initialize var to store number of branches checked
    path = 1
    # initialize var to store number of boards checked
    board_count = 0
    # initialize var to store max depth that will be checked for any successor
    depth_limit = 50
    # initialize var to store depth checked for each successor
    depth = 1

    # initialize node var with (current board, moves required to reach board, and player who moved to generate this board)
    initial_node = (initial_board, '', min_player)

    v = max_val(initial_node, -100, 100)

    # return best possible successor board and the corresponding move
    return alpha_val[1], int(alpha_val[2])

# initialize current time
t0 = time()
# store sysarg vars
n, max_player, initial_board, time_limit = int(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4])
# initialize max and min players
min_player = 'x' if max_player == 'o' else 'o'

# apply Minimax algo with alpha-beta pruning
new_board, action = alpha_beta_decision(initial_board)

print("\nI consulted the Oracle. She commands you to drop a pebble in column", action) if action > 0 else print("I consulted the Oracle. She commands you to rotate column", -1 * action)
print("\nIn case your 'wise' human brain can't process this, your current state is:")
print_board(initial_board)
print("\nAfter making the recommended move, your state will be:")
print_board(new_board)
print("Total time taken:", time() - t0, "seconds")
print(action, new_board)
