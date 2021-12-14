import os
import sys
import json
import re
from tqdm import tqdm


CURRENT_PATH = os.path.abspath(__file__)
SOLVER_PATH = os.path.abspath(
    os.path.join(CURRENT_PATH,"../../../")
)

sys.path.append(SOLVER_PATH)

###SOLVER 
from language_fragments import get_config, BuildParser,BuildSolver
from language_fragments.lang.logic_builders import *

CONFIG = get_config("solver")
CONFIG.parser = 'rule_taker'
CONFIG.parser_cache = 50000
CONFIG.solver_cache = 10000

SOLVER = BuildSolver(CONFIG)

### DATA
ORIG_PATH = os.path.abspath(
    os.path.join(current_path,"../ruletaker_3ext_sat/")
)
CHALLENGE_PATH = os.path.abspath(
    os.path.join(current_path,"../hard_ruletaker/")
)
ANNOTATION_MAP = {
    "true"    : "entailment",
    "false"   : "contradiction",
    "unknown" : "unknown",
}

def parse_lf(raw_lf,raw_expr):
    fact = False
    entities = None
    template = raw_expr 
    if "Implies" not in raw_lf and "ForAll" not in raw_lf:
        fact = True
        arg_pattern = re.search(
            r'\((.+)\)',
            raw_lf.replace("Not(","")
        ).groups()[0]
        entities = [e.strip().replace(")","") for e in arg_pattern.split(",")]
        for e in entities: template = template.lower().replace(e,"x")
    elif "Implies" in raw_lf:
        raw_lf = raw_lf.replace("And(","").\
          replace("Not(","").\
          replace("ForAll(","").\
          replace("Implies(","").\
          replace("[x],","").strip()

        preds = [
            i.replace("(x","").replace(")","").replace(")","").replace("("," ")
            for i in raw_lf.split(",")
        ]
        for p in preds:
            for piece in p.split():
                template = template.lower().replace(piece.lower(),"x")

    return raw_lf,fact,entities,template
        


if __name__ == "__main__":
    train_statements = set()
    train_facts = set()
    train_labels = set()
    train_entities = set()
    train_templates = set()
    train_rule_templates = set()

    ### ORIGINAL TRAINING AND DEV DATA
    for split in [
            "train.jsonl", ### takes about 50 minutes to verify 
            #"dev.jsonl",    ### takes about 10 minutes to verify 
        ]:
        training = True if "train." in split else False
        total_queries = 0
        matched_queries = 0
        
        with open(os.path.join(ORIG_PATH,split)) as my_data:
            print(f"PARSING ORIGINAL FILE: {split}, verifying correctness (might take a while)")
            for line in tqdm(my_data):
                line = line.strip()
                json_line = json.loads(line)

                sentences = [s.strip() for s in json_line["context"].split(". ")]
                last_statement,query = sentences[-1].split(" $query$ ")
                theory = sentences[:-1]+[last_statement.strip()]

                if training is True:
                    for item in theory: train_statements.add(item)

                normalized_label = ANNOTATION_MAP[json_line["answer"].strip()]
                train_labels.add(json_line["answer"])

                ### parse out 
                for k,lf in enumerate(SOLVER.parse_problem(theory)["lf"]):
                    _,is_fact,entities,template = parse_lf(lf,theory[k])
                    if is_fact and training is True:
                        train_templates.add(template)
                    elif training is True:
                        train_rule_templates.add(template) 

                    if is_fact and training is True:
                        train_facts.add(lf)
                    if entities and training is True:
                        for e in entities: train_entities.add(e)

                prover_out = SOLVER.prove(theory,query=query)
                total_queries += 1
                if prover_out.query == normalized_label:
                    matched_queries += 1

            print(f"RESULTS for {split}")
            print(f"matched queries {matched_queries} / {total_queries} ({matched_queries/total_queries})")

    ### CHALLENGE SPLIT

    correct_label = 0
    total_problems = 0
    matched_queries = 0
    matched_facts = 0
    dev_entities = set()
    dev_facts = set()
    dev_templates = set()
    dev_rule_templates = set()
    
    print(f"PARSING HARD SET AND VERIFYING (might take a while)")
    with open(os.path.join(CHALLENGE_PATH,"dev.jsonl")) as challenge_set:
        for line in tqdm(challenge_set):
            line = line.strip()
            json_line = json.loads(line)
            sentences = [s.strip() for s in json_line["context"].split(". ")]
            last_statement,query = sentences[-1].split(" $query$ ")
            theory = sentences[:-1]+[last_statement.strip()]

            total_problems += 1
            if json_line["answer"] in train_labels: correct_label += 1

            for k,lf in enumerate(SOLVER.parse_problem(theory)["lf"]):
                _,is_fact,entities,template = parse_lf(lf,theory[k])
                if is_fact:
                    dev_facts.add(lf)
                    dev_templates.add(template)
                    for e in entities: dev_entities.add(e)
                else:
                    dev_rule_templates.add(template)

            ### run prover
            normalized_label = ANNOTATION_MAP[json_line["answer"].strip()]
            prover_out = SOLVER.prove(theory,query=query)
            if prover_out.query == normalized_label:
                matched_queries += 1

    print("Results on eval set")
    print("----------------------")
    print(f"Matching labels: {correct_label} / {total_problems} {correct_label/total_problems}")
    print(f"Seen facts: {len([f for f in dev_facts if f in train_facts])} / {len(dev_facts)} {len([f for f in dev_facts if f in train_facts])/len(dev_facts)}")
    print(f"Seen entities: {len([e for e in dev_entities if e in train_entities])/len(dev_entities)}")
    print(f"Seen templates: {len([e for e in dev_templates if e not in train_templates])} / {len(dev_templates)} ({len([e for e in dev_templates if e not in train_templates])/len(dev_templates)})")
    print(f"Seen rule templates: {len([e for e in dev_rule_templates if e in train_rule_templates])} / {len(dev_rule_templates)} ({len([e for e in dev_rule_templates if e in train_rule_templates])/len(dev_rule_templates)})")

