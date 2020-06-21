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
Upcoming update.
```
...
parameters to optimize = QueenValueOp 650 550 750 1000, QueenValueEn 650 550 750 1000
starting iter 1 ...
current param:
  QueenValueOp: 650
  QueenValueEn: 650
Run engine match ...
current optimizer mean goal: 1.00000 (low is better, lowest: -1.0, highest: 1.0)
Run match 1 ...
param to use:
  QueenValueOp: 550, delta: -100
  QueenValueEn: 750, delta: +100
Done match 1!
Run match 2 ...
param to use:
  QueenValueOp: 750, delta: +100
  QueenValueEn: 550, delta: -100
Done match 2!
optimizer goal after match 1: -0.99829 (low is better)
optimizer goal after match 2: 0.00171 (low is better)
Basic gradient after 2 engine matches:
  QueenValueOp: 5.0
  QueenValueEn: -5.0
New gradient after applying correction:
  QueenValueOp: 0.049999999999999975
  QueenValueEn: -0.049999999999999975
Done engine match!
new param after application of gradient:
  QueenValueOp: 646
  QueenValueEn: 653
new param after application of limits:
  QueenValueOp: 646
  QueenValueEn: 653
new param after application of best average param:
  QueenValueOp: 646
  QueenValueEn: 653
new param after application of limits:
  QueenValueOp: 646
  QueenValueEn: 653
best param:
  QueenValueOp: 646
  QueenValueEn: 653
done iter 1!
=========================================
starting iter 2 ...
current param:
  QueenValueOp: 646
  QueenValueEn: 653
Run engine match ...
current optimizer mean goal: -0.49829 (low is better, lowest: -1.0, highest: 1.0)
Run 2 matches in parallel ...
Run match 1 ...
param to use:
  QueenValueOp: 720, delta: +74
  QueenValueEn: 681, delta: +28
Run match 2 ...
param to use:
  QueenValueOp: 572, delta: -74
  QueenValueEn: 625, delta: -28
Done match 1!
Done match 2!
optimizer goal after match 1: 0.00091 (low is better)
optimizer goal after match 2: -0.74911 (low is better)
Basic gradient after 2 engine matches:
  QueenValueOp: 5.094206099468385
  QueenValueEn: 13.584549598582361
New gradient after applying correction:
  QueenValueOp: 0.10533991588989927
  QueenValueEn: 0.24955644237306476
Done engine match!
new param after application of gradient:
  QueenValueOp: 639
  QueenValueEn: 636
new param after application of limits:
  QueenValueOp: 639
  QueenValueEn: 636
new param after application of best average param:
  QueenValueOp: 638
  QueenValueEn: 636
new param after application of limits:
  QueenValueOp: 638
  QueenValueEn: 636
best param:
  QueenValueOp: 638
  QueenValueEn: 636
done iter 2!
=========================================
starting iter 3 ...
current param:
  QueenValueOp: 638
  QueenValueEn: 636
Run engine match ...
current optimizer mean goal: -0.43620 (low is better, lowest: -1.0, highest: 1.0)
Run 2 matches in parallel ...
Run match 1 ...
param to use:
  QueenValueOp: 699, delta: +61
  QueenValueEn: 616, delta: -20
Run match 2 ...
param to use:
  QueenValueOp: 578, delta: -60
  QueenValueEn: 655, delta: +19
Done match 1!
Done match 2!
optimizer goal after match 1: -0.24929 (low is better)
optimizer goal after match 2: -0.49926 (low is better)
Basic gradient after 2 engine matches:
  QueenValueOp: 2.0741473575790126
  QueenValueEn: -6.358052776468576
New gradient after applying correction:
  QueenValueOp: 0.08190179887593763
  QueenValueEn: -0.11143641394750783
Done engine match!
new param after application of gradient:
  QueenValueOp: 633
  QueenValueEn: 643
new param after application of limits:
  QueenValueOp: 633
  QueenValueEn: 643
new param after application of best average param:
  QueenValueOp: 632
  QueenValueEn: 643
new param after application of limits:
  QueenValueOp: 632
  QueenValueEn: 643
best param:
  QueenValueOp: 632
  QueenValueEn: 643
done iter 3!
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
