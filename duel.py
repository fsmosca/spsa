"""
duel.py

A module to handle non-uci engine vs engine matches.
"""


import subprocess
import argparse
import time
import random
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor
import logging
from statistics import mean


logging.basicConfig(filename='log_duel.txt', filemode='w',
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


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
        return True if self.rem_cs() <= 0 else False

    def rem_cs(self):
        return self.rem_time // 10


def define_engine(engine_option_value):
    """
    Define engine files, name and options.
    """
    ed1, ed2 = {}, {}
    e1 = {'proc': None, 'cmd': None, 'name': 'test', 'opt': ed1, 'tc': ''}
    e2 = {'proc': None, 'cmd': None, 'name': 'base', 'opt': ed2, 'tc': ''}
    for i, eng_opt_val in enumerate(engine_option_value):
        for value in eng_opt_val:
            if i == 0:
                if 'cmd=' in value:
                    e1.update({'cmd': value.split('=')[1]})
                elif 'option.' in value:
                    # Todo: support float value
                    # option.QueenValueOpening=1000
                    optn = value.split('option.')[1].split('=')[0]
                    optv = int(value.split('option.')[1].split('=')[1])
                    ed1.update({optn: optv})
                    e1.update({'opt': ed1})
                elif 'tc' in value:
                    e1.update({'tc': value.split('=')[1]})
            elif i == 1:
                if 'cmd=' in value:
                    e2.update({'cmd': value.split('=')[1]})
                elif 'option.' in value:
                    optn = value.split('option.')[1].split('=')[0]
                    optv = int(value.split('option.')[1].split('=')[1])
                    ed2.update({optn: optv})
                    e2.update({'opt': ed2})
                elif 'tc' in value:
                    e2.update({'tc': value.split('=')[1]})

    return e1, e2


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


def get_tc(tcd):
    """
    tc=0/3+1 or 3+1, blitz 3m + 1s inc
    tc=0/0:5+0.1 or 0:5+0.1, blitz 0m + 5s + 0.1s inc
    """
    base_minv, base_secv, inc_secv = 0, 0, 0.0

    # Check base time with minv:secv format.
    if '/' in tcd:
        basev = tcd.split('/')[1].split('+')[0].strip()
    else:
        basev = tcd.split('+')[0].strip()

    if ':' in basev:
        base_minv = int(basev.split(':')[0])
        base_secv = int(basev.split(':')[1])
    else:
        base_minv = int(basev)

    if '/' in tcd:
        inc_secv = float(tcd.split('/')[1].split('+')[1].strip())
    else:
        inc_secv = float(tcd.split('+')[1].strip())

    return base_minv, base_secv, inc_secv


def turn(fen):
    """
    Return side to move of the given fen.
    """
    side = fen.split()[1].strip()
    if side == 'w':
        return True
    return False


def save_game(outfn, fen, moves, e1, e2, start_turn, gres, termination=''):
    logging.info('Saving game ...')
    with open(outfn, 'a') as f:
        f.write('[Event "Optimization test"]\n')
        f.write(f'[White "{e1 if start_turn else e2}"]\n')
        f.write(f'[Black "{e1 if not start_turn else e2}"]\n')
        f.write(f'[Result "{gres}"]\n')

        if termination != '':
            f.write(f'[Termination "{termination}"]\n')

        f.write(f'[FEN "{fen}"]\n\n')
        for m in moves:
            f.write(f'{m} ')
        f.write('\n\n')


def adjudicate_win(score_history, win_adj_move_num, side):
    logging.info('Try adjudicating this game by win ...')
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
            logging.info(f'{"White" if side else "Black"} wins by adjudication.')
            ret = True
        if swin_cnt >= 3:
            gres = '1-0' if side else '0-1'
            e1score = 0
            logging.info(f'{"White" if side else "Black"} wins by adjudication.')
            ret = True

    return ret, gres, e1score


def adjudicate_draw(score_history, draw_adj_move_num):
    logging.info('Try adjudicating this game by draw ...')
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
            logging.info('Draw by adjudication.')
            ret = True

    return ret, gres, e1score


def is_game_end(line, test_engine_color):
    game_end, gres, e1score = False, '*', 0.0

    if '1-0' in line:
        game_end = True
        e1score = 1.0 if test_engine_color else 0.0
        gres = '1-0'
    elif '0-1' in line:
        game_end = True
        e1score = 1.0 if not test_engine_color else 0.0
        gres = '0-1'
    elif '1/2-1/2' in line:
        game_end = True
        e1score = 0.5
        gres = '1/2-1/2'

    return game_end, gres, e1score


def param_to_dict(param):
    """
    Convert string param to a dictionary.
    """
    ret_param = {}
    for par in param.split(','):
        par = par.strip()
        sppar = par.split()  # Does not support param with space
        spname = sppar[0].strip()
        spvalue = int(sppar[1].strip())
        ret_param.update({spname: spvalue})

    return ret_param


def time_forfeit(is_timeup, current_color, test_engine_color):
    game_end, gres, e1score = False, '*', 0.0

    if is_timeup:
        # test engine loses as white
        if current_color and test_engine_color:
            gres = '0-1'
            e1score = 0.0
            game_end = True
            print(f'test engine with color {test_engine_color} loses on time')
        # test engine loses as black
        elif not current_color and not test_engine_color:
            gres = '1-0'
            e1score = 0.0
            game_end = True
            print(f'test engine with color {test_engine_color} loses on time')
        # test engine wins as white
        elif not current_color and test_engine_color:
            gres = '1-0'
            e1score = 1.0
            game_end = True
            print(f'test engine with color {test_engine_color} wins on time')
        # test engine wins as black
        elif current_color and not test_engine_color:
            gres = '0-1'
            e1score = 1.0
            game_end = True
            print(f'test engine with color {test_engine_color} wins on time')

    if game_end:
        logging.info('Game ends by time forfeit.')

    return game_end, gres, e1score


def match(e1, e2, fen, output_game_file, variant, num_games=2,
          is_adjudicate_game=False):
    """
    Run an engine match between e1 and e2. Save the game and print result
    from e1 perspective.
    """
    win_adj_move_num, draw_adj_move_num = 40, 60
    move_hist = []
    all_e1score = 0.0
    is_show_search_info = False

    # Start engine match, 2 games will be played.
    for gn in range(num_games):
        logging.info(f'Match game no. {gn + 1}')
        logging.info(f'Test engine plays as {"first" if gn % 2 == 0 else "second"} engine.')

        pe1 = subprocess.Popen(e1['cmd'], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=1)

        pe2 = subprocess.Popen(e2['cmd'], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=1)

        e1.update({'proc': pe1})
        e2.update({'proc': pe2})

        if gn % 2 == 0:
            eng = [e1, e2]
        else:
            eng = [e2, e1]

        for i, pr in enumerate(eng):
            e = pr['proc']
            pn = pr['name']

            e.stdin.write('xboard\n')
            logging.debug(f'{pn} > xboard')
            e.stdin.write('protover 2\n')
            logging.debug(f'{pn} > protover 2')

            for eline in iter(e.stdout.readline, ''):
                line = eline.strip()
                if 'done=1' in line:
                    break

            # Set param to engines.
            for k, v in pr['opt'].items():
                e.stdin.write(f'option {k}={v}\n')
                print(f'{pn} -> option {k}={v}')

        timer = []
        for i, pr in enumerate(eng):
            e = pr['proc']
            pn = pr['name']

            e.stdin.write(f'variant {variant}\n')
            logging.debug(f'{pn} > variant {variant}')

            e.stdin.write('ping 1\n')
            logging.debug(f'{pn} > ping 1')
            for eline in iter(e.stdout.readline, ''):
                line = eline.strip()
                logging.debug(f'{pn} < {line}')
                if 'pong' in line:
                    break

            e.stdin.write('new\n')
            logging.debug(f'{pn} > new')

            e.stdin.write('post\n')
            logging.debug(f'{pn} > post')

            # Define time control, base time in minutes and inc in seconds.
            base_minv, base_secv, incv = get_tc(pr['tc'])
            all_base_sec = base_minv * 60 + base_secv

            logging.info(f'base_minv: {base_minv}m, base_secv: {base_secv}s, incv: {incv}s')

            # Send level command to each engine.
            e.stdin.write(f'level 0 {all_base_sec//60} {int(incv)}\n')
            logging.debug(f'{pn} > level 0 {all_base_sec//60} {int(incv)}')

            # Setup Timer, convert base time to ms and inc in sec to ms
            timer.append(Timer(all_base_sec * 1000, int(incv * 1000)))

            e.stdin.write(f'setboard {fen}\n')
            logging.debug(f'{pn} > setboard {fen}')

        num, side, move, line, game_end = 0, 0, None, '', False
        score_history, elapse_history, start_turn = [], [], turn(fen)
        gres, e1score = '*', 0.0
        is_time_over = [False, False]
        current_color = start_turn  # True if white to move

        test_engine_color = True if start_turn and gn % 2 == 0 else False
        termination = ''

        # Start the game.
        while True:
            assert timer[side].rem_cs() > 0
            eng[side]['proc'].stdin.write(f'time {timer[side].rem_cs()}\n')
            logging.debug(f'{eng[side]["name"]} > time {timer[side].rem_cs()}')

            eng[side]['proc'].stdin.write(f'otim {timer[not side].rem_cs()}\n')
            logging.debug(f'{eng[side]["name"]} > otim {timer[not side].rem_cs()}')

            t1 = time.perf_counter_ns()

            if num == 0:
                eng[side]['proc'].stdin.write('go\n')
                logging.debug(f'{eng[side]["name"]} > go')
            else:
                move_hist.append(move)
                eng[side]['proc'].stdin.write(f'{move}\n')
                logging.debug(f'{eng[side]["name"]} > {move}')

            num += 1
            score = None

            for eline in iter(eng[side]['proc'].stdout.readline, ''):
                line = eline.strip()

                logging.debug(f'{eng[side]["name"]} < {line}')

                if is_show_search_info:
                    if not line.startswith('#'):
                        print(line)

                # Save score from engine search info.
                if line.split()[0].isdigit():
                    score = int(line.split()[1])  # cp

                # Check end of game as claimed by engines.
                game_endr, gresr, e1scorer = is_game_end(line, test_engine_color)
                if game_endr:
                    game_end, gres, e1score = game_endr, gresr, e1scorer
                    break

                if 'move ' in line and not line.startswith('#'):
                    elapse = (time.perf_counter_ns() - t1) // 1000000
                    timer[side].update(elapse)
                    elapse_history.append(elapse)

                    move = line.split('move ')[1]
                    score_history.append(score if score is not None else 0)

                    if timer[side].is_zero_time():
                        is_time_over[current_color] = True
                        termination = 'forfeits on time'
                        print('time is over')
                        logging.info('time is over')
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
                    print(f'Game ends by adjudication, side is {start_turn}')
                    break

            # Time is over
            game_endr, gresr, e1scorer = time_forfeit(
                is_time_over[current_color], current_color, test_engine_color)
            if game_endr:
                gres, e1score = gresr, e1scorer
                break

            side = not side
            current_color = not current_color

        if output_game_file is not None:
            save_game(output_game_file, fen, move_hist, eng[0]["name"],
                      eng[1]["name"], start_turn, gres, termination)

        for i, e in enumerate(eng):
            e['proc'].stdin.write('quit\n')
            logging.debug(f'{e["name"]} > quit')

        print(e1score)
        all_e1score += e1score

    return all_e1score/num_games


def round_match(fen, e1, e2, output_game_file, games_per_match,
                is_adjudicate_game, variant, posround=1):
    """
    Play a match between e1 and e2 using fen as starting position. By default
    2 games will be played color is reversed. If posround is more than 1, the
    match will be repeated posround times. The purpose of posround is to verify
    that the match result is repeatable with the use of only a single fen.
    """
    test_engine_score = []

    for _ in range(posround):
        res = match(e1, e2, fen, output_game_file, variant,
                    num_games=games_per_match,
                    is_adjudicate_game=is_adjudicate_game)
        test_engine_score.append(res)

    return test_engine_score


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--round', required=False,
                        help='number of rounds to play, default=1\n'
                             'if round is 1, total games will be 2\n'
                             'since each engine will play the start side\n'
                             'of the start position',
                        type=int, default=1)
    parser.add_argument('-engine', nargs='*', action='append', required=True,
                        metavar=('cmd=', 'name='),
                        help='This option is used to define the engines.\n'
                        'Example:\n'
                        '-engine cmd=engine1.exe name=test ... --engine cmd=engine2.exe name=base')
    parser.add_argument('--adjudicate', action='store_true',
                        help='adjudicate the game')
    parser.add_argument('-pgnout', required=False, metavar='pgn_output_filename',
                        help='pgn output filename')
    parser.add_argument('--concurrency', required=False,
                        help='number of game to run in parallel, default=1',
                        type=int, default=1)
    parser.add_argument('--variant', required=True, help='name of the variant')
    parser.add_argument('-each', nargs='*', action='append', required=False,
                        metavar=('tc=', 'option.<option_name>='),
                        help='This option is used to apply to both engnes.\n'
                             'Example where tc is applied to each engine:\n'
                             '-each tc=1+0.1')
    parser.add_argument('-openings', nargs='*', action='append', required=True,
                        metavar=('file=', 'format='),
                        help='Define start openings. Example:\n'
                             '-openings file=start.fen format=epd')

    args = parser.parse_args()

    # Define engine files, name and options.
    e1, e2 = define_engine(args.engine)

    # Exit if engine file is not defined.
    if e1['cmd'] is None or e2['cmd'] is None:
        print('Error, engines are not properly defined!')
        return

    each_engine_option = {}
    for opt in args.each:
        for value in opt:
            key = value.split('=')[0]
            val = value.split('=')[1].strip()
            each_engine_option.update({key: val})

    # Exit if tc or time control is not defined.
    if e1['tc'] == '' or e2['tc'] == '':
        if 'tc' in each_engine_option:
            for key, val in each_engine_option.items():
                if key == 'tc':
                    e1.update({key: val})
                    e2.update({key: val})
                    break
        else:
            print('Error, tc or time control is not properly defined!')
            return

    # Start opening file
    if args.openings:
        for opt in args.openings:
            for value in opt:
                if 'file=' in value:
                    fen_file = value.split('=')[1]

    is_random_startpos = True
    games_per_match = 2
    posround = 1  # Number of times the same position is played

    fens = get_fen_list(fen_file, is_random_startpos)

    output_game_file = args.pgnout

    t1 = time.perf_counter()

    # Start match
    joblist = []
    test_engine_score_list = []
    match_done = 0

    # Use Python 3.8 or higher
    with ProcessPoolExecutor(max_workers=args.concurrency) as executor:
        for i, fen in enumerate(fens):
            if i >= args.round:
                break
            job = executor.submit(round_match, fen, e1, e2,
                                  output_game_file, games_per_match,
                                  args.adjudicate, args.variant, posround)
            joblist.append(job)

        for future in concurrent.futures.as_completed(joblist):
            try:
                test_engine_score = future.result()[0]
                test_engine_score_list.append(test_engine_score)
                print(f'test_engine_score: {test_engine_score}')
                match_done += 1
                print(f'match done: {match_done}')
            except concurrent.futures.process.BrokenProcessPool as ex:
                print(f'exception: {ex}')

    # The match is done, print score perf of test engine.
    print(f'test engine score list: {test_engine_score_list}')
    print(f'final test score: {mean(test_engine_score_list)}')
    print(f'elapse: {time.perf_counter() - t1:0.2f}s')


if __name__ == '__main__':
    main()
