import re
import logging
from language_fragments.lang.rule_lexer import RuleLexerGenerator
from language_fragments.lang.parser import SpacyEnParser,LFTranslation
from language_fragments.lang.logic_builders import *
from language_fragments.lang.lexicon import RULE_TAKER_KEYWORDS
from language_fragments.base import UtilityClass,ConfigurableClass
from rply import ParserGenerator
from rply import Token as RplyToken

util_logger = logging.getLogger('language_fragments.lang.ruletaker_lang')

### rule lexer
RULE_LEXER_GEN = RuleLexerGenerator()
RULE_LEXER_GEN.add("INDEF",'a\^DET')
RULE_LEXER_GEN.add("SOMETHING_UNIVERSAL",'someone\^NOUN|something\^NOUN')
RULE_LEXER_GEN.add("UNIVERSAL_MARKERS",'thing\^NOUN|people\^NOUN')
RULE_LEXER_GEN.add("IF",'if\^ADP')
RULE_LEXER_GEN.add("THEN",'then\^ADV')
RULE_LEXER_GEN.add("PUNCT",',\^PUNCT')
RULE_LEXER_GEN.add('PROPN',r'[a-zA-Z0-9\_]+\^PROPN')
RULE_LEXER_GEN.add('NOUN',r'[a-zA-Z0-9\_]+\^NOUN')
RULE_LEXER_GEN.add('DOES_NOT',r'do\^VERB not\^ADV')
RULE_LEXER_GEN.add('NOT',r'be\^VERB not\^ADV a[n]?\^DET|be\^VERB not\^ADV|not\^ADV')
RULE_LEXER_GEN.add('IS_A',r'be\^VERB an\^DET|be\^VERB a\^DET|be\^VERB')
RULE_LEXER_GEN.add('UNIVERSAL',r'all\^DET')
RULE_LEXER_GEN.add('ADJ',r'[a-zA-Z]+\^ADJ')
RULE_LEXER_GEN.add("DEF_DESCR",r'the\^DET')
RULE_LEXER_GEN.add('PRON',r'they\^PRON|\-pron\-\^PRON')
RULE_LEXER_GEN.add('VERB',r'[a-zA-Z0-9]+\^VERB')
RULE_LEXER_GEN.add('AND',r'and\^CCONJ')

### ignore rules
RULE_LEXER_GEN.ignore(r'\s+')
RULE_LEXER_GEN.ignore(r';.*(?=\r|\n|$)')

## main lexer
RULE_LEXER = RULE_LEXER_GEN.build()

BINARY_QUANTS = {
    "UNIVERSAL"           : Universal,
    "SOMETHING_UNIVERSAL" : Universal,
}

### rule grammar generator/main grammar rules
pg = ParserGenerator(
    [rule.name for rule in RULE_LEXER.rules],
    precedence=[],
    cache_id="RuleTakerGrammar"
)

### TOP_LEVEL 

@pg.production("main : quantifier")
@pg.production("main : proposition")
#@pg.production("main : rantecedent")
def predicate_variable(p):
    return p[0]()

### QUANTIFIERS 
@pg.production("quantifier : IF antecedent THEN conclusion")
@pg.production("quantifier : IF antecedent THEN proposition")
def conditional(p):
    return p[1](p[3])

@pg.production("quantifier : IF proposition THEN proposition")
@pg.production("quantifier : IF conjunction THEN proposition")
def conditional_props(p):
    return GroundImplication.initialize(p[1])(p[3])

@pg.production("quantifier : antecedent I'")
def predicate_basic_copula(p):
    v = Predicate(p[1]) if isinstance(p[1],RplyToken) else p[1]
    return p[0](v)

@pg.production("quantifier : implicit_antecedent I'")
@pg.production("quantifier : rclause I'")
def zero_quantifier(p):
    v = Predicate(p[1]) if isinstance(p[1],RplyToken) else p[1]
    return Universal.initialize(p[0])(p[1])

## PROPOSITIONS

## weird one 
@pg.production("antecedent : PROPN I' quant_conj")
@pg.production("antecedent : def I' quant_conj")
@pg.production("antecedent : def TV quant_conj")
@pg.production("antecedent : PROPN TV quant_conj")
def reverse_antecedent(p):
    v = Value(p[0]) if isinstance(p[0],RplyToken) else p[0]
    prop = None
    if isinstance(p[1],BinaryPredicate):
        p[1].arg1 = v
        prop = Proposition.initialize(p[1])
    elif isinstance(p[1],(Universal,Existential)):
        p[1]._b.arg1 = v
        prop = Proposition.initialize(p[1])
    else:
        prop = Proposition.initialize(p[1](v))
    quantified = p[-1](prop)
    conj_op = AndOp.initialize(quantified._a)(quantified._b)
    return Universal.initialize(conj_op)

@pg.production("proposition : def I'")
@pg.production("proposition : PROPN I'")
@pg.production("proposition : def conjunction")
@pg.production("proposition : PROPN conjunction") 
@pg.production("proposition : def TV")
@pg.production("proposition : PROPN TV")
def proposition_variable(p):
    v = Value(p[0]) if isinstance(p[0],RplyToken) else p[0]
    if isinstance(p[1],BinaryPredicate):
        p[1].arg1 = v
        return Proposition.initialize(p[1])
    elif isinstance(p[1],(Universal,Existential)):
        p[1]._b.arg1 = v
        return Proposition.initialize(p[1])
    elif isinstance(p[1],AndOp):
        ## might need to check that sub-predicates are unary
        p[1]._a.arg1 = v
        p[1]._b.arg1 = v
        return p[1]
    return Proposition.initialize(p[1](v))

@pg.production("quant_conj : AND antecedent")
def special_conj(p):
    return p[1]

@pg.production("antecedent : binary_quant conjunction") 
@pg.production("antecedent : binary_quant I'")
@pg.production("antecedent : binary_quant implicit_antecedent")
@pg.production("antecedent : binary_quant NOUN")
@pg.production("antecedent : binary_quant PROPN")
@pg.production("antecedent : binary_quant rclause")
@pg.production("antecedent : binary_quant TV")
def antecedent_variable(p):
    v = Predicate(p[1]) if isinstance(p[1],RplyToken) else p[1]
    return p[0].initialize(v)

@pg.production("rclause : NOUN left_rclause")
@pg.production("rclause : PROPN left_rclause")
@pg.production("rclause : ADJ left_rclause")
def full_relative_clause(p):
    return AndOp.initialize(p[1])(Predicate(p[0]))

@pg.production("left_rclause : PUNCT implicit_antecedent")
def left_relative_clause(p):
    return p[1]

@pg.production("conjunction : I' conj")
@pg.production("conjunction : TV conj")
def explicit_conj(p):
    return AndOp.initialize(p[0])(p[1])

@pg.production("conj : AND indef")
@pg.production("conj : AND ADJ")
@pg.production("conj : AND TV")
@pg.production("conj : AND I'")
@pg.production("conj : AND conclusion")
@pg.production("conj : AND proposition")
def conjunction_1(p):
    n = Predicate(p[-1]) if isinstance(p[-1],(RplyToken,Value)) else p[-1]
    ## conjoined predicates 
    if isinstance(n,(Predicate,Proposition)):
        return n
    ### copula constructions 
    elif n.name == "NOT":
        return NegCopula()(n)
    return Copula()(n)

@pg.production("conclusion : PRON I'")
@pg.production("conclusion : PRON TV")
def copula_conclusion(p):
    return p[1]

@pg.production("implicit_antecedent : ADJ UNIVERSAL_MARKERS")
def copula_predicate_count_noun(p):
    n = Predicate(p[0])
    return Copula()(n)

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

@pg.production("binary_quant : SOMETHING_UNIVERSAL")
@pg.production("binary_quant : UNIVERSAL")
def quantifiers(p):
    ttype = p[0].gettokentype() if len(p) == 1 else p[1].gettokentype()
    return BINARY_QUANTS[ttype]

@pg.production("TV : DOES_NOT TV")
def tv_modified(p):
    tv = p[1]
    if isinstance(tv,BinaryPredicate):
        tv.negated = True
        return tv
    return tv.negate()

## transitive verbs 
@pg.production("TV : VERB def")
@pg.production("TV : VERB PROPN")
@pg.production("TV : VERB NOUN")
@pg.production("TV : VERB ADJ") ## issue
def symbol_seq(p):
    pred = BinaryPredicate(p[0])
    pred.arg2 = Value(p[1]) if isinstance(p[1],RplyToken) else p[1]
    pred.arity = 2
    return pred

## count noun
@pg.production("indef : INDEF NOUN")
def indefinite_descr(p):
    v = Value(p[1])
    return v

@pg.production("def : DEF_DESCR NOUN")
def def_descr1(p):
    v = Value(p[1])
    return v

@pg.error
def error_handler(token):
    raise ValueError("Ran into a %s where it wasn't expected, token=%s" %\
                         (token.gettokentype(),token.value))

class RuleTakerParser(SpacyEnParser):
    """Implementation of the `RuleTaker` language 

    The grammar is as follow: 

    main             := quantifier
                     := proposition
    quantifier       := IF antecedent THEN conclusion
                     := IF proposition THEN proposiion
                     := implicit_antecedent I'
                     := rclause I'
    proposition      := def I'
                     := def TV
                     := def conjunction
    antecedent       := binary_quant I'
                     := binary_quant implicit_antecedent
                     := binary_quant NOUN
                     := binary_quant PROPN
                     := binary_quant rclause
                     := binary_quant TV
                     := binary_quant conjunction
    rclause          := NOUN left_rclause
                     := PROPN left_rclause
                     := ADJ left_rclause
    left_rclause     := PUNCT implicit_antecedent
    implicit_antec.  := ADJ UNIVERSAL_MARKERS
    conjunction      := I' conj
                     := TV conj
    conj             := AND ADJ
                     := AND TV
                     := AND I'
                     := AND conclusion
                     := AND proposition
    conclusion       := PRON I' 
    I'               := IS_A NOUN 
                     := IS_A PROPN
                     := ISA_A ADJ
                     := NOT NOUN 
                     := NOT PROPN
                     := NOT ADJ
    binary_quant     := SOMETHING_UNIVERSAL 
                     := UNIVERSAL
    TV               := VERB def 
                     := VERB PROPN
                     := VERB NOUN
                     := VERB ADJ
    DEF              := DEF_DESCR NOUN 
                     := DEF_DESCR PROPN
    """
    lexer = RULE_LEXER
    _pg = pg

    reserve_words = RULE_TAKER_KEYWORDS

    @property
    def lowercase(self):
        return True
