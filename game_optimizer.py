# -*- coding: utf-8 -*-
"""
Optimizer for game coefficients using the SPSA algorithm.
Author: Stéphane Nicolet

Usage : python game-optimizer.py [PARAM_NAME PARAM_VALUE]...

The parameter list can also we provided as a string in the Python code,
see the function set_parameters_from_string() in the example section.

"""

from subprocess import Popen, PIPE
import random
import argparse
import copy
import logging

import spsa
import utils


APP_NAME = 'Python SPSA Parameter Optimizer'
APP_VERSION = 1.0


logging.basicConfig(format='%(asctime)s : %(message)s', level=logging.INFO,
                    filename='spsa_log.txt', filemode='a')


class game_optimizer:

    def __init__(self):
        """
        The constructor of a game_optimizer object.
        """

        # Store the arguments
        # name of the script used to make a match against the reference engine
        self.ENGINE_COMMAND = ""
        self.THETA_0 = {}  # the initial set of parameter

        # Size of the minimatches used to estimate the gradient.
        # When using cutechess this is the number of rounds.
        # If repeat is set and games=2 and rounds=12, then
        # total games to estimate the gradient equals 2x12 or 24.
        self.MINI_MATCH = 1

    def set_engine_command(self, command):
        """
        Set the name of the command used to run a minimatch against the
        reference engine. The command is a shell script which will receive
        the list of parameters on the standard output, and ruturn the score
        of the match, with the convention that higher scores will be a good
        thing for the optimized engine.
        """

        # Store the command name
        self.ENGINE_COMMAND = command

    def launch_engine(self, theta):
        """
        Launch the match of the engine with parameters theta
        """

        # Each match will be started with a different seed,
        # passed as a command line parameter
        seed = random.randint(1, 100000000)  # a random seed

        # Create the command line and the list of parameters
        command = f'{self.ENGINE_COMMAND}'
        args = f'--rounds {self.MINI_MATCH} '
        args += f'--seed {seed}'

        new_param, cnt = '"', 0
        for name, value in theta.items():
            cnt += 1
            new_param += f'{name} {value["value"]} {value["min"]} {value["max"]} {value["factor"]}'
            if cnt < len(theta):
                new_param += ', '
            else:
                new_param += '"'

        match_command = f'{command} {args} --param {new_param}'
        logging.info(f'{__file__} > match_command: {match_command}')

        # We use a subprocess to launch the match
        process = Popen(match_command, stdout=PIPE, text=True)
        output = process.communicate()[0]

        if process.returncode != 0:
            logging.exception('There is problem in match process!')
            raise

        # Return the score of the match.
        return float(output)

    def goal_function(self, i, **args):
        """
        This is the function that the class exports, and that can be plugged
        into the generic SPSA minimizer.

        Mainly we launch the engine match, take the opposite of the score (because
        we want to *maximize* the score but SPSA is a minimizer). Note that we add
        a regulization term, which helps the convexity of the problem.
        """

        logging.info(f'{__file__} > param suggestion from optimizer: {args}')

        # Create the parameter vector
        theta = copy.deepcopy(args)
        for (name, value) in self.THETA_0.items():
            theta[name]['value'] = args[name]['value']

        # Calculate the regularization term
        regularization = utils.regulizer(utils.difference(theta, self.THETA_0), 0.01, 0.5)

        # Calculate the score of the minimatch

        # Change the value of theta or parameters to centipawn as input to engine.
        param = copy.deepcopy(theta)
        for k, v in param.items():
            param[k]['value'] = int(param[k]['value'] * v['factor'])
        logging.info(f'{__file__} > new param for test engine: {param}')
        print(f'param suggestion from optimizer: {param}')

        score = self.launch_engine(param)
        logging.info(f'{__file__} > match score: {score}')

        result = -score + regularization
        logging.info(f'{__file__} > regularization = {regularization}')
        logging.info(f'{__file__} > result = -score + regularization = -({score}) + {regularization} = {result}')

        print(f'goal = {-result}, {"+ck" if i == 0 else "-ck"}')
        logging.info(f'{__file__} > goal = -(result) = -({result}) = {-result}')

        return result

    def set_parameters_from_string(self, s):
        """
        This is the function to transform the list of parameters, given as a string,
        into a vector for internal usage by the class.

        Example:
            From:
            QueenValueOp 750 300 1500 1000, QueenValueEn 750 300 1500 1000
            To:
            {'QueenValueOp': {'value': 750, 'min': 300, 'max': 1500, 'factor': 1000},
             'QueenValueEn': {'value': 750, 'min': 300, 'max': 1500, 'factor': 1000}}

        This vector will be used as the starting point for the optimizer.

        Note: Parameter with space like Skill Level is not supported at the moment.
        """
        init_param = {}

        param_div = s.split(',')

        for par in param_div:
            par = par.strip()
            name = par.split()[0].strip()
            val = int(par.split()[1].strip())
            minv = int(par.split()[2].strip())
            maxv = int(par.split()[3].strip())
            factor = int(par.split()[4].strip())
            init_param.update({name: {'value': val, 'min': minv, 'max': maxv, 'factor': factor}})

        # Apply limits based on user input of min and max
        self.THETA_0 = utils.apply_limits(init_param, is_factor=False)

        logging.info(f'{__file__} > init param {self.THETA_0}')

        return self.THETA_0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='%s %s' % (APP_NAME, APP_VERSION),
        description='Optimize parameters like evaluation parameters of a chess engine',
        epilog='%(prog)s')
    parser.add_argument('--iteration', required=False,
                        help='input iteration, default=10000',
                        type=int, default=10000)
    parser.add_argument('--param', required=True,
                        help='input parameters to optimize, example: '
                             'queenvalue 800 700 1200 1000, rookvalue 500 400 700 1000, '
                             '800 is the starting value '
                             '700 is the minimum '
                             '1200 is the maximum '
                             '1000 is the factor, 800/factor will be sent to optimizer')

    args = parser.parse_args()
    iterations = args.iteration
    parameters = args.param

    # Create the optimization object
    optimizer = game_optimizer()

    # Set the name of the script to run matches
    optimizer.set_engine_command("python chess_match.py")

    print(f'parameters = {parameters}')
    theta0 = optimizer.set_parameters_from_string(parameters)

    # Apply factor to the value before sending to optimizer
    for k, v in theta0.items():
        theta0[k]['value'] = int(v['value']) / int(v['factor'])

    # Create the SPSA minimizer with 10000 iterations...
    minimizer = spsa.SPSA_minimization(optimizer.goal_function, theta0, iterations)

    # Run it!
    minimum = minimizer.run()
    print(f'minimum = {minimum}')
