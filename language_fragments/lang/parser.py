import re
from itertools import chain
from optparse import OptionParser,OptionGroup
from language_fragments.base import ConfigurableClass,UtilityClass
from language_fragments.util.cache import LRUCache


class ParserError(Exception):
    pass

class ParserBase(ConfigurableClass):
    """Base class for new parser 

    :param _pg: the target parser generator to use 
    :param _lexer: the target lexer to use 
    """
    _pg = None
    lexer = None

    def __init__(self,tagger=None,cache_size=3000,extra_reserve={},disable_parser=False):
        """Creates a tagger instance 

        :param tagger: the main tagger model to use (optional)
        :type tagger: obj
        """
        self.tagger = tagger
        self.parser = self._pg.build()
        self._cache = LRUCache(cache_size)
        self.keywords = extra_reserve
        self.keywords.update(self.reserve_words)
        self.disable_parser = disable_parser

        self.logger.info('Loaded parser, with grammar=%s, cache_size=%d, extra_reserve=%d' %\
                             (self._pg.cache_id,cache_size,len(extra_reserve)))

    def _pre_process(self,expr):
        """Preprocess a text before parsing (passes 
        by default) 

        :param expr: the input expression 
        :type expr: str 
        :returns: parsed output 
        """
        return expr

class StatementList(UtilityClass):
    """Holds a list of statements, and can construct representations for them

    """
    def __init__(self,statement_list):
        """Creates a `StatementList` instance 

        :param statement_list: the list of parsed expressions
        """
        self.statements = statement_list

    def __iter__(self):
        for item in self.statements:
            yield item

    def __getitem__(self,k):
        ## selecting items in list
        return self.statements[k]

    @property 
    def predicates(self):
        """Returns a list of the unique predicates used in all the statements 

        :rtype: list
        """
        return list(set(chain(
            *[i.find_predicates() for i in self.statements])))

    @property 
    def constants(self):
        """Returns a list of the unique constants used in all the statements 

        :rtype: list
        """
        skolems = ["s_%d" % n for n,i in enumerate(self.statements) if i.gen_skolems]
        return list(set(chain(
            *[i.find_constants() for i in self.statements]))) + skolems

    @property 
    def variables(self):
        """Returns a list of the unique constants used in all the statements 

        :rtype: list
        """
        return list(set(chain(
            *[i.find_variables() for i in self.statements])))

    

class LFTranslation(UtilityClass):

    def find_constants(self):
        """Find all constants in all emebedded/constituent expressions 

        :rtype: list 
        :returns: a list of strings 
        """
        raise NotImplementedError

    def find_variables(self):
        """Find all constants in all emebedded/constituent expressions 

        :rtype: list 
        :returns: a list of strings 
        """
        raise NotImplementedError

    def find_predicates(self):
        """Find all predicates in all emebedded/constituent expressions. Does a 
        search down to all sub-expressions. 

        :rtype: list 
        :returns: a list of strings 
        """
        raise NotImplementedError

    @property
    def predicates(self):
        raise NotImplementedError
    


class LogicParser(ParserBase):
    def __call__(self,slist):
        return self.parse_statements(slist)

    def parse(self,expr):
        """Main method for parsing the expressions 
        
        :param expr: the target expression to parse 
        :rtype `LFTranslation`
        """
        backup = self._cache[expr]
        if backup is not None:
            return backup
        
        pexpr = self._before_tagging(expr)
        pexpr = self._pre_process(pexpr)

        try:
            lexer_gen = self.lexer.lex(pexpr)
        except Exception as e:
            raise ParserError('Error lexing: %s' % pexpr)
        try:
            parser_out = self.parser.parse(lexer_gen)
        except Exception as e:
            raise ParserError('Error parsing: %s\n%s' % (pexpr,e))

        self._cache[expr] = parser_out
        return parser_out

    def parse_statements(self,slist):
        """Parse statements into internal form 
        
        :param slist: a list of statements to parse 
        :returns: a list of `LFTranslation` statements
        """
        return StatementList([self.parse(a) for a in slist])

    def _before_tagging(self,expr):
        if self.lowercase:
            return expr.lower()
        return expr


class TaggerParser(LogicParser):
    """Parse that has some tagger model built-in"""

    @property
    def lowercase(self):
        return False

    def _pre_process(self,expr):
        """Preprocess a text before parsing (passes 
        by default) 

        :param expr: the input expression 
        :type expr: str 
        :returns: parsed output 
        """
        raise NotImplementedError('Did not implement the tagger pre-processor!')


_META_LEMMAS = {
    "is"     : "be",
    "does"   : "do",
}

_META_POS = {
    "a"     : "DET",
    "an"    : "DET",
}

    
class PseudoTag:
    def __init__(self,word):
        word = word.strip()
        self.lemma_ = _META_LEMMAS.get(word,word)
        self.text = word
        self.pos_ = _META_POS.get(word,"unknown")
    

class SpacyEnParser(TaggerParser):
    """Parser that uses a SpacyEn grammar and parser/tagger"""
    reserve_words = {
    }

    def _before_tagging(self,expr):
        ## remove punctuation 
        expr = re.sub(r'\.+|\;+|\?+','',expr)

        ## multi-word match
        return expr

    def _pre_process(self,expr):
        """Uses the basic spacy parser to do pos tagging and lemmatization;
        returns strings in the format 

        `lemma^_POS_NAME`

        :param exp: the expression to process 
        :returns: a string with pos markup 
        :rtype: str 
        :raises: ValueError
        """
        if not self.disable_parser:
            tagged = self.tagger(
                self._before_tagging(expr),
                disable=["parser","ner"]
            )
        else:
            tagged = [PseudoTag(w) for w in self._before_tagging(expr).split()]
            
        ## change into a loop
        new_str = []
        for item in tagged:
            lemma = item.lemma_
            text = item.text
            if self.lowercase:
                lemma = lemma.lower()
                text = text.lower()
            pos = item.pos_

            ## overrides the parser with reserve word declarations
            if lemma in self.keywords:
                new_str.append("%s^%s" % (lemma,self.keywords[lemma]))
            elif text in self.keywords:
                new_str.append("%s^%s" % (text.lower(),self.keywords[text]))
            else:
                if self.disable_parser and pos == "unknown":
                    raise ValueError(
                        "Token not known in parser offline mode! %s;  %s" % (item.text,expr)
                    )
                new_str.append("%s^%s" % (lemma,pos))
        
        return ' '.join(new_str)

    @classmethod
    def from_config(cls,config):
        """Loads a `SpacyEnParser` from configuration

        :param config: the global configuration 
        """
        extra_reserve = {} if not config.extra_reserve else config.extra_reserve
        
        import spacy
        return cls(tagger=spacy.load(config.grammar_type),
                       cache_size=config.parser_cache,
                       extra_reserve=extra_reserve,
                       disable_parser=config.disable_parser)


def params(config):
    """Main parameters for building a parser

    :param config: the global configuration object
    """
    group = OptionGroup(config,"reasoning_transformers.RuleGrammar",
                            "Setting for the rule grammar")

    group.add_option("--grammar_type",
                          dest="grammar_type",
                          default='en',
                          help="The type of depndency/SpACY grammar to use [default='en']")

    group.add_option("--parser_cache",
                          dest="parser_cache",
                          default=3000,
                          type=int,
                          help="The size of cache to use [default=3000]")

    group.add_option("--extra_reserve",
                          dest="extra_reserve",
                         default='',type=str,help="Extra reserce words to add [default='']")

    group.add_option("--disable_parser",dest="disable_parser",
                         action='store_true',default=False,
                      help="Turns off the parser (assumes all targets are in lexicon) [default=False]")

    config.add_option_group(group)

