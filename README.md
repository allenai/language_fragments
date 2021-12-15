Language Fragments
============

(still incomplete) repository for the code and data used in the following paper:
```
@inproceedings{richardson-aaai22,
  author    = {Richardson, Kyle, Ashish Sabharwal},
  title     = {{P}ushing the {L}imits of {R}ule {R}easoning in {T}ransformers
  through {N}atural {L}anguage {S}atisfiability},
  booktitle = {to appear at AAAI2022},
  year      = {2022},
  }
```
See details below.

Datasets
============

See `datasets/` for the different datasets, which are described below:

*3SAT datasets* in `data/3sat`

*2SAT datasets* in `data/2sat_pretraining`: this data was used for
 pre-training before training on the `3SAT` datasets above. 

*RuleTaker datasets* in `data/ruletaker_3ext_sat`: a version of the
 RuleTaker open world assumption (OWA) 3ext dataset available
 [here](https://allenai.org/data/proofwriter) lightly filtered to
 exclude some unsat examples and label assignments that differed from
 those produced by our solvers (< 2\% of the overall
 dataset). `data/hard_ruletaker/dev.jsonl`: the challenge dataset
 created using our 3SAT sampling technique and reported in the paper. 
  
General json schema we use for all datasets:
```json 
"context"  : If the dog is not red and the dog is not green then the dog is not young. If the dog is red and the dog is round then the dog is not big. If the dog is round and the dog is red then the dog is big. ..." ## <- the input
"answer" : "true" ##<-- the output
"meta" { ... } ##<-- additional information about instance 
```

Scripts for verifying the correctness of different datasets can be
found in `etc/data/{check_rc_fragment,check_ruletaker,check_rule_fragments}.py`,
some of which using the auxiliary solver code described below. 

Solver Code
============
We created various solvers for verifying the correctness of our
different datasets (and for potentially expanding our fragments to
include new datasets or reasoning problems), most relying on the [Z3 theorem prover](https://github.com/Z3Prover/z3). To load the necessary dependencies, we recommend using [conda](https://docs.conda.io/en/latest/miniconda.html) and doing the following
```
conda create -n language_fragments python==3.7
conda activate language_fragments
pip install -r requirements.txt
python -m spacy download en
```
To launch an example solver in Python, you can do the following:
```python 
>>> from language_fragments import BuildSolver, get_config
>>> config = get_config('solver')
>>> config.solver ## the type of solver being used
'smt_solver'
>>> solver = BuildSolver(config)
>>> solver
'<language_fragments.solver.SyllogisticSMTSolver at 0x7fdd69883a58>'

>>> solver.prove([
    "Every philosopher despises some cynic",
    "Every gentleman is a philosopher",
    "Every cynic is a man",
    "Every man is a human",
    "Socrates is a gentleman"
], query="Some gentleman despises some human")
'theory=sat, query=entailment'
## above: the model takes a `theory` (list of NL rules/facts) and an
# (optional) query, and deteremines the satisfiability of the theory
# and whether an entailment holds.

>>> solver.parse_problem([
        "Every philosopher despises some cynic",
        "Every gentleman is a philosopher",
        "Every cynic is a man",
        "Every man is a human",
        "Socrates is a gentleman"
        ],key='lf')
['ForAll([x],Implies(Philosopher(x),Exists([y],And(Cynic(y),Despise(x,y)))))',
 'ForAll([x],Implies(Gentleman(x),Philosopher(x)))',
 'ForAll([x],Implies(Cynic(x),Man(x)))',
 'ForAll([x],Implies(Man(x),Human(x)))',
 'Gentleman(socrate)']
## the internal representations generated and used directly by the solver
```
This implements some of the *language fragments* investigated in [Pratt-Hartmann 2003](http://www.cs.man.ac.uk/~ipratt/papers/nat_lang/jolli04.pdf) and the *RuleTaker language* from [Clark, Tadjford and Richardson 2020](https://arxiv.org/pdf/2002.05867.pdf).
```python

>>> from language_fragments import BuildSolver, get_config
>>> config = get_config('solver')
>>> config.parser = 'rule_taker'
>>> solver = BuildSolver(config)
>>> solver.parse_problem(
    ["The bald_eagle is big", 
     "The cat chases the squirrel", 
     "The cat needs the bald_eagle", 
     "The cat needs the tiger", 
     "The squirrel is blue", 
     "The squirrel needs the bald_eagle", 
     "The squirrel sees the bald_eagle", 
     "The squirrel sees the cat", 
     "The tiger chases the bald_eagle", 
     "The tiger chases the cat", 
     "The tiger is blue", 
     "The tiger is green", 
     "If the tiger chases the cat then the tiger is big", 
     "If someone chases the bald_eagle then the bald_eagle needs the cat", 
     "If someone is blue and they need the squirrel then the squirrel sees the bald_eagle", 
     "If the bald_eagle chases the cat and the cat chases the bald_eagle then the bald_eagle sees the squirrel",
     "If someone needs the tiger and the tiger needs the bald_eagle then they are red", 
     "Round people are green", 
     "If someone sees the cat and they chase the tiger then the cat sees the bald_eagle", 
     "If someone is big and blue then they chase the squirrel"],key='lf')
>>> pout = solver.prove(
    ["The bald_eagle is big", 
     "The cat chases the squirrel", 
     "The cat needs the bald_eagle", 
     "The cat needs the tiger", 
     "The squirrel is blue", 
     "The squirrel needs the bald_eagle", 
     "The squirrel sees the bald_eagle", 
     "The squirrel sees the cat", 
     "The tiger chases the bald_eagle", 
     "The tiger chases the cat", 
     "The tiger is blue", 
     "The tiger is green", 
     "If the tiger chases the cat then the tiger is big", 
     "If someone chases the bald_eagle then the bald_eagle needs the cat", 
     "If someone is blue and they need the squirrel then the squirrel sees the bald_eagle", 
     "If the bald_eagle chases the cat and the cat chases the bald_eagle then the bald_eagle sees the squirrel",
     "If someone needs the tiger and the tiger needs the bald_eagle then they are red", 
     "Round people are green", 
     "If someone sees the cat and they chase the tiger then the cat sees the bald_eagle", 
     "If someone is big and blue then they chase the squirrel"],query="The squirrel is blue")
```

When loading the configuration as above, setting `config.parser=...`
will load different rule languages. Below are the languages
implemented:
| default 	| Implements some of the fragments from Pratt-hartmann et al.  	|
|---	|---	|
| config.parser = 'rule_taker' 	| Implements the RuleTaker language with OWA classical semantics 	|
| config.parser = 'ground_rule_language' 	| Implements the grounded rule language from the paper 	|
The relative clause fragment from the paper does not yet have a full
implementation, but is partially implemented in the default parser. 


Transformer Code
============
*forthcoming* 

