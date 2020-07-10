"""
duel.py

A module to handle non-uci engine vs engine matches.
"""


import subprocess
import argparse
import time
import random


class Timer:
    def __init__(self, base_time, inc_time):
        """
        The time unit is in ms (milliseconds)
        """
        self.base_time = base_time
        self.inc_time = inc_time
        self.rem_time = self.base_time + self.inc_time

    def update(self, elapse):
        """
        This is called after every engine move is completed.
        """
        self.rem_time -= elapse
        self.rem_time += self.inc_time

    def is_zero_time(self):
        return True if self.rem_time <= 0 else False

    def rem_cs(self):
        return self.rem_time // 10


def get_fen_list(fn, is_rand=False):
    """
    Red fen file and return a list of fens.
    """
    fens = []
    with open(fn) as f:
        for lines in f:
            fen = lines.strip()
            fens.append(fen)

    if is_rand:
        random.shuffle(fens)

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
    with open(outfn, 'a') as f:
        f.write(f'[Event "Optimization test"]\n')
        f.write(f'[White "{e1 if start_turn else e2}"]\n')
        f.write(f'[Black "{e1 if not start_turn else e2}"]\n')
        f.write(f'[Result "{gres}"]\n')
        f.write(f'[FEN "{fen}"]\n\n')
        for m in moves:
            f.write(f'{m} ')
        f.write('\n\n')


def adjudicate_win(score_history, win_adj_move_num, side):
    ret, gres, e1score = False, '*', 0.0

    if len(score_history) >= win_adj_move_num:
        fcp_score = score_history[0::2]
        scp_score = score_history[1::2]

        fwin_cnt, swin_cnt, win_score = 0, 0, 300
        for i, (fs, ss) in enumerate(zip(reversed(fcp_score),
                                         reversed(scp_score))):
            if i >= 3:
                break
            if i <= 2 and fs >= win_score and ss <= -win_score:
                fwin_cnt += 1
            elif i <= 2 and fs <= -win_score and ss >= win_score:
                swin_cnt += 1

        if fwin_cnt >= 3:
            gres = '1-0' if side else '0-1'
            e1score = 1.0
            ret = True
        if swin_cnt >= 3:
            gres = '1-0' if side else '0-1'
            e1score = 0
            ret = True

    return ret, gres, e1score


def adjudicate_draw(score_history, draw_adj_move_num):
    ret, gres, e1score = False, '*', 0.0

    if len(score_history) >= draw_adj_move_num:
        fcp_score = score_history[0::2]
        scp_score = score_history[1::2]

        draw_cnt, draw_score = 0, 5
        for i, (fs, ss) in enumerate(zip(reversed(fcp_score),
                                         reversed(scp_score))):
            if i >= 3:
                break
            if i <= 2 and abs(fs) <= draw_score and abs(ss) <= draw_score:
                draw_cnt += 1

        if draw_cnt >= 3:
            gres = '1/2-1/2'
            e1score = 0.5
            ret = True

    return ret, gres, e1score


def is_game_end(line, start_turn):
    game_end, gres, e1score = False, '*', 0.0

    if '1-0' in line:
        game_end = True
        e1score = 1.0 if start_turn else 0.0
        gres = '1-0'
    elif '0-1' in line:
        game_end = True
        e1score = 0.0 if start_turn else 0.0
        gres = '0-1'
    elif '1/2-1/2' in line:
        game_end = True
        e1score = 0.5
        gres = '1/2-1/2'

    return game_end, gres, e1score


def match(e1, e2, fen, test_param, base_param, output_game_file, btms=10000,
          incms=100, num_games=2, is_adjudicate_game=False):
    """
    Run an engine match between e1 and e2. Save the game and print result
    from e1 perspective.

    :btms: base time in ms
    :incms: increment time in ms
    """
    win_adj_move_num, draw_adj_move_num = 40, 60
    move_hist = []
    time_value = btms//100 + incms//100  # Convert ms to centisec
    all_e1score = 0.0
    is_show_search_info = False

    # Setup Timer for test and base engine.
    timer = [Timer(btms, incms), Timer(btms, incms)]

    # Start engine match, 2 games will be played.
    for gn in range(num_games):

        pe1 = subprocess.Popen(e1, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)

        pe2 = subprocess.Popen(e2, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)

        if gn % 2 == 0:
            eng = [pe1, pe2]
        else:
            eng = [pe2, pe1]

        for i, e in enumerate(eng):
            e.stdin.write('xboard\n')
            e.stdin.write('protover 2\n')
            for eline in iter(e.stdout.readline, ''):
                line = eline.strip()
                if 'done=1' in line:
                    break

            # Set test param to e1
            if (i == 0 and gn % 2 == 0) or (i == 1 and gn % 2 == 1):
                for k, v in test_param.items():
                    e.stdin.write(f'option {k}={v}\n')
                    print(f'test_engine: set {k} to {v}')

            # Set base param to e2
            if (i == 1 and gn % 2 == 0) or (i == 0 and gn % 2 == 1):
                for k, v in base_param.items():
                    e.stdin.write(f'option {k}={v}\n')
                    print(f'base_engine: set {k} to {v}')

        for e in eng:
            e.stdin.write('variant\n')
            e.stdin.write('new\n')
            e.stdin.write('post\n')

            # Send level command.
            min, sec = divmod(btms//1000, 60)
            incsec = incms/1000
            e.stdin.write(f'level 0 {min}:{sec} {incsec}\n')
            print(f'level 0 {min}:{sec} {incsec}')

            e.stdin.write(f'setboard {fen}\n')

        num, side, move, line, game_end = 0, 0, None, '', False
        score_history, elapse_history, start_turn = [], [], turn(fen)
        gres, e1score = '*', 0.0

        # The name color index 0 is white.
        name_color = ['test' if gn%2 == 0 and start_turn else 'base',
                      'test' if gn%2 == 1 and start_turn else 'base']

        # Start the game.
        while True:
            eng[side].stdin.write(f'time {timer[side].rem_cs()}\n')
            eng[side].stdin.write(f'otim {timer[not side].rem_cs()}\n')
            t1 = time.perf_counter_ns()

            if num == 0:
                eng[side].stdin.write('go\n')
            else:
                move_hist.append(move)
                eng[side].stdin.write(f'{move}\n')

            num += 1

            for eline in iter(eng[side].stdout.readline, ''):
                line = eline.strip()

                if is_show_search_info:
                    if not line.startswith('#'):
                        print(line)

                # Save score from engine search info.
                if line.split()[0].isdigit():
                    score = int(line.split()[1])  # cp

                # Check end of game as claimed by engines.
                game_endr, gresr, e1scorer = is_game_end(line, start_turn)
                if game_endr:
                    game_end, gres, e1score = game_endr, gresr, e1scorer
                    break

                if 'move ' in line and not line.startswith('#'):
                    elapse = (time.perf_counter_ns() - t1) // 1000000
                    timer[side].update(elapse)
                    elapse_history.append(elapse)

                    move = line.split('move ')[1]
                    score_history.append(score)
                    break

            if game_end:
                break

            if is_adjudicate_game:
                game_endr, gresr, e1scorer = adjudicate_win(
                    score_history, win_adj_move_num, side)
                if not game_endr:
                    game_endr, gresr, e1scorer = adjudicate_draw(
                        score_history, draw_adj_move_num)
                if game_endr:
                    gres, e1score = gresr, e1scorer
                    print('Game ends by adjudication')
                    break

            side = not side

        if output_game_file is not None:
            save_game(output_game_file, fen, move_hist, name_color[0],
                      name_color[1], start_turn, gres)

        for e in eng:
            e.stdin.write('quit\n')

        print(e1score)
        all_e1score += e1score

    return all_e1score/num_games


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--round', required=False,
                        help='number of rounds to play, default=1\n'
                             'if round is 1, total games will be 2\n'
                             'since each engine will play the start side\n'
                             'of the start position',
                        type=int, default=1)
    parser.add_argument('--test-engine', required=True,
                        help='engine path/file or file of the engine\n'
                             'to be optmized')
    parser.add_argument('--base-engine', required=True,
                        help='engine path/file or file of the engine\n'
                             'as opponent to test engine')
    parser.add_argument('--start-fen', required=True,
                        help='fen file of startpos for the match')
    parser.add_argument('--test-param', required=True,
                        help='parameters to be optimized\n'
                             'Example:\n'
                             '"QueenOp 800 500 1500 1000, RookOp ..."\n'
                             'parname value min max factor')
    parser.add_argument('--base-param', required=True,
                        help='parameters for base_engine\n'
                             'Example:\n'
                             '"QueenOp 800 500 1500 1000, RookOp ..."\n'
                             'parname value min max factor')
    parser.add_argument('--tc-base-timems', required=False,
                        help='base time in millisec, default=10000',
                        type=int, default=10000)
    parser.add_argument('--tc-inc-timems', required=False,
                        help='increment in millisec, default=100',
                        type=int, default=100)
    parser.add_argument('--adjudicate', action='store_true',
                        help='adjudicate the game')
    parser.add_argument('--pgn-output-file', required=False,
                        help='pgn output filename')

    args = parser.parse_args()

    e1 = args.test_engine
    e2 = args.base_engine
    fen_file = args.start_fen
    is_random_startpos = True

    # Convert param to a dict
    test_param = {}
    for par in args.test_param.split(','):
        par = par.strip()
        sppar = par.split()  # Does not support param with space
        spname = sppar[0].strip()
        spvalue = int(sppar[1].strip())
        test_param.update({spname: spvalue})

    # Convert base param to a dict
    base_param = {}
    for par in args.base_param.split(','):
        par = par.strip()
        sppar = par.split()  # Does not support param with space
        spname = sppar[0].strip()
        spvalue = int(sppar[1].strip())
        base_param.update({spname: spvalue})

    fens = get_fen_list(fen_file, is_random_startpos)
    test_engine_score = []

    output_game_file = args.pgn_output_file

    # Loop thru the fens and create a match.
    for i, fen in enumerate(fens):
        print(f'starting round {i+1} ...')
        res = match(e1, e2, fen, test_param, base_param, output_game_file,
                    btms=args.tc_base_timems, incms=args.tc_inc_timems,
                    is_adjudicate_game=args.adjudicate)
        print(f'ended round {i + 1}')
        test_engine_score.append(res)
        if i >= args.round - 1:
            break

    # The match is done, print score perf of test engine.
    print(f'{sum(test_engine_score)/len(test_engine_score)}')


if __name__ == '__main__':
    main()
