import logging
import re
from language_fragments.lang.rule_lexer import RuleLexerGenerator
from language_fragments.lang.parser import SpacyEnParser,LFTranslation
from language_fragments.base import UtilityClass,ConfigurableClass
from language_fragments.lang.logic_builders import *
from rply import ParserGenerator
from rply import Token as RplyToken

### building materials
util_logger = logging.getLogger('language_fragments.lang.rule_lang')

BINARY_QUANTS = {
    "UNIVERSAL"           : Universal,
    "EXISTS"              : Existential,
    "NO"                  : No,
    "SOMETHING_UNIVERSAL" : Universal,
    "SOMETHING_EXIST"     : Existential,
}

### rule lexer
RULE_LEXER_GEN = RuleLexerGenerator()
RULE_LEXER_GEN.add("SOMETHING_UNIVERSAL",r'everything\^NOUN|everyone\^NOUN|every\^DET person\^NOUN|every\^DET thing\^NOUN|every\^DET element\^NOUN|every\^DET item\^NOUN')
RULE_LEXER_GEN.add("SOMETHING_EXIST",r'some\^DET person\^NOUN|something\^NOUN|someone\^NOUN')
RULE_LEXER_GEN.add('PROPN',r'[a-zA-Z0-9\_]+\^PROPN')
#RULE_LEXER_GEN.add('AND',r'u\^CONJ')
RULE_LEXER_GEN.add('NOUN',r'[a-zA-Z0-9\_]+\^NOUN')
RULE_LEXER_GEN.add('ADV',r'[a-zA-Z0-9]+\^ADV')
RULE_LEXER_GEN.add('DOES_NOT',r'do\^VERB not\^ADV')
RULE_LEXER_GEN.add('NOT',r'be\^VERB not\^ADV a[n]?\^DET|be\^VERB not\^ADV')
RULE_LEXER_GEN.add('IS_A',r'be\^VERB an\^DET|be\^VERB a\^DET|be\^VERB')
RULE_LEXER_GEN.add('UNIVERSAL',r'every\^DET|all\^DET')
RULE_LEXER_GEN.add('ADJ',r'[a-zA-Z]+\^ADJ')
RULE_LEXER_GEN.add("DEF_DESCR",r'the\^DET')
RULE_LEXER_GEN.add('EXISTS',r'some\^DET|any\^DET|an\^DET|a\^DET')
RULE_LEXER_GEN.add('NO',r'no\^DET')
RULE_LEXER_GEN.add('RCLAUSE',r'which\^DET|who\^DET|that\^DET|who\^PRON')
RULE_LEXER_GEN.add('VERB',r'[a-zA-Z0-9]+\^VERB')

### ignore rules
RULE_LEXER_GEN.ignore(r'\s+')
RULE_LEXER_GEN.ignore(r';.*(?=\r|\n|$)')

## main lexer
RULE_LEXER = RULE_LEXER_GEN.build()

### rule grammar generator/main grammar rules
pg = ParserGenerator(
    [rule.name for rule in RULE_LEXER.rules],
    precedence=[],
    cache_id="RuleGrammar"
)

### rules
@pg.production("main : quantifier")
@pg.production("main : proposition")
def predicate_variable(p):
    return p[0]()

#################
# PROPOSITIONS  #
#################

@pg.production("proposition : PROPN I'")
@pg.production("proposition : NOUN I'")
@pg.production("proposition : def I'")
@pg.production("proposition : def TV")
@pg.production("proposition : PROPN TV")
@pg.production("proposition : NOUN TV")
def predicate_variable(p):
    v = Value(p[0]) if isinstance(p[0],RplyToken) else p[0]
    if isinstance(p[1],BinaryPredicate):
        p[1].arg1 = v
        return Proposition.initialize(p[1])
    elif isinstance(p[1],(Universal,Existential)):
        p[1]._b.arg1 = v
        return Proposition.initialize(p[1])
    return Proposition.initialize(p[1](v))

@pg.production("proposition : ADV I'")
@pg.production("proposition : ADV TV")
def predicate_adv_mispase(p):
    ### mis-parse for adverbs
    v = Value(p[0])
    if isinstance(p[1],BinaryPredicate):
        p[1].arg1 = v
        return Proposition.initialize(p[1])
    return Proposition.initialize(p[1](v))

#############################
# QUANTIFIER CONSTRUCTIONS  #
#############################

@pg.production("quantifier : SOMETHING_UNIVERSAL TV")
@pg.production("quantifier : SOMETHING_UNIVERSAL I'")
def universal_predicate(p):
    return UniversalPredicate.initialize(p[1])

@pg.production("quantifier : SOMETHING_EXIST TV")
@pg.production("quantifier : SOMETHING_EXIST I'")
def exist_predicate(p):
    return ExistentialPredicate.initialize(p[1])

@pg.production("quantifier : left_bin_quant I'")
@pg.production("quantifier : left_bin_quant TV")
@pg.production("quantifier : left_bin_quant NOUN")
def predicate_basic_copula(p):
    v = Predicate(p[1]) if isinstance(p[1],RplyToken) else p[1]
    return p[0](v)

@pg.production("TV : DOES_NOT TV")
def tv_modified(p):
    tv = p[1]
    if isinstance(tv,BinaryPredicate):
        tv.negated = True
        return tv
    return tv.negate()

@pg.production("TV : VERB left_bin_quant")
def tv(p):
    embed_quant = p[1](BinaryPredicate(p[0]))()
    embed_quant.var = 'y'
    return embed_quant

@pg.production("left_bin_quant : binary_quant rclause")
@pg.production("left_bin_quant : binary_quant I'")
@pg.production("left_bin_quant : binary_quant ADJ")
@pg.production("left_bin_quant : binary_quant NOUN")
@pg.production("left_bin_quant : binary_quant PROPN")
def predicate_variable(p):
    v = Predicate(p[1]) if isinstance(p[1],RplyToken) else p[1]
    return p[0].initialize(v)

@pg.production("left_bin_quant : SOMETHING_UNIVERSAL left_rclause")
@pg.production("left_bin_quant : something left_rclause")
def non_relative_clause(p):
    return Universal.initialize(p[1])

@pg.production("left_bin_quant : SOMETHING_EXIST left_rclause")
@pg.production("left_bin_quant : something_e left_rclause")
def non_relative_clause(p):
    return Existential.initialize(p[1])

@pg.production("binary_quant : UNIVERSAL")
@pg.production("binary_quant : NO")
@pg.production("binary_quant : EXISTS")
#@pg.production("binary_quant : SOMETHING_EXIST")
#@pg.production("binary_quant : SOMETHING_UNIVERSAL")
def quantifiers(p):
    ttype = p[0].gettokentype() if len(p) == 1 else p[1].gettokentype()
    return BINARY_QUANTS[ttype]

###########################
# ## copula constructions #
###########################

@pg.production("rclause : NOUN left_rclause")
@pg.production("rclause : PROPN left_rclause")
def full_relative_clause(p):
    return AndOp.initialize(p[1])(Predicate(p[0]))

@pg.production("left_rclause : RCLAUSE I'")
@pg.production("left_rclause : RCLAUSE TV")
def left_relative_clause(p):
    return p[1]

@pg.production("I' : IS_A NOUN")
@pg.production("I' : IS_A PROPN")
@pg.production("I' : IS_A ADJ")
def copula_predicate_count_noun(p):
    n = Predicate(p[1])
    return Copula()(n)

@pg.production("I' : NOT NOUN")
@pg.production("I' : NOT PROPN")
@pg.production("I' : NOT ADJ")
def negated_predicate(p):
    n = Predicate(p[1])
    return NegCopula()(n)

########################
# ## PRIMITIVE SYMBOLS #
########################

@pg.production("something : UNIVERSAL SOMETHING_UNIVERSAL")
def universal_macro(p):
    return p[1]

@pg.production("something_e : EXISTS SOMETHING_EXIST")
def universal_macro(p):
    return p[1]

@pg.production("TV : VERB def")
@pg.production("TV : VERB PROPN")
@pg.production("TV : VERB NOUN")
@pg.production("TV : VERB ADJ") ## issue
def symbol_seq(p):
    pred = BinaryPredicate(p[0])
    pred.arg2 = Value(p[1]) if isinstance(p[1],RplyToken) else p[1]
    pred.arity = 2
    return pred

@pg.production("def : DEF_DESCR NOUN")
@pg.production("def : DEF_DESCR PROPN")
def def_descr1(p):
    v = Value(p[1])
    return v

### ERRORS
####

@pg.error
def error_handler(token):
    raise ValueError("Ran into a %s where it wasn't expected, token=%s" %\
                         (token.gettokentype(),token.value))

## specification of the rule lexer and grammar
_DEFAULT_RESERVE = {
        "rs"         : "VERB",
        "every"      : "DET",
        "some"       : "DET",
        "all"        : "DET",
        "any"        : "DET",
        "something"  : "NOUN",
        "someone"    : "NOUN",
        "if"         : "ADP",
        "which"      : "DET",
        "who"        : "DET",
        "that"       : "DET",
        "verb"       : "VERB",
        "verb1"      : "VERB",
        "verb2"      : "VERB",
        "no"         : "DET",
        "not"        : "ADV",
        "constant"   : "NOUN",
        "constant1"  : "NOUN",
        "constant2"  : "NOUN",
        "Aa" : "NOUN",
        "Bb" : "NOUN",
        "Cc" : "NOUN",
        "Dd" : "NOUN",
        "the": "DET",
        "and": "CCONJ",
        'be' : 'VERB',
        "everything" : "NOUN",
        "everyone"   : "NOUN",
        "element"    : "NOUN",
        "item"       : "NOUN",
        
}

class RuleParser(SpacyEnParser):
    """The main parser for all of the `language fragments`
    convered in this tool so far. 

    :param _lexer: the target lexer 
    :param _pg: the target parser generator with 
       a set of production rules. 

    A specification of the rules covered in this parser:
    """
    lexer = RULE_LEXER
    _pg = pg

    reserve_words = _DEFAULT_RESERVE
        
    @property
    def lowercase(self):
        ## lowercase after running through tagger
        return True

    def _before_tagging(self,expr):
        ## remove punctuation
        text_input = re.sub(r'\.+|\;+|\?+','',expr)
        text_input = re.sub(r'\,',' , ',text_input)
        text_input = re.sub(r'\s+',' ',text_input)
        return text_input

