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
    os.path.join(CURRENT_PATH,"../3sat/relative_clause/combined/")
)

SOLVER = Solver() #<-- z3 solver 

def convert_rep(context):
    """Converts a relative clause theory or `context` to a dimacs and sat representation. 

    :param context: the target context 
    """
    rule_clauses = []
    fact_clauses = []
    characters = set()
    
    for line in context.split(". "):
        ### fact line
        rep = re.sub(r'\s+',' ',re.sub(r'\b(a|an|is|who)\b','',line))
        rep = re.sub(r'not ','-',rep)
        rep = re.sub(r'person','',rep)

        if 'Every' in rep or 'Everything' in rep:
            rep = rep.replace('and','').replace('Everyone','').replace("Every",'').strip()
            rep = re.sub(r'\s+',' ',rep)
            rep1,rep2,rep3 = rep.split()
            rep1 = "-%s" % rep1 if "-" not in rep1 else "%s" % rep1.replace("-","")
            rep2 = "-%s" % rep2 if "-" not in rep2 else "%s" % rep2.replace("-","")
            rule_clauses.append("%s %s %s" % (rep1,rep2,rep3))

            
        elif 'No' in rep:
            rep = rep.replace('No','').strip()
            rep = re.sub(r'\s+',' ',rep)
            rep1,rep2,rep3 = rep.split()
            assert '-' not in rep3
            assert '-' not in rep1
            
            rep3 = "-%s" % rep3
            rep1 = "-%s" % rep1 if "-" not in rep1 else "%s" % rep1.replace("-","")
            rep2 = "-%s" % rep2 if "-" not in rep2 else "%s" % rep2.replace("-","")


            
            rule_clauses.append("%s %s %s" % (rep1,rep2,rep3))

        elif 'or' in rep:
            character = rep.split()[0]
            assertions = ' '.join(rep.split()[1:])
            characters.add(character) 

            assertions = assertions.replace(" or "," ")
            ass = ' '.join(["%s_%s" % (a,character) for a in assertions.split()])
            fact_clauses.append(ass)
        else:
            raise ValueError(
                'Unparse-able structure: %s' % rep
            )

    #### expand out
    expanded_rule_clauses = []
    for clause in rule_clauses:
        for character in characters:
            ass = ' '.join(["%s_%s" % (c,character) for c in clause.split()])
            expanded_rule_clauses.append(ass)

    ###
    var_map = {}
    new_dimacs = []

    for clause in fact_clauses + expanded_rule_clauses:
        local_m = []
        for literal in clause.split():
            raw_var = literal.replace("-","").strip()
            if raw_var not in var_map:
                var_map[raw_var] = len(var_map) + 1
            new = literal.replace(raw_var,str(var_map[raw_var]))
            local_m.append(new)
        new_dimacs.append("%s 0" % ' '.join(local_m))

    dimacs_header = "p cnf %d %d" % (len(var_map),len(new_dimacs))
    dimacs = "%s\n%s" % (dimacs_header,'\n'.join(new_dimacs))

    return (dimacs,len(new_dimacs)/len(var_map),
                {v:k for k,v in var_map.items()})





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
    return (avg_conflicts,
                avg_jumps,
                avg_decisions,
                avg_props1,
                avg_props2)

MAX_DATA = 10000   #<---- 
SOLVER_RUNS = 1    #<--- number of times to call solver (set to > 1 to compile statistics)

for split in [
        #"train.jsonl",
        "dev.jsonl",
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
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   



for split in [
        #"train.jsonl",
        "dev.jsonl",
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
