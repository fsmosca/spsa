"""
duel.py

A module to handle non-uci engine vs engine matches.
"""


import subprocess
import argparse


def get_fen_list(fn):
    """
    Red fen file and return a list of fens.
    """
    fens = []
    with open(fn) as f:
        for lines in f:
            fen = lines.strip()
            fens.append(fen)

    return fens


def turn(fen):
    """
    Return side to move of the given fen.
    """
    side = fen.split()[1].strip()
    if side == 'w':
        return True
    return False


def save_game(outfn, fen, moves, e1, e2, start_turn, gres):
    # Todo: Add other pgn tags.
    with open(outfn, 'a') as f:
        f.write(f'[White "{e1 if start_turn else e2}"]\n')
        f.write(f'[Black "{e1 if not start_turn else e2}"]\n')
        f.write(f'[Result "{gres}"]\n')
        f.write(f'[FEN "{fen}"]\n\n')
        for m in moves:
            f.write(f'{m} ')
        f.write('\n\n')


def match(e1, e2, fen, param, output_game_file, movetimems=100):
    """
    Run an engine match between e1 and e2. Save the game and print result
    from e1 perspective.
    """
    move_hist = []

    pe1 = subprocess.Popen(e1, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           universal_newlines=True, bufsize=0)

    pe2 = subprocess.Popen(e2, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           universal_newlines=True, bufsize=0)

    eng = [pe1, pe2]

    for i, e in enumerate(eng):
        e.stdin.write('xboard\n')
        e.stdin.write('protover\n')
        for eline in iter(e.stdout.readline, ''):
            line = eline.strip()
            if 'done=1' in line:
                break

        # Set option to e1
        if i == 0:
            for k, v in param.items():
                e.stdin.write(f'option {k}={v}\n')
                print(f'set {k} to {v}')

    for e in eng:
        e.stdin.write('variant\n')
        e.stdin.write('new\n')
        e.stdin.write('post\n')

        # Todo: Use TC from parameter.
        e.stdin.write('level 0 0:15 0.1\n')

        e.stdin.write(f'setboard {fen}\n')

    num, side, move, line, game_end = 0, 0, None, '', False
    start_turn = turn(fen)
    gres, e1score = '', 0.0

    # Todo: Calculate remaining time from each engine.
    mt = int(movetimems/10)

    # Start the match.
    # Todo: Reverse starting side on same fen.
    while True:

        if num == 0:
            eng[side].stdin.write(f'time {mt}\n')
            eng[side].stdin.write(f'otim {mt}\n')
            eng[side].stdin.write('go\n')
        else:
            eng[side].stdin.write(f'time {mt}\n')
            eng[side].stdin.write(f'otim {mt}\n')
            move_hist.append(move)
            eng[side].stdin.write(f'{move}\n')

        num += 1

        for eline in iter(eng[side].stdout.readline, ''):
            line = eline.strip()

            # print(line)
            # sys.stdout.flush()

            # Todo: Add adjudication.
            # if not line.startswith('# '):
                # print(f'score: {line.split()[1]}')

            # Check end of game as claimed by engines.
            # Todo: Refactor
            if '1-0 {White mates}' in line:
                game_end = True
                e1score = 1.0 if start_turn else 0.0
                gres = '1-0'
                break
            elif '0-1 {Black mates}' in line:
                game_end = True
                e1score = 0.0 if start_turn else 0.0
                gres = '0-1'
                break
            elif '{Draw by repetition}' in line:
                game_end = True
                e1score = 0.5
                gres = '1/2-1/2'
                break
            elif '{Draw by fifty move rule}' in line:
                game_end = True
                e1score = 0.5
                gres = '1/2-1/2'
                break

            if 'move' in line:
                move = line.split('move ')[1]
                break

        if game_end:
            break

        side = not side

    save_game(output_game_file, fen, move_hist, 'e1', 'e2', start_turn, gres)

    for e in eng:
        e.stdin.write('quit\n')
        e.stdin.write('quit\n')

    return e1score


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--num-games', required=False,
                        help='number of games to play in a match, default=2',
                        type=int, default=2)
    parser.add_argument('--test-engine', required=True,
                        help='engine path/file or file of the engine\n'
                             'to be optmized')
    parser.add_argument('--base-engine', required=True,
                        help='engine path/file or file of the engine\n'
                             'as opponent to test engine')
    parser.add_argument('--start-fen', required=True,
                        help='fen file of startpos for the match')
    parser.add_argument('--param', required=True,
                        help='parameters to be optimized\n'
                             'Example:\n'
                             '"QueenOp 800 500 1500 1000, RookOp ..."\n'
                             'parname value min max factor')

    args = parser.parse_args()

    num_games = args.num_games
    e1 = args.test_engine
    e2 = args.base_engine
    fen_file = args.start_fen

    # Convert param to a dict
    param = {}
    for par in args.param.split(','):
        par = par.strip()
        sppar = par.split()  # Does not support param with space
        spname = sppar[0].strip()
        spvalue = int(sppar[1].strip())
        param.update({spname: spvalue})

    fens = get_fen_list(fen_file)
    test_engine_score = []

    # Todo: Add in command line.
    output_game_file = 'output_game.pgn'

    # Loop thru the fens and create a match.
    for i, fen in enumerate(fens):
        print(f'starting game {i+1} ...')
        res = match(e1, e2, fen, param, output_game_file)
        print(f'ended game {i + 1}')
        test_engine_score.append(res)
        if i >= num_games - 1:
            break

    # The match is done, print score perf of test engine.
    print(f'{sum(test_engine_score)/len(test_engine_score)}')


if __name__ == '__main__':
    main()
