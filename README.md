# Optimizer for games

Optimizer for game coefficients using the SPSA algorithm.
Author: Stéphane Nicolet

### Installation
* On windows
  * Install python 3.8 from https://www.python.org/downloads/  
  * Install requirements.txt  
  `pip install -r requirements.txt`
  * Download this repo as it already contains sample engines and cutechess-cli tourney manager.  
  Press `Clone->Download ZIP` at the top-right of this page.
  * Edit optimizer_setting.yml with notepad or notepad++ to set the engine and cutechess options.
  * Run the optimizer
  `python game_optimizer.py iteration 10000`

### Usage:  
`python game_optimizer.py --iteration 1000`

#### Sample output from console
```
...
starting iter 167 ...
current param:
  QueenValueOp: 633
  QueenValueEn: 734
  ck: 0.05411
  ak: 0.02546
Run engine match ...
current optimizer average goal: -0.40454 (low is better)
Run 2 matches in parallel ...
Run match 1 ...
param to use:
  QueenValueOp: 645
  QueenValueEn: 710
Run match 2 ...
param to use:
  QueenValueOp: 622
  QueenValueEn: 750
Done match 1!
Done match 2!
optimizer goal after match 1: -0.49884169145813706 (low is better)
optimizer goal after match 2: -0.49937300450957006 (low is better)
Basic gradient after 2 engine matches:
  QueenValueOp: 0.023198056267053235
  QueenValueEn: -0.010971817016388493
New gradient after applying correction:
  QueenValueOp: -1.442036239487017
  QueenValueEn: 0.4365528930954838
Done engine match!
new param after application of gradient:
  QueenValueOp: 670
  QueenValueEn: 723
new param after application of limits:
  QueenValueOp: 670
  QueenValueEn: 723
new param after application of best average param:
  QueenValueOp: 668
  QueenValueEn: 723
new param after application of limits:
  QueenValueOp: 668
  QueenValueEn: 723
best param:
  QueenValueOp: 668
  QueenValueEn: 723
done iter 167!
=========================================
...
```

### List of files in the directory ###

- *game_optimizer.py* : the main file of the package
- *spsa.py* : a general-purpose minimization algorithm (an improved version of the SPSA algorithm)
- *utils.py* : small utility functions
- *match.py* : a script to organize a match between two playing engines in any game (Go, Chess, etc..)
- *chess_game.py* : organize one game of Chess between two engines. Can be plugged into *match.py*
- *chess_match.py* : a specialized Chess version of *match.py*, more efficient because it uses parallelism for the match

### Sample run
[Queen piece value optimization](https://github.com/fsmosca/spsa/wiki/Sample-run)
