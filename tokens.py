builtin_constants=['false','true','null']
builtin_keywords=['as','case','default','echo','else','exit','for','foreach','function','global','if','include','require_once','return','switch','while']
builtin_functions=['array','count','isset','mysql_error','mysql_query','printf']
builtin_types=['int','string', 'boolean']

# A token is specified by a tuple whose first element is
# tokens.Something and whose later elements, if any, are parameters
# specified below

Raw=1 # something outside of <?php ?>
Comment=Raw+1 # This is actually never returned (anymore)
Semicolon=Comment+1
Comma=Semicolon+1
Period=Comma+1
OpeningBracket=Period+1
ClosingBracket=OpeningBracket+1
OpeningSquareBracket=ClosingBracket+1
ClosingSquareBracket=OpeningSquareBracket+1
OpeningCurly=ClosingSquareBracket+1
ClosingCurly=OpeningCurly+1
Ampersand=ClosingCurly+1
Pipe=Ampersand+1 # |
LessOrEqual=Pipe+1
LessThan=LessOrEqual+1
GreaterOrEqual=LessThan+1
GreaterThan=GreaterOrEqual+1
NotEqualsExactly=GreaterThan+1 # !==
EqualsExactly=NotEqualsExactly+1 # ===
NotEquals=EqualsExactly+1 # !=
Equals=NotEquals+1 # ==
Assign=Equals+1 # =
MapsTo=Assign+1 # =>
CatAssign=MapsTo+1 # .=
PlusAssign=CatAssign+1 # +=
MinusAssign=PlusAssign+1 # -=
Increment=MinusAssign+1 # ++
Plus=Increment+1
Decrement=Plus+1 # --
Minus=Decrement+1
Times=Minus+1
Divide=Times+1
Modulo=Divide+1
BooleanAnd=Modulo+1
BooleanOr=BooleanAnd+1
BooleanNot=BooleanOr+1
Question=BooleanNot+1 # question mark
Colon=Question+1
String=Colon+1 # Parameter: the unescaped string
BuiltinFunction=String+1 # Parameter: the function as a string
Keyword=BuiltinFunction+1 # Parameter: the keyword as a string
Type=Keyword+1 # Parameter: the type name
BuiltinConstant=Type+1 # Parameter: the constant name as a string
FunctionName=BuiltinConstant+1 # Parameter: function name
Number=FunctionName+1 # Parameter: the value as an int
Variable=Number+1 # Parameter: the name as a string (without the $)
EndOfFile=Variable+1 # Only returned by peek()
BadChar=EndOfFile+1 # Parameter: the character

# Some more items used in expressions:
ArrayAccess=OpeningSquareBracket
FunctionCall=OpeningBracket

# Tokens that can stand on their own as an expression ("nullary operators")
atoms = [String, Number, Variable, BuiltinConstant]

# Prefix unary operators
unaryoperators = [BooleanNot, Ampersand, Minus]

postfixoperators = [Increment, Decrement]

binaryoperators = [LessOrEqual, LessThan,
                   GreaterOrEqual, GreaterThan,
                   NotEqualsExactly, EqualsExactly, NotEquals, Equals,
                   CatAssign, PlusAssign, MinusAssign, Assign,
                   Plus, Minus, Times, Divide, Modulo,
                   Ampersand, Pipe, # bitwise operators
                   BooleanAnd, BooleanOr, Period]

def prettyTok(tok):
    ''' Pretty print the given token '''
    # print('printing token {0}'.format(tok))
    if (tok[0] == Raw):
        return 'raw character sequence'
    elif (tok[0] == Comment):
        return 'Comment'
    elif (tok[0] == Semicolon):
        return 'Semicolon'
    elif (tok[0] == Comma):
        return 'Comma'
    elif (tok[0] == Period):
        return 'Period'
    elif (tok[0] == OpeningBracket):
        return 'OpeningBracket'
    elif (tok[0] == ClosingBracket):
        return 'ClosingBracket'
    elif (tok[0] == OpeningSquareBracket):
        return 'OpeningSquareBracket'
    elif (tok[0] == ClosingSquareBracket):
        return 'ClosingSquareBracket'
    elif (tok[0] == OpeningCurly):
        return 'OpeningCurly'
    elif (tok[0] == ClosingCurly):
        return 'ClosingCurly'
    elif (tok[0] == Ampersand):
        return 'Ampersand'
    elif (tok[0] == Pipe):
        return 'Pipe'
    elif (tok[0] == LessOrEqual):
        return 'LessOrEqual'
    elif (tok[0] == LessThan):
        return 'LessThan'
    elif (tok[0] == GreaterOrEqual):
        return 'GreaterOrEqual'
    elif (tok[0] == GreaterThan):
        return 'GreaterThan'
    elif (tok[0] == NotEqualsExactly):
        return 'NotEqualsExactly'
    elif (tok[0] == EqualsExactly):
        return 'EqualsExactly'
    elif (tok[0] == NotEquals):
        return 'NotEquals'
    elif (tok[0] == Equals):
        return 'Equals'
    elif (tok[0] == MapsTo):
        return 'MapsTo'
    elif (tok[0] == CatAssign):
        return 'CatAssign'
    elif (tok[0] == PlusAssign):
        return 'PlusAssign'
    elif (tok[0] == MinusAssign):
        return 'MinusAssign'
    elif (tok[0] == Assign):
        return 'Assign'
    elif (tok[0] == Increment):
        return 'Increment'
    elif (tok[0] == Plus):
        return 'Plus'
    elif (tok[0] == Decrement):
        return 'Decrement'
    elif (tok[0] == Minus):
        return 'Minus'
    elif (tok[0] == Times):
        return 'Times'
    elif (tok[0] == Divide):
        return 'Divide'
    elif (tok[0] == Modulo):
        return 'Modulo'
    elif (tok[0] == BooleanAnd):
        return 'BooleanAnd'
    elif (tok[0] == BooleanOr):
        return 'BooleanOr'
    elif (tok[0] == BooleanNot):
        return 'BooleanNot'
    elif (tok[0] == Question):
        return 'Question'
    elif (tok[0] == Colon):
        return 'Colon'
    elif (tok[0] == String):
        return 'String {0}'.format(tok[1])
    elif (tok[0] == BuiltinFunction):
        return 'BuiltinFunction {0}'.format(tok[1])
    elif (tok[0] == Keyword):
        return 'Keyword {0}'.format(tok[1])
    elif (tok[0] == BuiltinConstant):
        return 'BuiltinConstant {0}'.format(tok[1])
    elif (tok[0] == FunctionName):
        return 'FunctionName {0}'.format(tok[1])
    elif (tok[0] == Number):
        return 'Number {0}'.format(tok[1])
    elif (tok[0] == Variable):
        return 'Variable {0}'.format(tok[1])
    elif (tok[0] == EndOfFile):
        return 'End of File'
    elif tok[0] == BadChar:
        return 'Unrecognised character {0}'.format(tok[1]) 
    else:
        return 'Unknown'

def shorttok(tok):
    ''' print the given token as it may appear in code '''
    if (tok[0] == Raw):
        return '?>...<?php'
    elif (tok[0] == Comment):
        return '/* ... */'
    elif (tok[0] == Semicolon):
        return ';'
    elif (tok[0] == Comma):
        return ','
    elif (tok[0] == Period):
        return '.'
    elif (tok[0] == OpeningBracket):
        return '('
    elif (tok[0] == ClosingBracket):
        return ')'
    elif (tok[0] == OpeningSquareBracket):
        return '['
    elif (tok[0] == ClosingSquareBracket):
        return ']'
    elif (tok[0] == OpeningCurly):
        return '{'
    elif (tok[0] == ClosingCurly):
        return '}'
    elif (tok[0] == Ampersand):
        return '&'
    elif (tok[0] == Pipe):
        return '|'
    elif (tok[0] == LessOrEqual):
        return '<='
    elif (tok[0] == LessThan):
        return '<'
    elif (tok[0] == GreaterOrEqual):
        return '>='
    elif (tok[0] == GreaterThan):
        return '>'
    elif (tok[0] == NotEqualsExactly):
        return '!=='
    elif (tok[0] == EqualsExactly):
        return '==='
    elif (tok[0] == NotEquals):
        return '!='
    elif (tok[0] == Equals):
        return '=='
    elif (tok[0] == MapsTo):
        return '=>'
    elif (tok[0] == CatAssign):
        return '.='
    elif (tok[0] == PlusAssign):
        return '+='
    elif (tok[0] == MinusAssign):
        return '-='
    elif (tok[0] == Assign):
        return '='
    elif (tok[0] == Increment):
        return '++'
    elif (tok[0] == Plus):
        return '+'
    elif (tok[0] == Decrement):
        return '--'
    elif (tok[0] == Minus):
        return '-'
    elif (tok[0] == Times):
        return '*'
    elif (tok[0] == Divide):
        return '/'
    elif (tok[0] == Modulo):
        return '%'
    elif (tok[0] == BooleanAnd):
        return ' and '
    elif (tok[0] == BooleanOr):
        return ' or '
    elif (tok[0] == BooleanNot):
        return ' not '
    elif (tok[0] == Question):
        return '?'
    elif (tok[0] == Colon):
        return ' : '
    elif (tok[0] == String):
        return '"{0}"'.format(tok[1])
    elif tok[0] in [BuiltinFunction,Keyword,BuiltinConstant,FunctionName]:
        return tok[1]
    elif (tok[0] == Number):
        return tok[1]
    elif (tok[0] == Variable):
        return '${0}'.format(tok[1])
    elif (tok[0] == EndOfFile):
        return '^D'
    else:
        return 'Unknown'
