import re
from language_fragments.base import ConfigurableClass,UtilityClass
from rply import ParserGenerator
from rply import Token as RplyToken
from rply.lexergenerator import LexerGenerator
from rply.lexer import Lexer,LexerStream
from rply.token import Token,SourcePosition
from rply.errors import LexingError

class RuleToken(Token):
    def __init__(self, name, value, source_pos=None):
        self.name = name
        self.value = value
        self.source_pos = source_pos

class RuleStream(LexerStream):
    """Custom `LexerStream` specific to rule grammars and lexer 
    """
    def __init__(self, lexer, s):
        self.lexer = lexer
        self.s = s
        self.idx = 0
        self._lineno = 1
        self._colno = 1

    def next(self):
        while True:
            if self.idx >= len(self.s):
                raise StopIteration
            for rule in self.lexer.ignore_rules:
                match = rule.matches(self.s, self.idx)
                if match:
                    self._update_pos(match)
                    break
            else:
                break
        for rule in self.lexer.rules:
            match = rule.matches(self.s, self.idx)
            if match:
                lineno = self._lineno
                self._colno = self._update_pos(match)
                source_pos = SourcePosition(match.start, lineno, self._colno)
                full_match = self.s[match.start:match.end]
                aname = full_match

                if rule.name == "NOUN" or rule.name == "VERB" or rule.name == "ADJ" \
                  or rule.name == "PROPN" or rule.name == "ADV":
                    aname = ' '.join(full_match.split("^")[:-1])

                token = RuleToken(
                    rule.name, aname, source_pos
                )
                return token
        else:
            raise LexingError(None, SourcePosition(
                self.idx, self._lineno, self._colno))

class RuleLexer(Lexer):

    def __init__(self, rules, ignore_rules):
        self.rules = rules
        self.ignore_rules = ignore_rules

    def lex(self, s):
        """The main lexer function 
        
        :param s: the lexer input expression
        """
        return RuleStream(self, s)

class RuleLexerGenerator(LexerGenerator,ConfigurableClass):
    """A custom `LexerGenerator` specialized to rule languages 
    """

    def build(self):
        """
        Returns a lexer instance, which provides a `lex` method that must be
        called with a string and returns an iterator yielding
        :class:`~rply.Token` instances.
        """
        return RuleLexer(self.rules, self.ignore_rules)
