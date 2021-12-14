import re
import logging
from language_fragments.lang.rule_lexer import RuleLexerGenerator
from language_fragments.lang.parser import LogicParser,LFTranslation,SpacyEnParser
from language_fragments.lang.logic_builders import *
from language_fragments.lang.lexicon import RULE_TAKER_KEYWORDS
from language_fragments.base import UtilityClass,ConfigurableClass
from rply import ParserGenerator
from rply import Token as RplyToken
from rply.lexergenerator import LexerGenerator


util_logger = logging.getLogger('language_fragments.lang.grounded_rule_lang')

RULE_LEXER_GEN = LexerGenerator()

RULE_LEXER_GEN.add("IF",'if')
RULE_LEXER_GEN.add('AND',r'and')
RULE_LEXER_GEN.add("THEN",'then')
RULE_LEXER_GEN.add('NOT',r'no')
RULE_LEXER_GEN.add('NOUN',r'[a-z]+')

RULE_LEXER_GEN.ignore(r'\s+')
RULE_LEXER_GEN.ignore(r';.*(?=\r|\n|$)')

## main lexer
RULE_LEXER = RULE_LEXER_GEN.build()

pg = ParserGenerator(
    [rule.name for rule in RULE_LEXER.rules],
    precedence=[],
    cache_id="GroundedRuleLanguage"
)


@pg.production("main : IF I' AND I' THEN I'")
def predicate_variable(p):
    antecedent = AndOp.initialize(p[1])(p[3])
    universal = Universal.initialize(antecedent)(p[5])
    return universal()

@pg.production("I' : NOT NOUN")
def negated_predicate(p):
    n = Predicate(p[1])
    return NegCopula()(n)

@pg.production("I' : NOUN")
def simple_noun(p):
    n = Predicate(p[0])
    return Copula()(n)

class GroundedRuleParser(LogicParser):
    lexer = RULE_LEXER
    _pg = pg

    reserve_words = {
    }

    @property
    def lowercase(self):
        return True

    @classmethod
    def from_config(cls,config):
        """Loads a `SpacyEnParser` from configuration

        :param config: the global configuration 
        """
        return cls()
