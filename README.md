# Optimizer for games

Optimizer for game coefficients using the SPSA algorithm.
Author: Stéphane Nicolet

### Usage:  
`python game_optimizer.py --iteration 1000 --param "queenvalue 1000 800 1200 1000, rookvalue 500 450 600 1000"`  
1000 is the value  
800 is the min  
1200 is the max  
1000 is the factor, used to control the input number to optimizer. value/factor = 1000/1000 = 1 will be sent to optimizer. If the engine  is not sensitive to the suggested parameter values from optimizer, you may increase that factor. For centipawn values for piece values, a factor of 1000 is a good start.

### List of files in the directory ###

- *game_optimizer.py* : the main file of the package
- *spsa.py* : a general-purpose minimization algorithm (an improved version of the SPSA algorithm)
- *utils.py* : small utility functions
- *match.py* : a script to organize a match between two playing engines in any game (Go, Chess, etc..)
- *chess_game.py* : organize one game of Chess between two engines. Can be plugged into *match.py*
- *chess_match.py* : a specialized Chess version of *match.py*, more efficient because it uses parallelism for the match

### Sample run
[Queen piece value optimization](https://github.com/fsmosca/spsa/wiki/Sample-run)
