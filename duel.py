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


def match(e1, e2, fen, param, output_game_file, btms=10000, incms=100,
          num_games=2):
    """
    Run an engine match between e1 and e2. Save the game and print result
    from e1 perspective.

    :btms: base time in ms
    :incms: increment time in ms
    """
    num_games = 2
    win_adj_move_num, draw_adj_move_num = 40, 60
    move_hist = []
    time_value = btms//100 + incms//100  # Convert ms to centisec
    all_e1score = 0.0

    # Reverse start color of engine.
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
            e.stdin.write('protover\n')
            for eline in iter(e.stdout.readline, ''):
                line = eline.strip()
                if 'done=1' in line:
                    break

            # Set option to e1
            if (i == 0 and gn % 2 == 0) or (i == 1 and gn % 2 == 1):
                for k, v in param.items():
                    e.stdin.write(f'option {k}={v}\n')
                    print(f'set {k} to {v}')

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
        score_history, start_turn = [], turn(fen)
        gres, e1score = '*', 0.0

        # Start the match.
        while True:
            # Todo: Calculate time remaining

            if num == 0:
                eng[side].stdin.write(f'time {time_value}\n')
                eng[side].stdin.write(f'otim {time_value}\n')
                eng[side].stdin.write('go\n')
            else:
                eng[side].stdin.write(f'time {time_value}\n')
                eng[side].stdin.write(f'otim {time_value}\n')
                move_hist.append(move)
                eng[side].stdin.write(f'{move}\n')

            num += 1

            for eline in iter(eng[side].stdout.readline, ''):
                line = eline.strip()

                if False:
                    if not line.startswith('#'):
                        print(line)

                # Save score from engine search info.
                if line.split()[0].isdigit():
                    score = int(line.split()[1])  # cp

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

                if 'move ' in line and not line.startswith('#'):
                    move = line.split('move ')[1]
                    score_history.append(score)
                    break

            game_endr, gresr, e1scorer = adjudicate_win(score_history,
                                                     win_adj_move_num, side)

            if not game_endr:
                game_endr, gresr, e1scorer = adjudicate_draw(score_history,
                                                             draw_adj_move_num)

            if game_endr:
                gres = gresr
                e1score = e1scorer
                break

            if game_end:
                break

            side = not side

        save_game(output_game_file, fen, move_hist, 'e1', 'e2', start_turn, gres)

        for e in eng:
            e.stdin.write('quit\n')
            print(f'Quit {e}')

        print(e1score)
        all_e1score += e1score

    return all_e1score/num_games


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
    parser.add_argument('--tc-base-timems', required=False,
                        help='base time in millisec, default=10000',
                        type=int, default=10000)
    parser.add_argument('--tc-inc-timems', required=False,
                        help='increment in millisec, default=100',
                        type=int, default=100)

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
        res = match(e1, e2, fen, param, output_game_file,
                    btms=args.tc_base_timems, incms=args.tc_inc_timems)
        print(f'ended game {i + 1}')
        test_engine_score.append(res)
        if i >= num_games - 1:
            break

    # The match is done, print score perf of test engine.
    print(f'{sum(test_engine_score)/len(test_engine_score)}')


if __name__ == '__main__':
    main()
