import parser
import reporting
import tokens

class MixedType:
    ''' A type that can't be decided statically, or the return type of
    an unknown function. The super type of all other types. '''
    def __str__(self):
        return '<mixed>'

    def __repr__(self):
        # Come back to me when str of a dict calls str of its elements!
        return str(self)

    def __or__(self,other):
        ''' (t1 | t2) returns the most specific type that includes
        self and other. '''
        if self == other:
            return self
        else:
            # If self doesn't know how to unify with other, let's ask other
            return other.__ror__(self)

    def __ror__(self,other):
        # We've already tried and failed to ask other, so neither self
        # nor other knows how to proceed
#        print('{0} and {1} can\'t be unified.'.format(self,other))
        # Note, making a new MixedType rather than returning self,
        # so that this can be used as default behaviour in subclasses
        # as well.
        return MixedType()

    def __and__(self,other):
        ''' (t1 & t2) returns the widest type that is included in self
        and other '''
        # Inheritance goes the wrong way for this operator, so the
        # full implementation is here.
        # Note: This should be made into a congruence, for instance
        # array(x) & array(y) should return array(x & y), it currently
        # returns Empty.
        if type(self) == MixedType:
            return other
        elif self == other:
            return self
        elif self.dropattrs() == other:
            return self
        elif other.dropattrs() == self:
            return other
        elif self.dropattrs() == other.dropattrs():
            return TrustedType(self.dropattrs())
        else:
            return EmptyType()

    # def __rand__(self,other):
    #     return other

    def __ne__(self,other):
        return not (self == other)

    # def reduce(self):
    #     ''' If the type contains type variables, attempt to replace
    #     them with their correct values. The reduced type is returned
    #     and this method must be used as t = t.reduce() '''
    #     return self
    def dropattrs(self):
        ''' Return a copy of this type without semantic attributes
        like escaped or trusted '''
        return self
    def dereference(self):
        ''' In Parameter Types that have a known value, return said
        known value. In all other cases, return self '''
        return self
    def arrayelttype(self,warn):
        ''' if self denotes an array type, return its element
        type. '''
        mp = {}
        x = ParamType('_')
        if ArrType(x).match(self,mp,warn.at('operator []')):
            if x not in mp:
                return x
            else:
                return mp[x]
        else:
            return ErrorType()
    def cast(self,ptype):
        ''' Simulate a PHP (ptype)expression cast operation '''
        return PrimType(ptype)
    def match(self,other,typemap,warn):
        ''' Return True if other is included in (is a subtype of)
        self.

        typemap: a dictionary of ParamType instances to types.

        msg: If set, a warning message is printed in case of
        mismatch. msg should contain a human readable description of
        what this is a type of (eg "second parameter of foo")

        In case self contains parameter types, returns True if there
        exists a mapping of those parameter types to actual types such
        that inclusion holds, and if so populate the typemap
        dictionary with said mapping.

        In case other contains parameter types, they are initialised
        or specialised to whatever type is required for matching to
        hold.

        In case typemap isn't empty, it will only be WEAKENED
        (i.e. additional entries can be added, and types can be
        replaced by SUPERtypes).

        See Also: instantiate()

        Note: in subclasses, override _match instead of this one.

        Typemap may get damaged when False is returned. This may get
        fixed eventually. '''
        if not self._match(other.dereference(),typemap) and not self._match(other.dereference().dropattrs(),typemap):
            # Matching didn't hold. Maybe that's because other is a
            # parameter, so in that case just initialise it.
            if type(other) == ParamType:
                other.assign(self)
                return True
            else: # Matching failed
                warn.warning("expected {0}, got {1}".format(self,other))
                return False
        else:
            return True

    def _match(self,other,typemap):
        return self==other

    def instantiate(self,typemap):
        ''' The companion method to match(). Applies the given type
        mapping to ParamTypes contained in self, and returns the
        resulting type. self is not modified. '''
        return self

class ErrorType(MixedType):
    ''' The type of an expression whose type analysis failed (e.g. the
    return type of a function that doesn't return, the element type of
    a value that is not an array, etc) '''
    def __init__(self,msg=''):
        ''' msg optionally gives information about the error. '''
        self.msg = msg

    def __str__(self):
        return '<error>'

    def __or__(self,other):
        # Note, we may eventually include error message from other
        # into self
        return self

    def __and__(self,other):
        # Note sure about that. Shouldn't ands converge to <empty>?
        return self

    def cast(self,ptype):
        # Maybe errors should be an *attribute* of types rather than a
        # *subclass* of Mixed?
        return self

    def _match(self,other,typemap):
        return True

class ParamType(MixedType):
    ''' The type of a function parameter. When matching types,
    parameter types get mapped to actual types. 
    
    When analysing a function body, more information can be gathered
    about parameter types. When that happens, the parameter acquires a
    *value* (which itself may contain more parameter types if it is
    not full known) '''

    def __init__(self,name):
        ''' The name is just a user-friendly label for use in error
        messages etc. Two paramtypes with the same name are *not*
        equal, just like two PHP variables with the same name can be
        distinct. '''
        self.name = name
        self.value = None
    def dereference(self):
        if self.value:
            return self.value.dereference()
        else:
            return self
    def __str__(self):
        if self.value:
            return str(self.value)
        else:
            return '{'+self.name+'}'
    def _match(self,other,typemap):
        if self.value:
            return self.value.match(other,typemap,reporting.noWarn)

        if self in typemap:
            typemap[self] = typemap[self] | other
        else:
            typemap[self] = other
        return True

    def assign(self,value):
        ''' Tell this parameter it should be equal to value, or more
        specific. Note that value is not dereferenced, so that future
        assignments performed on value itself will also affect
        self. '''
#        print('{0} := {1}'.format(self.name,value))
        if self.value:
            self.value = self.value & value
        else:
            self.value = value

    def instantiate(self,typemap):
        if self.value:
            return self.value.instantiate(typemap)

        if self in typemap:
            return typemap[self]
        else:
            return self

class UnsetType(MixedType):
    ''' The type of an uninitialised variable (so it may be controlled
    by the attacker if register globals is on) '''
    def __str__(self):
        return '<not initialised>'

class EmptyType(MixedType):
    ''' The element type of an empty array. The subtype of every other
    type. '''
    def __str__(self):
        return '<empty>'

    def __or__(self,other):
        return other

    def __ror__(self,other):
        return other

    def __eq__(self,other):
        return type(other) == EmptyType

class PrimType(MixedType):
    ''' A primitive, non-structured (i.e. not made out of smaller
    things like arrays) type such as number or string
    '''
    def __init__(self,typename):
        ''' typename should be in tokens.builtin_types '''
        self.typename = typename

    def __str__(self):
        return self.typename

    def __eq__(self,other):
        return type(other) == PrimType and self.typename == other.typename


class ArrType(MixedType):
    ''' The type of a PHP array. Its elements are (for now) all
    assumed to have the same type. A future version may record the
    types of specific elements separately '''
    def __init__(self,elttype):
        self.elttype = elttype

    def __str__(self):
        return 'array({0})'.format(self.elttype)

    # def reduce(self):
    #     return ArrType(self.elttype.reduce())

    def __eq__(self,other):
        return type(other) == ArrType and self.elttype == other.elttype

    def _match(self,other,typemap):
        return type(other) == ArrType and self.elttype.match(
            other.elttype,typemap,reporting.noWarn)

    def instantiate(self,typemap):
        return ArrType(self.elttype.instantiate(typemap))


class EscapedType(MixedType):
    ''' An object that has been escaped in some way '''
    def __init__(self,target,elttype):
        ''' elttype is the type the data had *before* escaping, target
        it the target against which we're escaping, for instance 'mysql'
        or 'html'. The special 'any' value may be used for numbers, that
        are invariant under escaping (?) '''
        self.target = target
        self.elttype = elttype

    def __str__(self):
        return '{0}escape({1})'.format(self.target,self.elttype)

    def dropattrs(self):
        return self.elttype.dropattrs()

    def __or__(self,other):
        if isinstance(other,EscapedType):
            if isinstance(other,TrustedType) or self.target == other.target:
                return EscapedType(self.target,self.elttype | other.elttype)
        return self.dropattrs() | other.dropattrs()
    def __ror__(self,other):
        return self.__or__(other)

    def __eq__(self,other):
        return type(other) == EscapedType and self.target == other.target and self.elttype == other.elttype

    def cast(self,ptype):
        if self.dropattrs() == PrimType(ptype):
            return self
        else:
            return MixedType.cast(self,ptype)
    def _match(self,other,typemap):
        if type(other) == EscapedType:
            return self.target == other.target and self.elttype.match(
                other.elttype,typemap,reporting.noWarn)
        elif type(other) == TrustedType:
            # Note, we match our elttype against other, NOT against
            # other.elttype so that escape1(escape2(...(x))) matches trusted(x)
            return self.elttype.match(other,typemap,reporting.noWarn)
        else:
            return False
    def instantiate(self,typemap):
        return EscapedType(self.target,self.elttype.instantiate(typemap))

class TrustedType(EscapedType):
    ''' An object that is trusted in that it doesn't require escaping,
    typically because it's a constant in the program. 

    It is a subtype of an escaped type for any target, because it can
    be in some sense assumed to be properly escaped for all targets '''
    def __init__(self,elttype):
        EscapedType.__init__(self,None,elttype)
    def __str__(self):
        return 'trusted {0}'.format(self.elttype)
    def dropattrs(self):
        return self.elttype.dropattrs()
    def __or__(self,other):
        if isinstance(other,TrustedType):
            # trusted | trusted = trusted
            return TrustedType(self.elttype | other.elttype)
        elif isinstance(other,EscapedType):
            # trusted | escaped = escaped

            # Using __or__ instead of | because python would otherwise
            # prefer to call self.__ror__(other)
            return other.__or__(self)
        else:
            return self.dropattrs() | other
    def __ror__(self,other):
         return self | other
    def cast(self,ptype):
        return TrustedType(PrimType(ptype))
    def __eq__(self,other):
        return type(other) == TrustedType and self.elttype == other.elttype
    def _match(self,other,typemap):
        return type(other) == TrustedType and self.elttype.match(
            other.elttype,typemap,reporting.noWarn)
    def instantiate(self,typemap):
        return TrustedType(self.elttype.instantiate(typemap))

# class ReturnedType(MixedType):
#     ''' The type returned by a particular function call. We need this
#     in case the function has not been seen yet '''
#     def __init__(self,fname,ptypes):
#         ''' fname: the name of the function being invoked
        
#         ptypes: a list of the types of the parameters '''
#         self.fname = fname
#         self.ptypes = ptypes[:]

#     def __str__(self):
#         return '{0}(...)'.format(self.fname)

#     def reduce(self):
#         if self.fname in funcs:
#             changeoccurred=True
#             if not funcs[self.fname].getreturntype():
#                 print("{0} has return type None!".format(self.fname))
#             return funcs[self.fname].getreturntype()
#         elif self.fname in consts:
#             changeoccurred=True
#             return consts[self.fname]
#         else:
#             # print("Warning, function {0} may not be defined.".format(expr[1][1]))
#             # return ['uninitialised']
#             return self

# Random thoughts about function types:
# A function type is given by a pair (input parameter types , output
# parameter types) where an input parameter is anything the function
# can obtain about the system's state, and an output parameter is
# anything it can alter about the system state. Specifically:
#
# 1. Global variables (including superglobals and session variables)
#    can act as input or output parameters, and are identified by
#    their names given as strings.
#
# 2. Formal parameters are input parameters, possibly output as well
#    if the &$name notation is used. They are identified by their
#    position, starting from zero (although the function refers to
#    them by names, like local variables)
#
# 3. The return value is an output parameter, identified by constant
#    -1.
#
# Other possible parameters would include database entries and the
# filesystem but I'm not doing those for now. Note that loading a php
# produced webpage is equivalent to calling such a function with only
# _SESSION, _GET and _POST as input parameters, and _SESSION as output
# parameter. I'm not considering the data sent to the browser to be an
# output parameter but that may change.
class FunType(MixedType):
    ''' The type of a function (distinct from ReturnType, that is the
    type of a *function call*). '''
    def __init__(self,inp,out,name):
        ''' inp and out are dictionaries mapping identifiers (as
        specified in the comment above) to types. name is the function
        name if you have one (only used for error messages). '''
        self.inp = inp
        self.out = out
        self.name = name

    def __str__(self):
        return '{0} -> {1}'.format(self.inp,str(self.out))

    def apply(self,context,ptypes,warn):
        ''' Simulate a call of a function of this type.
        
        context argument: the typingcontext in which the call occurs

        ptypes argument: A list of types, one for each parameter

        warn argument: ErrorInfo, enabled if you need the return value to be
        well-defined.

        returns: The return type of the function

        side effect: Alters types of global variables in the context,
        matching the side effects of the function self '''

        # First match the context and parameters to the input
        typemap={} # Matching dictionary
        for id,tp in self.inp.items():
            if type(id) == str:
                tp.match(context.gettype(id,warn.on()),typemap,warn.at("global $"+id))
            else:
                tp.match(ptypes[id],typemap,warn.at("parameter {0} of function {1}".format(id+1,self.name)))
        # Now typemap has been filled with values for ParamTypes so we
        # can instantiate the output parameters

        context.settypes({n: t.instantiate(typemap) for n,t in self.out.items() if type(n)==str})
        return self.getreturntype(warn).instantiate(typemap)

    def getreturntype(self,warn):
        if -1 in self.out:
            # if not self.out[-1]:
            #     print("Warning, ill-formed type {0}".format(self))
            return self.out[-1]
        else:
            warn.warning("using return value of a function that doesn't have any")
            return ErrorType()

# Maps function names to their types.
funcs={'isset':FunType({0:MixedType()},{-1:PrimType('boolean')},'isset'),
       'mysql_query':FunType({0:EscapedType('mysql',PrimType('string'))},
                             {-1:PrimType('resource')},'mysql_query'),
       'mysql_error':FunType({},{-1:PrimType('string')},'mysql_error'),
       'count':FunType({0:MixedType()},{-1:PrimType('num')},'count'),
       'mysql_real_escape_string':FunType({0:PrimType('string')},
                                          {-1:EscapedType('mysql',PrimType('string'))},'mysql_real_escape_string')
}

# Maps define()d constants to their types
consts={}

# def mergeattrs(a,b):
#     ''' a and b being two types, return a triple (p,a',b') where p is
#     their common prefix (taking subtyping into account), and a',b'
#     where a and b start to differ (i.e. you can consider a and b got
#     cast to p.a' and p.b'). WARNING if a and b are equal, a' and b'
#     will be empty. '''
#     p = []
#     for n,(pa,pb) in enumerate(zip(a,b)):
#         if pa == 'empty':
#             p += b[n:]
#             break
#         elif pb == 'empty':
#             p += a[n:]
#             break
#         elif pa == pb:
#             p.append(pa)
#         elif pa in ['trusted','mysql'] and pb in ['trusted','mysql']:
#             p.append('mysql')
#         elif pa in ['trusted','html'] and pb in ['trusted','html']:
#             p.append('html')
#         elif dropattrs(a[n:]) == dropattrs(b[n:]):
#             # a and b are not identical but removing semantic
#             # attributes makes them match again.
#             p += dropattrs(a[n:])
#             break
#         else:
#             return (p,a[n:],b[n:])
#     return (p,[],[])

def _analyseexpr(expr,context,warn):
    ''' Simulate execution of the given expression in the given
    context, and return the expression's return type. (The context may
    get modified during this call).

    Disable warn if the expression having no defined value is not
    a problem (e.g. when analysing an expression whose value is not
    used) '''
    if not expr:
        print('Skipping broken expression')
        return ErrorType()
    if expr[0][0] in tokens.binaryoperators:
        # The if is to prevent that warning about uninitialised
        # variables for lhs of assignments.
        if expr[0][0]==tokens.Assign:
            ptypes = [MixedType()] + [
                analyseexpr(e,context,warn) for e in expr[2:] ]
        else:
            ptypes = [ analyseexpr(e,context,warn) for e in expr[1:] ]
        # 1. Compute the returned value "rtype"

        if expr[0][0]==tokens.Assign:
            rtype = ptypes[1]
        elif expr[0][0] in [tokens.Minus,tokens.MinusAssign,tokens.Plus,tokens.PlusAssign,
                        tokens.Times,tokens.Divide,tokens.Modulo]:
            # Numerical operations
            rtype = TrustedType(PrimType('num'))
            for param in ptypes:
                rtype = rtype | param.cast('num')
        elif expr[0][0] in [tokens.Period, tokens.CatAssign]:
            # String operations
            rtype = TrustedType(PrimType('string'))
            for param in ptypes:
                rtype = rtype | param.cast('string')
        else:
            rtype = MixedType()
        # 2. Perform the assignment, if any
        if expr[0][0] in [tokens.MinusAssign, tokens.PlusAssign, tokens.CatAssign, tokens.Assign]:
            if expr[1][0][0]==tokens.Variable:
                context.settype(expr[1][0][1],rtype)
            else:
                warn.warning('Unrecognised l-value, skipping assignment')
        return rtype
    elif expr[0][0] in tokens.unaryoperators or expr[0][0] == tokens.Type:
        analyseexpr(expr[1],context,warn)
    elif expr[0][0] == tokens.Question:
        analyseexpr(expr[1],context,warn)
        analyseexpr(expr[2],context,warn)
        analyseexpr(expr[3],context,warn)
    elif expr[0][0] == tokens.String:
        return TrustedType(PrimType('string'))
    elif expr[0][0] == tokens.Number:
        return TrustedType(PrimType('num'))
    elif expr[0][0] == tokens.BuiltinConstant:
        return TrustedType(PrimType('boolean'))
    elif expr[0][0] == tokens.Variable:
        return context.gettype(expr[0][1],warn.on())
    elif expr[0][0] == tokens.FunctionCall:
        ptypes = [ analyseexpr(e,context,warn) for e in expr[2:] ]
        if expr[1][1] == 'define':
            if expr[2][0][0] == tokens.String:
                consts[expr[2][0][1]] = ptypes[1]
            else:
                warn.warning('lhs of {0} not a constant string, ignoring.'.format(parser.prettyexpr(expr)))
            return UnsetType()
        elif expr[1][1] == 'array':
            # Can't make this a builtin function because of the
            # unlimited argument count...
            r = EmptyType()
            for ptype in ptypes:
                # print('r = {0} | {1}'.format(r,ptype))
                r = r | ptype

            return ArrType(r)
        else:
            fname = expr[1][1]
            if fname in funcs:
                return funcs[fname].apply(context,ptypes,warn)
            elif fname in consts:
                return consts[fname]
            else:
                warn.warning("calling undefined function {0}.".format(fname))
                return ErrorType()

            # return ReturnedType(expr[1][1], ptypes).reduce()
    elif expr[0][0] == tokens.ArrayAccess:
        ptypes = [ analyseexpr(e,context,warn) for e in expr[1:] ]
        return ptypes[0].arrayelttype(warn)
    else:
        return MixedType()

def analyseexpr(expr,context,warn):
    t = _analyseexpr(expr,context,warn)
    if not t:
        print('{0} has undefined type.'.format(parser.prettyexpr(expr)))
        return ErrorType()
    else:
        return t
