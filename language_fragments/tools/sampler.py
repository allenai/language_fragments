import logging
import random
import numpy as np
from optparse import OptionParser,OptionGroup

util_logger = logging.getLogger('reasoning_transformers.tools.sampler')

def set_seed(config):
    """Set the random seed 

    :param config: the global configuration.
    """
    #util_logger.info('Setting random seed: %s' % config.seed)
    random.seed(config.seed)
    np.random.seed(config.seed)

def params(config):
    """Main configuration settings for this module 

    :param config: a global configuration instance
    :rtype: None 
    """
    group = OptionGroup(config,"language_fragments.tools.sampler",
                            "Sampler parameters")

    group.add_option("--sample_name",
                         dest="sample_name",
                         default=3,
                         help="the type of sampling run [default='generic']")
    
    group.add_option("--k",
                         dest="k",
                         default=3,
                         help="the type of SAT problems to consider [default=3]")

    group.add_option("--m",
                         dest="m",
                         default=3,
                         help="the number of clauses [default=3]")

    group.add_option("--p",
                         dest="p",
                         default=0.5,
                         type=float,
                         help="the negation probability [default=3]")

    group.add_option("--num_examples",
                         dest="num_examples",
                         default=2000,
                         type=int,
                         help="The number of examples to sample [default=10000]")

    group.add_option("--min_examples",
                         dest="min_examples",
                         default=-1,
                         type=int,
                         help="The minimum number of examples to plot/keep [default=-1]")

    group.add_option("--n",
                         dest="n",
                         default=20,
                         help="the number of variables [default=3]")
    
    group.add_option("--ofile",
                         dest="ofile",
                         default='',
                         help="The path to re-direct the generated output [default='']")
    
    group.add_option("--seed",
                         dest="seed",
                         default=42,
                         type=int,
                         help="The random seed to use [default=42]")

    group.add_option("--total_examples",
                         dest="total_examples",
                         default=20000,
                         type=int,
                         help="The total number of examples to sample [default=20000]")

    group.add_option("--clause_min",
                         dest="clause_min",
                         default=5,
                         type=int,
                         help="The total number of examples to sample [default=20000]")

    group.add_option("--clause_max",
                         dest="clause_max",
                         default=20,
                         type=int,
                         help="The total number of examples to sample [default=20000]")

    group.add_option("--interpolate_param",
                         dest="interpolate_param",
                         default=1.0,
                         type=float,
                         help="The interpolation parameter [default=0.6]")

    group.add_option("--num_paramater_find",
                         dest="num_parameter_find",
                         default=8,
                         type=int,
                         help="The number of parameters to find [default=5]")
    
    group.add_option("--print_data",
                         dest="print_data",
                         action='store_true',
                         default=False,
                         help="Print the data out [default=False]")

    group.add_option("--compute_stats",
                         dest="compute_stats",
                         action='store_true',
                         default=False,
                         help="Compute just stats for the sampler [default=False]")

    group.add_option("--synthesize_to_nl",
                         dest="synthesize_to_nl",
                         action='store_true',
                         default=False,
                         help="Translate the data into natural language/english [default=False]")

    group.add_option("--no_repeats",
                         dest="no_repeats",
                         action='store_true',
                         default=False,
                         help="No repeat propositions allowed in each clause [default=False]")

    group.add_option("--synthesize_to_non_nl",
                         dest="synthesize_to_non_nl",
                         action='store_true',
                         default=False,
                         help="Translate the data into natural language/english [default=False]")

    group.add_option("--predicate_file",
                         dest="predicate_file",
                         default='',
                         type=str,
                         help="A list of predicate names [default='']")

    group.add_option("--constant_file",
                         dest="constant_file",
                         default='',
                         type=str,
                         help="A list of constant names [default='']")

    group.add_option("--main_parameter",
                         dest="main_parameter",
                         default='avg_pred_occ',
                         type=str,
                         help="The main parameter to optimize for [default='avg_pred_occ']")

    group.add_option("--sample_type",
                         dest="sample_type",
                         default='fixed_length_sampler',
                         type=str,
                         help="The type of sampler to use [default='fixed_length_sampler']")

    group.add_option("--fragment",
                         dest="fragment",
                         default='relative_clause',
                         help="The type of fragment to sample from [default='relative_clause']")

    group.add_option("--fragment_sampler",
                         dest="fragment_sampler",
                         default='random_nl_sat',
                         type=str,
                         help="The type of fragment sampler to use [default='random_nl_sat']")

    group.add_option("--num_theories",
                         dest="num_theories",
                         default=5000,
                         type=int,
                         help="The number of theories to sample [default=5000]")

    group.add_option("--num_preds",
                         dest="num_preds",
                         default="3",
                         #type=int,
                         help="The number of predicates to use (maximum 26) [default=3]")

    group.add_option("--num_cons",
                         dest="num_cons",
                         default="3",
                         #type=int,
                         help="The number of constants to use (maximum 26) [default=3]")

    config.add_option_group(group)
