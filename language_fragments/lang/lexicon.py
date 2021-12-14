###################################
# GENERIC OPERATORS/DUMMY SYMBOLS #
###################################

_OPERATORS = {
        "every"       : "DET",
        "some"        : "DET",
        "all"         : "DET",
        "any"         : "DET",
        "something"   : "NOUN",
        "someone"     : "NOUN",
        "if"          : "ADP",
        "which"       : "DET",
        "who"         : "DET",
        "that"        : "DET",
        "the"         : "DET",
        "and"         : "CCONJ",
        "Not"         : "ADV",
        "no"          : "DET",        
}

_DUMMY_PREDS = dict(
    [("verb%d" % d,"VERB") for d in range(20)]+[("verb","VERB")]+[("rs","VERB")]+\
    [("%s%s" % (a.upper(),a),"NOUN") for a in 'abcdefghijklmnopqrstuvwxyz']
)

_DUMMY_CONSTANTS = dict(
    [("constant%d" % d,"NOUN") for d in range(20)]+[("constant","NOUN")]
)

########################
# RULE_TAKER KEYWORDS  #
########################

RULE_TAKER_KEYWORDS = {
        ### original rule nouns/verbs/adjectives...
        "kind"        : "ADJ",
        "bald_eagle"  : "NOUN",
        "a"           : "DET",
        "chase"       : "VERB",
        "see"         : "VERB",
        "eat"         : "VERB",
        "visit"       : "VERB",
        "lion"        : "NOUN",
        "squirrel"    : "NOUN",
        "blue"        : "ADJ",
        "young"       : "ADJ",
        "red"         : "ADJ",
        "cold"        : "ADJ",
        "bob"         : "PROPN",
        "like"        : "VERB",
        "mouse"       : "NOUN",
        "tiger"       : "NOUN",
        "harry"       : "PROPN",
        "cow"         : "NOUN",
        "rough"       : "ADJ",
        "white"       : "ADJ",
        "blue"        : "ADJ",
        "gary"        : "PROPN",
        "rough"       : "ADJ",
        "quiet"       : "ADJ",
        "anne"        : "PROPN",
        "erin"        : "PROPN",
        "furry"       : "ADJ",
        "smart"       : "ADJ",
        "big"         : "ADJ",
        "nice"        : "ADJ",
        "cat"         : "NOUN",
        "dave"        : "PROPN",
        "green"       : "ADJ",
        "young"       : "ADJ",
        "dog"         : "NOUN",
        "fiona"       : "PROPN",
        "charlie"     : "PROPN",
        "bear"        : "NOUN",
        "need"        : "VERB",
        "round"       : "ADJ",
        "rabbit"      : "NOUN",
}

RULE_TAKER_KEYWORDS.update(_OPERATORS)
RULE_TAKER_KEYWORDS.update(_DUMMY_PREDS)

# multi-word
