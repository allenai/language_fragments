import sys
import os
import re
import logging
import argparse
import json
import shutil
import subprocess as subprocess
from optparse import OptionParser,OptionGroup
from language_fragments.base import ConfigurableClass,UtilityClass
from language_fragments.lang import BuildParser
from language_fragments.util.cache import LRUCache
from copy import deepcopy

from z3 import (
    DeclareSort,
    Function,
    BoolSort,
    Const,
    ForAll,
    Implies,
    Exists,
    And,
    Or,
    Not,
    Solver
)

## z3 keywords
Object = DeclareSort('Object')

Z3_GLOBALS = {
    "DeclareSort" : DeclareSort,
    "Function" : Function,
    "BoolSort" : BoolSort,
    "Const"    : Const,
    "ForAll"   : ForAll,
    "Implies"  : Implies,
    "Exists"   : Exists,
    "And"      : And,
    "Or"       : Or,    
    "Not"      : Not,
    "Solver"   : Solver,
    "Object"   : DeclareSort('Object'),
    "x"        : Const('x', Object), ## variables are mssed up below
    "y"        : Const('y', Object),
}

class SATResult(UtilityClass):

    def __init__(self):
        self.theory = None
        self.query  = None
        self.statistics = None

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "theory=%s, query=%s" % (self.theory,self.query)

    def __eq__(self,other):
        return self.theory == other.theory

class SolverBase(ConfigurableClass):
    """Base class for automated solver 
    """
    def prove(self,assumptions,query=None):
        """Provie something about a set of assumptions and (optionally) a query 

        :param assumptions: list of assumptions or axioms 
        :type assumptions: list 
        :param query: a query to those assumptions (optional) 
        :type query: str 
        """
        raise NotImplementedError

    def __call__(self,assumptions,query=None):
        return self.prove(assumptions,query)

class SatBasedSolvers(SolverBase):
    """Solvers that are based on Sat or SMT solvers

    :param _parser: the parser used for parsing the incoming 
        expressions used by the solver. 
    """
    @classmethod
    def from_config(cls,config):
        """Load from configuration. By default, this just returns 
        an object without any special initialization. 

        :param config: the global configuration object
        """
        parser = BuildParser(config)
        
        return cls(parser,config.solver_cache)

    def parse_problem(self,assumptions,key=None):
        """Conert a list of assumptions to propositional SAT 

        :param assumptions: the list of assumptions to parse 
        :param key: the type of format to return (defaults to `None` for all)
        """
        raise NotImplementedError


class SyllogisticSMTSolver(SatBasedSolvers):
    """Solvers that are based on Sat or SMT solvers, this one using 
    the `Z3` SMT solver. 
    """
    def __init__(self,parser,cache_size):
        """Create a `SyllogisticSMTSolver` instance 

        :param solver: the underlying z3 solver 
        :param parser: the parser for parsing expressions 
        """
        self.solver = Solver()
        self.parser = parser

        self._query_cache = LRUCache(cache_size)
        self.logger.info('Created solver, cache_size=%d' % cache_size)

    def _create_envs(self,statement_list,g,negated=False):
        """Creates an environment list from a statement 

        :param statement_list: 
        """
        for constant in statement_list.constants:
            if constant in g: continue 
            g[constant] = Const(constant,Object)
        for variable in statement_list.variables:
            if variable in g: continue 
            g[variable] = Const(variable,Object)

        for (var,arity) in statement_list.predicates:
            if var in g: continue 
            g[var] = Function(var,Object,BoolSort()) if arity == 1 else\
              Function(var,Object,Object,BoolSort())

        ## return list of evaluated statements
        if negated: 
            return [eval("Not(%s)" % str(s),g) for s in statement_list]
        return [eval(str(s),g) for s in statement_list]

    def prove(self,assumptions,query=None,debug=False):
        """Prove something about a set of assumptions and (optionally) a query. 

        In the case of a set of assumptions, will return whether that set of assumptions 
        is satisfiability or not. In the case of assumptions with a query, will first 
        check whether the assumptions are satisfiability, then whether the negation query 
        is unsatisfiability when added to the assumptions. 

        :param assumptions: list of assumptions or axioms 
        :type assumptions: list 
        :param query: a query to those assumptions (optional) 
        :type query: str 
        """
        assumptions = self.parser(assumptions)
        ## doesn't seem expensive, will allow for automatic garbage collection (I think) 
        g = deepcopy(Z3_GLOBALS)
        result_obj = SATResult()

        ## create axioms
        axioms = self._create_envs(assumptions,g)

        ## add to solver
        self.solver.add(axioms)
        theory_result = str(self.solver.check())
        result_obj.theory = theory_result
        result_obj.stats = self.solver.statistics()

        # ## run the query
        if query and theory_result == "unsat":
            result_obj.query = "no"
        elif query:
            query_list = self.parser([query])

            ## non-negated
            bare_query = self._create_envs(query_list,g,negated=False)[0]
            self.solver.add(bare_query)
            first_result = str(self.solver.check())
            if first_result == "unsat":
                result_obj.query = "contradiction"
            else:
                self.solver.reset()
                query = self._create_envs(query_list,g,negated=True)[0]
                self.solver.add(axioms)
                self.solver.add(query)
                query_result = str(self.solver.check())

                if query_result == "unsat":
                    result_obj.query = "entailment"
                else:
                    result_obj.query = "unknown"

        ## reset the solver 
        self.solver.reset()

        if debug:
            print("%s" % ' '.join([str(a) for a in assumptions]))
        
        return result_obj

    def parse_problem(self,assumptions,key=None):
        """Creates a dictionary of the different internal representations generated by 
        the parser 

        :param assumptions: the list of assumptions to parse 
        :param key: the type of format to return (defaults to `None` for all)
        """
        reps = {}
        assumptions = self.parser(assumptions)
        reps["lf"] = [str(a) for a in assumptions]
        if key is not None and key in reps:
            return reps[key]
        return reps

class SyllogisticSATSolver(SatBasedSolvers):
    pass

SOLVERS={
    "smt_solver" : SyllogisticSMTSolver,
}

def BuildSolver(config):
    """Factory for building a solver from configuration 

    :param config: the global configuration 
    :raises: ValueError
    """
    stype = SOLVERS.get(config.solver)
    if stype is None:
        raise ValueError('Unknown solver type: %s' % config.solver)
    return stype.from_config(config)
    
def params(config):
    """Main configuration settings for this module 

    :param config: a global configuration instance
    :rtype: None 
    """
    group = OptionGroup(config,"language_fragments.solver","Solver settings")

    ## add the parser params
    from language_fragments.lang import params as lparams
    lparams(config)
    
    group.add_option("--solver",
                          dest="solver",
                          default='smt_solver',
                          help="The type of solver to use [default='smt_solver']")

    group.add_option("--solver_cache",
                          dest="solver_cache",
                          default=3000,
                          type=int,
                          help="The size of cache to use for the solver [default=3000]")

    config.add_option_group(group)
