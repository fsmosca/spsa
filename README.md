# Optimizer for games

Optimizer for game coefficients using the SPSA algorithm.
Author: Stéphane Nicolet

### A. Installation
* On windows
  * Install python 3.8 from https://www.python.org/downloads/  
  * Install requirements.txt  
  `pip install -r requirements.txt`
  * Download this repo as it already contains sample engines and cutechess-cli tourney manager.  
  Press `Clone->Download ZIP` at the top-right of this page.
  * Edit optimizer_setting.yml with notepad or notepad++ to set the engine and cutechess options.
  * Run the optimizer
  `python game_optimizer.py`

### B. Usage:  
`python game_optimizer.py`

#### Save console output to file testlog.txt in windows 10 powershell
`python -u game_optimizer.py | tee testlog.txt`

#### Limit iteration to 1000
`python game_optimizer.py --iteration 1000`

#### Add another stopping rule if goal is good (all mean goal <= option_value) and minimum iter is meet.
`python game_optimizer.py --stop-all-mean-goal -0.75 --stop-min-iter 200`  

For optimizer the goal is to maximize the score of test_engine vs base_engine in a match of 4 games or so. The optimizer will vary the value of the parameter (say queenvalue 650) to be optimized which will be used by test_engine. It will then match with base_engine at say fast time control of 5s+50ms. If test_engine scored 1/4 or 1.0 point out of 4 games, the score is 0.25 for test_engine and this is bad because it is below 0.5 or 50%. This score is then reported to the optimizer as -(actual match score of test_engine) or -0.25 that is (negate the actual match score because the optimizer will minimize it). The minimum of optimizer is -1.0, so from -0.25 it will attempt to have -0.5, -0.75 and so on. The minimum of optimizer is a maximum score of the test_engine. 
After some calculations the optimizer will suggest a new parameter values say queenvalue 700, to try next vs the base_engine. An iteration is completed after the score is received. Optimizer saves every score or goal in every iteration, it will then calculate the mean or average of it in the last 30 iterations. If this mean goal is equal or below `--stop-all-mean-goal` and the iterations is already equal or more than the `--stop-min-iter` then the optimizer is stopped.

#### Help
`python game_optimizer.py -h`

```
PS D:\github\spsa> python game_optimizer.py -h
usage: Python SPSA Parameter Optimizer 1.1 [-h] [--iteration ITERATION] [--stop-all-mean-goal STOP_ALL_MEAN_GOAL]
                                           [--stop-min-iter STOP_MIN_ITER]

Optimize parameters like evaluation parameters of a chess engine

optional arguments:
  -h, --help            show this help message and exit
  --iteration ITERATION
                        input iteration, default=10000
  --stop-all-mean-goal STOP_ALL_MEAN_GOAL
                        input mean goal to stop the optimizer, default=-0.95
  --stop-min-iter STOP_MIN_ITER
                        input min iteration to stop the optimizer when the
                        mean goal condition is meet, default=10000

Python SPSA Parameter Optimizer 1.1
```

#### Sample output from console
```
PS D:\github\spsa> python -u game_optimizer.py --iteration 500 --stop-min-iter 50 | tee testlog.txt                     
parameters to optimize = QueenValueOp 650 550 750 100, QueenValueEn 650 550 750 100
starting iter 1 ...
current param:
  QueenValueOp: 650
  QueenValueEn: 650
Run engine match ...
current optimizer mean goal: 1.00000 (low is better, lowest: -1.0, highest: 1.0)
Sample, optimizer goal = -(engine match score) or -(3.0 pts/4 games) or -0.75
Run match 1 ...
param to use:
  QueenValueOp: 640, delta applied: -10
  QueenValueEn: 640, delta applied: -10
Done match 1!, elapse: 26.99sec
Run match 2 ...
param to use:
  QueenValueOp: 660, delta applied: +10
  QueenValueEn: 660, delta applied: +10
Done match 2!, elapse: 25.01sec
Done engine match!
optimizer goal after match 1: -0.62329 (low is better)
optimizer goal after match 2: -0.62329 (low is better)
perf is the same in match 1 and 2, launch new matches ...
Run match 1 ...
param to use:
  QueenValueOp: 640, delta applied: -10
  QueenValueEn: 640, delta applied: -10
Done match 1!, elapse: 25.21sec
Run match 2 ...
param to use:
  QueenValueOp: 660, delta applied: +10
  QueenValueEn: 660, delta applied: +10
Done match 2!, elapse: 18.16sec
Done engine match!
optimizer goal after match 1: -0.49829 (low is better)
optimizer goal after match 2: -0.74829 (low is better)
Basic gradient after 2 engine matches:
  QueenValueOp: -1.2499999999999996
  QueenValueEn: -1.2499999999999996
New gradient after applying correction:
  QueenValueOp: -0.01249999999999999
  QueenValueEn: -0.01249999999999999
new param after application of gradient:
  QueenValueOp: 650
  QueenValueEn: 650
new param after application of limits:
  QueenValueOp: 650
  QueenValueEn: 650
new param after application of best average param:
  QueenValueOp: 650
  QueenValueEn: 650
new param after application of limits:
  QueenValueOp: 650
  QueenValueEn: 650
best param:
  QueenValueOp: 650
  QueenValueEn: 650
best mean goal: -0.6232928932188134
done iter 1!
=========================================
starting iter 2 ...
current param:
  QueenValueOp: 650
  QueenValueEn: 650
Run engine match ...
current optimizer mean goal: -0.62329 (low is better, lowest: -1.0, highest: 1.0)
Sample, optimizer goal = -(engine match score) or -(3.0 pts/4 games) or -0.75
Run 2 matches in parallel ...
Run match 1 ...
param to use:
  QueenValueOp: 642, delta applied: -8
  QueenValueEn: 642, delta applied: -8
Run match 2 ...
param to use:
  QueenValueOp: 657, delta applied: +7
  QueenValueEn: 657, delta applied: +7
Done match 1!, elapse: 31.88sec
Done match 2!, elapse: 31.88sec
Done engine match!
optimizer goal after match 1: -0.37373 (low is better)
optimizer goal after match 2: -0.37376 (low is better)
Basic gradient after 2 engine matches:
  QueenValueOp: -0.0001993076417823503
  QueenValueEn: -0.0001993076417823503
Modify the gradient because the result of engine matches
when using the new param did not improve, but we will not
re-run the engine matches.
Modified gradient at alpha=0.1:
  QueenValueOp: -1.993076417823503e-05
  QueenValueEn: -1.993076417823503e-05
New gradient after applying correction:
  QueenValueOp: -0.002137878684519384
  QueenValueEn: -0.002137878684519384
new param after application of gradient:
  QueenValueOp: 650
  QueenValueEn: 650
new param after application of limits:
  QueenValueOp: 650
  QueenValueEn: 650
new param after application of best average param:
  QueenValueOp: 650
  QueenValueEn: 650
new param after application of limits:
  QueenValueOp: 650
  QueenValueEn: 650
best param:
  QueenValueOp: 650
  QueenValueEn: 650
best mean goal: -0.6232928932188134
done iter 2!
=========================================
starting iter 3 ...
current param:
  QueenValueOp: 650
  QueenValueEn: 650
Run engine match ...
current optimizer mean goal: -0.54011 (low is better, lowest: -1.0, highest: 1.0)
Sample, optimizer goal = -(engine match score) or -(3.0 pts/4 games) or -0.75
Run 2 matches in parallel ...
Run match 1 ...
param to use:
  QueenValueOp: 643, delta applied: -7
  QueenValueEn: 643, delta applied: -7
Run match 2 ...
param to use:
  QueenValueOp: 657, delta applied: +7
  QueenValueEn: 657, delta applied: +7
Done match 1!, elapse: 23.18sec
Done match 2!, elapse: 33.34sec
Done engine match!
optimizer goal after match 1: -0.24882 (low is better)
optimizer goal after match 2: -0.62379 (low is better)
Basic gradient after 2 engine matches:
  QueenValueOp: -2.6737869287694087
  QueenValueEn: -2.6737869287694087
New gradient after applying correction:
  QueenValueOp: -0.07298105438080521
  QueenValueEn: -0.07298105438080521
new param after application of gradient:
  QueenValueOp: 650
  QueenValueEn: 650
new param after application of limits:
  QueenValueOp: 650
  QueenValueEn: 650
new param after application of best average param:
  QueenValueOp: 650
  QueenValueEn: 650
new param after application of limits:
  QueenValueOp: 650
  QueenValueEn: 650
best param:
  QueenValueOp: 650
  QueenValueEn: 650
best mean goal: -0.6234573089733992
done iter 3!
=========================================
starting iter 4 ...
...
```

### C. Sample Optimization scenario
#### Computer with 8 threads
* Computer has 8 threads, either from 4 cores and 8 threads or 8 cores.
* You can use 4 threads for optimization, leave the other 4 threads for personal use.
* This optimizer needs to run 2 matches per iteration.
* In optimizer_setting.yml for cutechess section, set concurrency to 2 because 4 threads/2 is 2.
* So for match 1, set games per encounter to 2, set rounds to 2 set repeat to 2,  
that would generate 4 games from 2 games per encounter x 2 rounds. With concurrency of 2,  
2 games will be started automatically by cutechess.
* Meanwhile match 2 also starts with same conditions as in match 1. Match 1 and Match 2 will be run  
in parallel starting at iteration 2.
* Overall there are 8 games to be completed in every iteration in this setup.
* In both match 1 and 2, it is better to have more games so that the optimizer can give better prediction  
of optimal parameter values that will be tried in the next iteration. If you want 8 games in match 1 and 8  
games in match 2, just increase the number of rounds to 4, that is from 2 games per encounter x 4 rounds equals 8 games.

#### Computer with 16 threads
* You may use 12 threads for optimization.
* Set concurrency of cutechess to 6, match 1 will use 6 and match 2 will use 6 too.
* If you want 6 games in match 1 and 6 games in match 2, set games per encounter to 2 and set rounds to 3.  
6 games will be started by cutechess concurrently for match 1 and in parallel, 6 games will be started by cutechess for match 2.

### D. List of files in the directory ###

- *game_optimizer.py* : the main file of the package
- *spsa.py* : a general-purpose minimization algorithm (an improved version of the SPSA algorithm)
- *utils.py* : small utility functions
- *match.py* : a script to organize a match between two playing engines in any game (Go, Chess, etc..)
- *chess_game.py* : organize one game of Chess between two engines. Can be plugged into *match.py*
- *chess_match.py* : a specialized Chess version of *match.py*, more efficient because it uses parallelism for the match

### E. Sample run
[Sample piece values optimization](https://fsmosca.github.io/spsa/)
