import re
import os
import sys
import json
import re
from tqdm import tqdm
from collections import defaultdict
import numpy as np

from z3 import * #<--- sat solver machinery 

### pointer to the combined relative clause data
CURRENT_PATH = os.path.abspath(__file__)

ORIG_PATH = os.path.abspath(
    os.path.join(CURRENT_PATH,"../3sat/grounded_rule_lang/combined/")
)

SOLVER_PATH = os.path.abspath(
    os.path.join(CURRENT_PATH,"../../../")
)

sys.path.append(SOLVER_PATH)

###SOLVER 
from language_fragments import get_config, BuildParser,BuildSolver
from language_fragments.lang.logic_builders import *


SOLVER = Solver() #<-- z3 solver


def run_solver(dimacs,gold):
    mean_conflicts = []
    mean_decisions = []
    mean_backjumps = []
    first_props = []
    second_props = []

    for i in range(SOLVER_RUNS):
        SOLVER.from_string(dimacs)
        sout = str(SOLVER.check())
        normed_out = "yes" if sout == "sat" else "no"
        if normed_out == "no": assert sout == "unsat"
        assert normed_out == gold,"wrong answer"
        stats = SOLVER.statistics()

        

        try: conflicts = stats.sat_conflicts
        except AttributeError: conflicts = 0
        try: decisions = stats.sat_decisions
        except AttributeError: decisions = 0
        try: backjumps = stats.sat_backjumps
        except AttributeError: backjumps = 0
        try: props_2 = stats.sat_propagations_2ary
        except: props_2 = 0
        try: props_3 = stats.sat_propagations_3ary
        except: props_3 = 0

        first_props.append(props_2)
        second_props.append(props_3)

        mean_backjumps.append(backjumps) 
        mean_conflicts.append(conflicts)
        mean_decisions.append(decisions)

        SOLVER.reset()

    avg_conflicts = np.round(np.mean(mean_conflicts))
    avg_jumps = np.round(np.mean(mean_backjumps))
    avg_decisions = np.round(np.mean(mean_decisions))
    avg_props1 = np.round(np.mean(first_props))
    avg_props2 = np.round(np.mean(second_props))
    return (avg_conflicts,avg_jumps,avg_decisions,avg_props1,avg_props2)

def convert_rep(rep):
    var_map = {}
    total_vars = set()
    dimacs_list = []
    ## hack to deal with `pineapple` and `apple` overlap
    rep = rep.replace("pineapple","bababa")
    
    for clause in rep.split(". "):
        normalized_clause = clause.strip().replace("no ","-").replace('If','').\
          replace('and','').replace('then','').strip()

        assert len(normalized_clause.split()) == 3

        for k,variable in enumerate(normalized_clause.split()):
            raw_var = variable 
            variable = variable.strip().replace("-","") #.replace("pineapple","ppapap")
            if variable not in var_map: 
                var_map[variable] = len(var_map) + 1

            normalized_clause = normalized_clause.replace(
                variable,str(var_map[variable])
            )
            total_vars.add(var_map[variable])

        ####
        switched = []
        for k,item in enumerate(normalized_clause.split()):
            if k < 2:
                normalized = "-%s" % item if "-" not in item else item.replace("-","").strip()
                switched.append(normalized)
            else:
                switched.append(item)

        assert len(switched) == 3
        dimacs_list.append(' '.join(switched)+" 0")  
        
    ret = "p cnf %s %s" % (len(total_vars),len(dimacs_list))
    dimacs = "%s\n%s" % (ret,'\n'.join(dimacs_list))
    inverse_map = {v:k for k,v in var_map.items()}
    assert len(var_map) == len(total_vars) == len(inverse_map)
    return (dimacs.strip(),len(dimacs_list)/len(total_vars),inverse_map)


MAX_DATA = 10000   #<---- 
SOLVER_RUNS = 1    #<--- number of times to call solver (set to > 1 to compile statistics, we chose 10 for the statistics in the paper)


### CHECK VIA SAT 

for split in [
        #"train.jsonl",
        #"dev.jsonl",
        #"test.jsonl",
    ]:

    print(f"VERIFYING split={split}, might take a while...")
    with open(os.path.join(ORIG_PATH,split)) as my_data:
        total_queries = 0
        correct_queries = 0

        for k,line in enumerate(tqdm(my_data)):
            json_line = json.loads(line.strip())
            context = json_line["context"]

            dimacs,ratio,inverse_map = convert_rep(context)
            try: 
                run_solver(dimacs,json_line["answer"])
                correct_queries += 1
            except AssertionError:
                pass 

            total_queries += 1 

            if k > MAX_DATA:
                break
    print(f"split={split}, Verified {correct_queries} / {total_queries} queries ({correct_queries/total_queries})")



CONFIG = get_config("solver")
CONFIG.parser = 'ground_rule_language'
CONFIG.parser_cache = 50000
CONFIG.solver_cache = 10000

SMT_SOLVER = BuildSolver(CONFIG)

for split in [
        #"train.jsonl",
        #"dev.jsonl",
        #"test.jsonl",
    ]:
    matching = 0
    total = 0

    print(f"VERIFYING split={split} with SMT solver, might take a while...")
    with open(os.path.join(ORIG_PATH,split)) as my_data:
        for k,line in enumerate(tqdm(my_data)):
            json_line = json.loads(line.strip())
            context = json_line["context"]
            answer = json_line["answer"]
            normalized = "sat" if answer == "yes" else "unsat"

            if k > 30000: break

            prove_out = SMT_SOLVER.prove(context.split(". "))
            decision = prove_out.theory
            if normalized == decision: matching += 1
                
            total += 1

    print(f"Total matches: {matching} / {total} ({matching/total})")
