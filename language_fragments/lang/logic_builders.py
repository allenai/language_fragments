####
from language_fragments.lang.parser import LFTranslation
from language_fragments.base import UtilityClass,ConfigurableClass

__all__ = [
    "Value",
    "Predicate",
    "BinaryPredicate",
    "BinaryOperator",
    "NegatableBinary",
    "Universal",
    "Existential",
    "QuantifiedPredicate",
    "UniversalPredicate",
    "ExistentialPredicate",
    "No",
    "Proposition",
    "BooleanOperator",
    "AndOp",
    "OrOp",
    "Copula",
    "NegCopula",
    "GroundImplication",
]

class LFObj(UtilityClass):
    def __str__(self):
        return self.lf_format()

    def lf_format(self):
        raise NotImplementedError('LF not implemented..')

    @property
    def is_complex(self):
        return False

class Symbol(LFObj):
    @property
    def is_constant(self):
        return False

    @property
    def value(self):
        raise NotImplementedError

    def clausal_form(self,negate=False):
        raise NotImplementedError

class Value(Symbol):
    def __init__(self,const):
        self._const = const

    @property
    def is_constant(self):
        return True

    @property 
    def value(self):
        return self._const.value.lower()

    def lf_format(self):
        return self.value


class LFSystem(LFTranslation):
    def find_predicates(self):
        """Find all predicates in all emebedded/constituent expressions. Does a 
        search down to all sub-expressions. 

        :rtype: list 
        :returns: a list of strings 
        """
        symbol_list = [self]
        pred_list = []

        while symbol_list:
            s = symbol_list.pop(0)

            if isinstance(s,GrammarFunction):
                symbol_list.append(s._a)
                symbol_list.append(s._b)

            elif isinstance(s,Predicate):
                pred_list.append((s.value,s.arity))
        return pred_list

    def find_constants(self):
        """Find all constants in all emebedded/constituent expressions 

        :rtype: list 
        :returns: a list of strings 
        """
        symbol_list = [self]
        const_list = []

        while symbol_list:
            s = symbol_list.pop(0)
            
            if isinstance(s,GrammarFunction):
                symbol_list.append(s._a)
                symbol_list.append(s._b)

            elif isinstance(s,Proposition):
                symbol_list.append(s._a)

            elif isinstance(s,BinaryPredicate):
                symbol_list.append(s.arg1)
                symbol_list.append(s.arg2)

            elif isinstance(s,Predicate):
                symbol_list.append(s.arg1)

            elif isinstance(s,Value):
                const_list.append(s.value)
                
        return const_list

    def find_variables(self):
        """Find all of the variables involved

        :returns: a list of variables
        """
        symbol_list = [self]
        const_list = []

        while symbol_list:
            s = symbol_list.pop(0)
            
            if isinstance(s,GrammarFunction):
                symbol_list.append(s._a)
                symbol_list.append(s._b)

            elif isinstance(s,Proposition):
                symbol_list.append(s._a)

            elif isinstance(s,BinaryPredicate):
                symbol_list.append(s.arg1)
                symbol_list.append(s.arg2)

            elif isinstance(s,Predicate):
                symbol_list.append(s.arg1)

            elif not isinstance(s,Value) and isinstance(s,str):
                const_list.append(s)
                
        return const_list


class Predicate(Symbol,LFSystem):
    def __init__(self,pred,negated=False):
        self._pred = pred 
        self._negated = False
        self._arity = 1
        self.arg1 = 'x'

    @property
    def negated(self):
        """Determines if the predicate is negated 

        :rtype: bool
        """
        return self._negated

    @negated.setter
    def negated(self,x):
        self._negated = x

    @property 
    def value(self):
        return self._pred.value.capitalize()

    @property
    def arity(self):
        return self._arity

    @arity.setter
    def arity(self,value):
        self._arity = value

    def lf_format(self):
        return "%s(%s)" % (self.value,self.arg1) if not self._negated \
          else "Not(%s(%s))" % (self.value,self.arg1)

    def __call__(self,a='x'):
        self.arg1 = a
        return self

    @property
    def gen_skolems(self):
        return False
    
class BinaryPredicate(Predicate):
    def __init__(self,pred,negated=False):
        self._pred = pred 
        self._negated = False
        self._arity = 2
        self.arg1 = 'x'
        self.arg2 = 'y'

    def __call__(self,a='x',b='y'):
        self.arg1 = a
        self.arg2 = b
        return self

    def lf_format(self):
        return "%s(%s,%s)" % (self.value,self.arg1,self.arg2) if not self._negated \
          else "Not(%s(%s,%s))" % (self.value,self.arg1,self.arg2)

class GrammarFunction(LFObj,LFSystem):
    pattern = None 

    @classmethod
    def initialize(cls,a):
        raise NotImplementedError('Function not implemented')

    def __call__(self):
        return self

class BinaryOperator(GrammarFunction):
    
    def __init__(self,a,b,var='x'):
        self._a = a
        self._b = b
        self._var = var

    @property
    def var(self):
        return self._var

    @var.setter
    def var(self,value):
        self._var = value
        ## need to make this more general
        self._a.arg1 = value

    @classmethod
    def initialize(cls,a):
        return lambda b : cls(a,b)

    def lf_format(self):
        return self.pattern % (self.var,self._a,self._b)

    @property
    def is_complex(self):
        return True

class NegatableBinary(BinaryOperator):
    def negate(self):
        """Negated the Binary expression (e.g., a universal
        or existential in the scope of a negation) 
        
        :returns: a new instance in negated form
        """
        raise NotImplementedError

    @property
    def gen_skolems(self):
        return False

class Universal(NegatableBinary):
    pattern = "ForAll([%s],Implies(%s,%s))"

    def negate(self):
        """Negated the Binary expression (e.g., a universal
        or existential in the scope of a negation) 
        
        :returns: a new instance in negated form
        """
        self._b.negated = False if self._b.negated is True else True
        return Existential(self._a,self._b,self.var)

    @property
    def gen_skolems(self):
        return False

class Existential(NegatableBinary):
    pattern = "Exists([%s],And(%s,%s))"

    def negate(self):
        """Negated the Binary expression (e.g., a universal
        or existential in the scope of a negation) 
        
        :returns: a new instance in negated form
        """
        self._b.negated = False if self._b.negated is True else True
        return Universal(self._a,self._b,self.var)

    @property
    def gen_skolems(self):
        return True


class QuantifiedPredicate(NegatableBinary):

    def lf_format(self):
        return self.pattern % (self.var,self._a)

    @classmethod
    def initialize(cls,a):
        return cls(a,None)

    def negate(self):
        """Negated the Binary expression (e.g., a universal
        or existential in the scope of a negation) 
        
        :returns: a new instance in negated form
        """
        raise ValueError('Cannot be negated!')

class UniversalPredicate(QuantifiedPredicate):
    pattern = "ForAll([%s],%s)"

class ExistentialPredicate(QuantifiedPredicate):
    pattern = "Exists([%s],%s)"

        
class No(BinaryOperator):
    

    def __call__(self):
        ## with internal structure 
        if self._b.is_complex:
            self._b = self._b.negate()
            return Universal(self._a,self._b,self.var)

        ## simple 
        self._b.negated = False if self._b.negated is True else True
        return Universal(self._a,self._b,self.var)

    def negate(self):
        """Negated the Binary expression (e.g., a universal
        or existential in the scope of a negation) 
        
        :returns: a new instance in negated form
        """
        raise ValueError('Not negatable!')

    def __str__(self):
        raise ValueError('Not to be used directly')

    
####################
# UNARY OPERATORS  #
####################

class UnaryOperator(GrammarFunction):
    pattern = "%s"

    def __init__(self,a):
        self._a = a
        self._b = None

    @classmethod
    def initialize(cls,a):
        return cls(a)

    def lf_format(self):
        return self.pattern % self._a


class Proposition(UnaryOperator):
    @property
    def gen_skolems(self):
        return False

class BooleanOperator(GrammarFunction):
    pattern = "%s(%s,%s)"
    name = None

    def __init__(self,a,b):
        self._a = a
        self._b = b

    @classmethod
    def initialize(cls,a):
        return lambda b : cls(a,b)

    def lf_format(self):
        return self.pattern % (self.name,self._a,self._b)

class AndOp(BooleanOperator):
    pattern = "%s(%s,%s)"
    name = "And"

class GroundImplication(BooleanOperator):
    pattern = "%s(%s,%s)"
    name = "Implies"

    def __call__(self):
        return self

    @property
    def gen_skolems(self):
        return False

class OrOp(AndOp):
    name = "Or"

## copulas

class Copula(GrammarFunction):

    def __call__(self,a):
        ## return argument (semantically vacuous) 
        return a
    
class NegCopula(Copula):

    def __call__(self,a):
        ## negates argument
        a.negated = False if a.negated is True else True
        return a
