from optparse import OptionParser,OptionGroup
from language_fragments.lang.rule_lang import RuleParser
from language_fragments.lang.ruletaker_lang import RuleTakerParser
from language_fragments.lang.ground_rule_lang import GroundedRuleParser

def params(config):
    """Main parameters

    :param config: the global configuration 
    """
    from language_fragments.lang.parser import params as pparams
    pparams(config)

    group = OptionGroup(config,"langauge_fragments.lang",
                            "Settings for different parsers")
    group.add_option("--parser",
                          dest="parser",
                          default='rule_parser',
                          help="The type of parser to use [default='rule_parser']")

    config.add_option_group(group)

_PARSERS = {
    "rule_parser"          : RuleParser,
    "rule_taker"           : RuleTakerParser,
    "ground_rule_language" : GroundedRuleParser,
}
    
def BuildParser(config):
    """Factory method for building a parser 

    :param config: the global configuration 
    :return: an instantiated, usable grammar 
    :raises: ValueError 
    """
    ptype = _PARSERS.get(config.parser)
    if ptype is None:
        raise ValueError(
            'Unknown parser type: %s' % config.parser 
        )
    return ptype.from_config(config)
