#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Usage: chess-match.py LENGTH SEED [PARAM_NAME PARAM_VALUE]...

Organize a small chess match with a set of parameters, using cutechess-cli:

  LENGTH        Length of the match to be played
  SEED          Random seed for the match to be played
  PARAM_NAME    Name of a parameter that's being optimized
  PARAM_VALUE   Value for parameter PARAM_NAME

This script works between SPSA3 and cutechess-cli, a chess utility to organize
matches between chess engines. This Python script plays one MATCH between two
chess engines. One of the engines receives the list of arguments values given
on the command line, and the other one being chosen by the script among a fixed
pool of oppenent(s) specified in the script.

Note: SPSA3 is used as black-box parameter tuning tool, in an implementation
written by S. Nicolet. This is the SPSA algorithm, with a focus on optimizing
parameters for game playing engines like Go, Chess, etc.

In this script the following variables must be modified to fit the test
environment and conditions. The default values are just examples.
   'test_engine_path'
   'base_engine_path
   'cutechess_cli_path'
   'engine'
   'opponents'
   'options'

When the match is completed the script writes the average score of the match
outcome to its standard output, which is a real number between 0.0 (the engine
lost all the games of the match), and 1.0 (the engine won all the games of the
match). For example in a match of six games, 2 wins, 1 draw and 3 losses gives
a match result of (2 + 0.5 + 0) / 6 = 0.417
"""


from subprocess import Popen, PIPE
import logging
import argparse
from pathlib import Path


APP_VERSION = 1.1


logging.basicConfig(format='%(asctime)s : %(message)s', level=logging.INFO,
                    filename='spsa_log.txt', filemode='a')


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--seed', required=False,
                        help='random seed for cutechess, default=0',
                        type=int, default=0)
    parser.add_argument('--fcp', required=True,
                        help='first engine or test engine setting.\n'
                             'Example 1:\n'
                             '--fcp "cmd=deuterium.exe name=test proto-uci"\n'
                             'Example 2 with opetion:\n'
                             '--fcp "cmd=deuterium.exe name=test option.Hash=64 proto-uci"')
    parser.add_argument('--scp', required=True,
                        help='second engine or base engine setting, this is similar to fcp\n'
                             'Example:\n'
                             '--scp "cmd=deuterium.exe name=base proto-uci"')
    parser.add_argument('--cutechess-cli-path', required=True,
                        help='path of cutechess-cli program')
    parser.add_argument('--cutechess-cli-options', required=True,
                        help='cutechess-cli options')
    parser.add_argument('--cutechess-cli-engine-options', required=True,
                        help='cutechess-cli engine options')
    parser.add_argument('--test-param', required=True,
                        help='parameters to be optimized.\n'
                        'Example "QueenValueOp 800 500 1500 1000, RookValueOp ..."')
    parser.add_argument('--base-param', required=True,
                        help='parameters for base_engine.\n'
                             'Example "QueenValueOp 800 500 1500 1000, RookValueOp ..."')

    args = parser.parse_args()
    cutechess_cli_path = args.cutechess_cli_path.rstrip()
    cutechess_cli_options = args.cutechess_cli_options.rstrip()
    cutechess_cli_engine_options = args.cutechess_cli_engine_options.rstrip()
    seed = args.seed

    # test engine
    fcp = args.fcp
    engine_test_name = args.fcp.split('name=')[1].strip().split()[0].strip()

    # base engine
    opponents = [args.scp]
    engine_base_name = args.scp.split('name=')[1].strip().split()[0].strip()
    scp = opponents[seed % len(opponents)]

    # Parse the parameters that should be optimized
    # --param "q 800 500 1200 1000, r 450 400 600 1000"
    # q value min max factor, r value min max factor
    for par in args.test_param.split(','):
        par = par.strip()
        sppar = par.split()  # Does not support param with space
        spname = sppar[0].strip()
        spvalue = int(sppar[1].strip())
        fcp += f' option.{spname}={spvalue} '

    # Parse parameters for base engine
    for par in args.base_param.split(','):
        par = par.strip()
        sppar = par.split()  # Does not support param with space
        spname = sppar[0].strip()
        spvalue = int(sppar[1].strip())
        scp += f' option.{spname}={spvalue} '

    # Run optimizer at the folder where game_optimizer.py is located.
    if Path(cutechess_cli_path).suffix == '.py':
        command = f'python -u {cutechess_cli_path} {cutechess_cli_options} -variant mt '
    else:
        command = f'{cutechess_cli_path} {cutechess_cli_options} -srand {seed} '
    command += f'-engine {fcp} -engine {scp} '
    command += f'-each {cutechess_cli_engine_options}'
    logging.info(f'{__file__} > {command}')

    # Run cutechess-cli and wait for it to finish
    process = Popen(command, shell=True, stdout=PIPE, text=True)
    output = process.communicate()[0]
    if process.returncode != 0:
        print('Could not execute command: %s' % command)
        return 2

    # Convert cutechess-cli's output into a match score:
    # we search for the last line containing a score of the match
    result = ""
    for line in output.splitlines():
        if line.startswith(f'Score of {engine_test_name} vs {engine_base_name}'):
            result = line[line.find("[")+1: line.find("]")]

    if result == "":
        raise Exception('The match did not terminate properly')
    else:
        logging.info(f'{__file__} > match result: {result}')
        print(result)


if __name__ == "__main__":
    main()
