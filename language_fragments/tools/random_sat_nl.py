import os
import sys
import random
import logging
import itertools
import json
import tempfile
import tqdm
import inflect
import wandb
from collections import defaultdict
import numpy as np
from optparse import OptionParser,OptionGroup
from z3 import Solver
from language_fragments import initialize_config
from language_fragments.util.lex import *
from language_fragments.tools.sampler import params as sparams,set_seed
from transformers import T5Tokenizer

tokenizer = T5Tokenizer.from_pretrained('t5-large')

util_logger = logging.getLogger('reasoning_transformers.tools.random_sat_nl')

def translate_to_dimacs(problem,num_variables,num_clauses):
    """Translates problem into dimacs format 

    :param problem: raw list representation of problem 
    :param num_variables: the number of unique variables 
    :param num_clauses: the number of clauses in the overall formula
    """
    ret = "p cnf %s %s" % (num_variables,num_clauses)
    for clause in problem:
        line = ' '.join([str(p[-1]) if p[0] == 1 else "-%d" % p[-1]  for p in clause]+["0"])
        ret += '\n'+line
    return ret


SOLVER = Solver()

WANDB_ENTITY="nlsat"
WANDB_PROJECT="random-ksat"

def fixed_clause_length_interp_sampler(
        num_examples,
        m,
        k,
        n,
        interp_param=1.0,
        no_repeats=True,
    ):
    """Implementation of the Selman et al. `fixed clause length` SAT generator, with 
    the following parameters: clause size=`k`, number of clauses=`m`, negation probability=`p`,
    number of variables=`n`

    :param config: the global configuration, with all of these parameters inside 
    """
    sampled_examples = []
    bool_variables = np.array([k for k in range(n)],dtype=np.int32)
    negate_prob = np.array([1,0,],dtype=np.int32)

    pbar = tqdm.tqdm(total=num_examples)
    pbar.set_description("sampling %d, m=%d, k=%d, n=%d" % (num_examples,m,k,n))
    contain_full_variables = 0
    
    while len(sampled_examples) < num_examples:

        ## new problem
        new_problem = []
        predicate_assignment = {}
        variables_sampled = set() #<-- keep track of `non-trivial` cases
        
        for size in range(m):
            k_vars = []
            var_set = set()

            clause_size = np.random.choice([3,2],p=[interp_param,1.0-interp_param])

            # for variable in np.random.choice(bool_variables,clause_size,replace=not no_repeats):
            #     variable += 1
            #     negate = np.random.choice(negate_prob)

            #     var_set.add((negate,variable))
            #     k_vars.append((int(negate),int(variable)))
            #     variables_sampled.add(int(variable))
                
            #while len(k_vars) != k:            
            while len(k_vars) != clause_size:
                variable = np.random.choice(bool_variables)
                variable += 1
                negate = np.random.choice(negate_prob)
                opposite = 0 if negate == 1 else 1
                if (opposite,variable) in var_set: continue #<- ignore `trivial` cases
                if no_repeats and (negate,variable) in var_set: continue #<- ignore repeated props
                    
                var_set.add((negate,variable))
                k_vars.append((int(negate),int(variable)))
                variables_sampled.add(int(variable))

            ## assign to predicaets
            new_problem += [k_vars]

            ###
            if no_repeats:
                assert len(var_set) == clause_size,"repeat props!"

        ## assign predicates
        ## add example
        alpha = m/len(variables_sampled)
        if len(variables_sampled) == n:
            contain_full_variables += 1

        # ## map to dimacs
        dimacs = translate_to_dimacs(new_problem,len(variables_sampled),m)
        SOLVER.from_string(dimacs)
        sout = SOLVER.check()
        stats = SOLVER.statistics()

        try: 
            sat_decisions = stats.sat_decisions
        except:
            sat_decisions = 0
        ## record conflicts, if they exist 
        try: 
            sat_conflicts = stats.sat_conflicts
        except:
            sat_conflicts = 0
        try:
            sat_3ary = stats.sat_propagations_3ary
        except:
            sat_3ary = 0
        try:
            sat_nary = stats.sat_propagations_nary
        except:
            sat_nary = 0

        SOLVER.reset()

        ###
        instance = {
            "id" : "%d_%d_%d_%s" % (k,n,m,len(sampled_examples)),
            "alpha"         : alpha,
            "sat_decisions" : sat_decisions,
            "sat_conflicts" : sat_conflicts,
            "dimacs"        : dimacs,
            "problem"       : new_problem,
            "output"        : str(sout),
            "k"             : k if interp_param > 0.0 else 2,
            #"n"             : n,
            "m"             : m,
            "n"             : len(variables_sampled),
            "sat_3ary"      : sat_3ary,
            "sat_nary"      : sat_nary,
            "sat_prop"      : sat_3ary+sat_nary,
            "total_sat"     : sat_decisions+sat_3ary+sat_nary+sat_conflicts,
            "iterpolated"   : False if (interp_param == 1.0 or interp_param == 0.0) else True
        }

        sampled_examples.append(instance)
        pbar.update(1)

    util_logger.info('Finished, total with full variables: %d / %d' % (contain_full_variables,len(sampled_examples)))
    return sampled_examples

# def interpolated_sampler(
#         num_examples,
#         m,
#         k,
#         n
#     ):
#     """2+p sampler

#     :param config: the global configuration, with all of these parameters inside 
#     """
#     sampled_examples = []
#     bool_variables = np.array([k for k in range(n)],dtype=np.int32)
#     negate_prob = np.array([1,0,],dtype=np.int32)

#     pbar = tqdm.tqdm(total=num_examples)
#     pbar.set_description("sampling %d, m=%d, k=%d, n=%d" % (num_examples,m,k,n))
    
#     while len(sampled_examples) < num_examples:

#         ## new problem
#         new_problem = []
#         predicate_assignment = {}
#         variables_sampled = set() #<-- keep track of `non-trivial` cases
        
#         for size in range(m):
#             k_vars = []
#             var_set = set()

#             while len(k_vars) != k:
#                 variable = np.random.choice(bool_variables)
#                 variable += 1
#                 negate = np.random.choice(negate_prob)
#                 opposite = 0 if negate == 1 else 1
#                 if (opposite,variable) in var_set: continue #<- ignore `trivial` cases

#                 ## no repeats
                    
#                 var_set.add((negate,variable))
#                 k_vars.append((int(negate),int(variable)))
#                 variables_sampled.add(int(variable))

#             ## assign to predicaets
#             new_problem += [k_vars]


#         ## assign predicates
#         ## add example
#         alpha = m/len(variables_sampled)

#         # ## map to dimacs
#         dimacs = translate_to_dimacs(new_problem,len(variables_sampled),m)
#         SOLVER.from_string(dimacs)
#         sout = SOLVER.check()
#         stats = SOLVER.statistics()

#         try: 
#             sat_decisions = stats.sat_decisions
#         except:
#             sat_decisions = 0
#         ## record conflicts, if they exist 
#         try: 
#             sat_conflicts = stats.sat_conflicts
#         except:
#             sat_conflicts = 0
#         try:
#             sat_3ary = stats.sat_propagations_3ary
#         except:
#             sat_3ary = 0
#         try:
#             sat_nary = stats.sat_propagations_nary
#         except:
#             sat_nary = 0

#         SOLVER.reset()

#         ###
#         instance = {
#             "id" : "%d_%d_%d_%s" % (k,n,m,len(sampled_examples)),
#             "alpha"         : alpha,
#             "sat_decisions" : sat_decisions,
#             "sat_conflicts" : sat_conflicts,
#             "dimacs"        : dimacs,
#             "problem"       : new_problem,
#             "output"        : str(sout),
#             "k"             : k,
#             #"n"             : n,
#             "n"             : len(variables_sampled),
#             "m"             : m,
#             "sat_3ary"      : sat_3ary,
#             "sat_nary"      : sat_nary,
#             "sat_prop"      : sat_3ary+sat_nary,
#             "total_sat"     : sat_decisions+sat_3ary+sat_nary+sat_conflicts,
#         }

#         sampled_examples.append(instance)
#         pbar.update(1)

#     return sampled_examples

SAT_TEMPLATE = "If %s and %s, then %s."

INFLECT = inflect.engine()

NAMES = [
    male_names,
    female_names,
]

PROPERTIES = emotion_adj + [INFLECT.a(a) for a in count_professions] + colors + [INFLECT.a(a) for a in count_animals]

    
def synthesize_3sat(config,problems):
    """Synthesize 3sat problems into natural language 

    :param config: the global configuration 
    :param problems: the instances
    """
    for example in problems:
        variable_map = {}
        already = set()
        full_expression = []
        
        for problem in example["problem"]:
            v1,v2,v3 = problem
            needs_assignment = True
            
            ## sample a template
            vnames = [v1,v2,v3]
            local_expr = []

            ## randomly assign propositions 
            while True:
                try:
                    negation,new_var = vnames.pop()
                except:
                    break 

                ## already assigned 
                if new_var in variable_map: continue

                ## assign name 
                name_list = NAMES[np.random.randint(0,2)]
                rand_name = name_list[np.random.randint(0,len(name_list))]

                ## assign property
                rand_prop = PROPERTIES[np.random.randint(0,len(PROPERTIES))]
                rand_prop = rand_prop.replace("_"," ").lower()

                if (rand_name,rand_prop) in already:
                    vnames.append((negation,new_var))
                    continue
                already.add((rand_name,rand_prop))
                variable_map[new_var] = (rand_name,rand_prop)

            ## formulate expression
            new_expression = []
            for k,(negation,variable) in enumerate([v1,v2,v3]):
                if (k == 0 or k == 1):
                    expr = "%s is %s" if negation == 0 else "%s is not %s" #<- reverse 
                else: 
                    expr = "%s is %s" if negation == 1 else "%s is not %s"
                expr = expr % variable_map[variable]
                new_expression.append(expr)

                
            final = SAT_TEMPLATE % (new_expression[0],new_expression[1],new_expression[2])
            full_expression.append(final)

        ## add to instance
        full_expr = ' '.join(full_expression)
        example["question"] = {}
        example["question"]["stem"] = full_expr
        example["variable_map"] = ' '.join(["%d-%s" % (k,'_'.join(v).replace(" ","&")) for k,v in variable_map.items()])
        #print(example["variable_map"])
        del example["problem"]

def synthesize_non(config,problems):
    """Synthesize 3sat problems into natural language 

    :param config: the global configuration 
    :param problems: the instances
    """
    for example in problems:
        variable_map = {}
        already = set()
        full_expression = []

        for problem in example["problem"]:
            #v1,v2,v3 = problem
            needs_assignment = True
            full_expression.append(' '.join(["not %d" % v[-1] if v[0] == 0 else str(v[-1]) for v in problem]))
            
        full_expr = ' and '.join(full_expression)
        #print(len(tokenizer.tokenize(' and '.join(full_expression))))
        example["question"] = {}
        example["question"]["stem"] = full_expr
        example["variable_map"] = None
        del example["problem"]

def wandb_backup(config,problems,instances):
    """Log a graph of the results to wandb 

    :param problems: the list of problems characterized by alpha parameter
    """
    ## params along with their instances 
    used = [(a,[p[-1] for p in problems[a][:config.min_examples]]) for a in problems.keys() \
                            if len(problems[a]) >= config.min_examples]

    alpha_decisions = [[a,np.median([p[1] for p in problems[a][:config.min_examples]])] for a in problems.keys() \
                            if len(problems[a]) >= config.min_examples]
    alpha_conflicts = [[a,np.median([p[2] for p in problems[a][:config.min_examples]])] for a in problems.keys()\
                           if len(problems[a]) >= config.min_examples]
    alpha_prob = [[a,float(len([p[0] for p in problems[a][:config.min_examples] \
                                    if p[0] == "sat"])/len(problems[a][:config.min_examples]))] \
                      for a in problems.keys() if len(problems[a]) >= config.min_examples]

    alpha_total = [[a,np.median([p[3] for p in problems[a][:config.min_examples]])] for a in problems.keys() \
                            if len(problems[a]) >= config.min_examples]


    ## 3 tables 
    table1 = wandb.Table(data=alpha_decisions,
                             columns=["Clause/Variable Ratio","#SAT Decisions"]
    )
    table2 = wandb.Table(data=alpha_conflicts,
                             columns=["Clause/Variable Ratio","#SAT Conflicts"]
    )
    table3 = wandb.Table(data=alpha_prob,
                             columns=["Clause/Variable Ratio","Probability"]
    )

    table4 = wandb.Table(data=alpha_total,
                             columns=["Clause/Variable Ratio","# Total Decisions"]
    )

    ## load this to wandb 
    run = wandb.init(
        project=config.wandb_project,
        entity=config.wandb_entity,
        name=config.sample_name
    )

    ### only log if fixed clause length
    if config.interpolate_param == 1.0: 

        run.log({"hardness_table1" : wandb.plot.line(
            table1,"Clause/Variable Ratio","#SAT Decisions",
            title="SAT Decisions")})
    
        run.log({"hardness_table2" : wandb.plot.line(
            table2,"Clause/Variable Ratio","#SAT Conflicts",
            title="SAT Conflicts")})

        run.log({"total_table4" : wandb.plot.line(
            table4,"Clause/Variable Ratio","# Total Decisions",
            title="SAT Total Decisions")})
    
    run.log({"probability_table3" : wandb.plot.line(
        table3,"Clause/Variable Ratio","Probability",
        title="SAT Probaility")})

    a_avg = np.mean([len(v) for k,v in problems.items()])

    run.log({
        "n"             : config.n,
        "m"             : config.m,
        "k"             : config.k,
        "num_sampled"   : config.num_examples,
        "avg_per_alpha" : a_avg,
        "seed"          : config.seed,
    })

    ### back up the data
    artifact = wandb.Artifact("%s_dump" % config.sample_name.replace("=","-"),type='dataset')

    ### add to temporary directory 
    with tempfile.TemporaryDirectory() as temp_dir:
        util_logger.info('Backing up to %s' % temp_dir)

        ## raw instances 
        raw_instances = os.path.join(temp_dir,"raw_instances.jsonl")
        with open(raw_instances,'w') as temp_out:
            for instance in instances:
                temp_out.write(json.dumps(instance))
                temp_out.write("\n")

        ## the used instances 
        used_instances = os.path.join(temp_dir,"used_instances.jsonl")
        with open(used_instances,'w') as temp_used:
            temp_used.write(json.dumps(used))
            temp_used.write("\n")

        #artifact.add_file(tf_instances.name)
        artifact.add_dir(temp_dir)
        run.log_artifact(artifact)
        run.finish()

    # with tempfile.NamedTemporaryFile() as tf_instances:
    #     with tempfile.NamedTemporaryFile() as tf_used:
    #         util_logger.info('Backing up data to: %s, used_instances=%s' % (tf_instances.name,tf_used.name))
    #         with open(tf_instances.name,'w') as temp_out:
    #             for instance in instances:
    #                 temp_out.write(json.dumps(instance))
    #                 temp_out.write("\n")

    #         with open(tf_used.name,'w') as temp_used:
    #             temp_used.write(json.dumps(used))
    #             temp_used.write("\n")

    #         artifact.add_file(tf_instances.name)
    #         artifact.add_file(tf_used.name)
    #         run.log_artifact(artifact)
    #         run.finish()


def sample(config):
    """Main entry point for running the solvers 
    
    :param config: the global configuration 
    """
    util_logger.info(
        'sampling, sampler=%s, no_repeats=%s' % (
            config.sample_type,
            str(config.no_repeats),
            ))
    
    ## if no minimum set, plot only items that are near maximum
    if config.min_examples == -1:
        config.min_examples = int(config.num_examples*0.9)
    
    num_examples = config.num_examples
    total_problems = []
    alpha_tracker = defaultdict(list)

    if config.sample_type == "fixed_length_sampler":
        
        for clause_size in str(config.k).split(";"):
            for num_clauses  in str(config.m).split(";"):
                for num_variables in str(config.n).split(";"):

                    ## sample the problems 
                    problems = fixed_clause_length_interp_sampler(
                        num_examples,
                        int(num_clauses),
                        int(clause_size),
                        int(num_variables),
                        interp_param=float(config.interpolate_param),
                        no_repeats=config.no_repeats,
                    )

                    for instance in problems:
                        alpha = instance["alpha"]
                        alpha_tracker[alpha].append([
                            instance["output"],
                            instance["sat_decisions"],
                            instance["sat_conflicts"],
                            instance["total_sat"],
                            instance["id"],
                        ])
                        total_problems.append(instance)

    elif config.sample_type == "naive_sampler":
        sampled = 0

        while sampled < config.total_examples:

            num_clauses = np.random.randint(
                config.clause_min,
                config.clause_max+1
            )

            problems = fixed_clause_length_interp_sampler(
                        20,
                        num_clauses,
                        int(config.k),
                        int(config.n),
                        interp_param=float(config.interpolate_param),
                        no_repeats=config.no_repeats
            )

            for instance in problems:
                alpha = instance["alpha"]
                alpha_tracker[alpha].append([
                    instance["output"],
                    instance["sat_decisions"],
                    instance["sat_conflicts"],
                    instance["total_sat"],
                    instance["id"],
                ])
                total_problems.append(instance)
                sampled += 1

    else:
        raise ValueError('Unknown sampler type!')

    ### synthesisze
    if config.synthesize_to_nl: 
        synthesize_3sat(config,total_problems)
    elif config.synthesize_to_non_nl:
        synthesize_non(config,total_problems)

    ### graph the results?
    if config.print_data:
        wandb_backup(config,alpha_tracker,total_problems)

def params(config):
    """Main configuration settings for this module 

    :param config: a global configuration instance
    :rtype: None 
    """
    from language_fragments.tools.sampler import params as sparams
    sparams(config)

def main(argv):
    """The main execution point 

    :param argv: the cli input 
    """
    ## set up config and get working directory set up
    config = initialize_config(argv,params)

    ## set seed and grab predicates
    set_seed(config)

    #fixed_clause_length_sampler(config)
    sample(config)
