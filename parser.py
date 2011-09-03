import tokens

# An expression is specified by a tuple whose first element is a
# token, telling what kind of expression it is, much like a lisp
# expression, and other elements are its parameters. For instance
#
# $a = ($b+2)*$c[4]-something(8)
#
# is represented as
#
# (Assign, (Variable, "a"), (Minus, (Times, (Plus (Variable, "b"),
# (Number, 2)), (ArrayAccess, (Variable, "c"), (Number, 4))),
# (FunctionCall, (FunctionName, "something"), (Number, 8))))

def readexprseq(tokstream):
    ''' Read a (possibly empty) comma-separated sequence of
    expressions, return them as a list. Expressions of the form (a) =>
    (b) are also permitted '''
    r = []
    while True:
        x = readexpr(tokstream,required=False)
        if x:
            if tokstream.skip((tokens.MapsTo,)):
                x = ((tokens.MapsTo,),x,readexpr(tokstream,required=True))
                
            r.append(x)
        else:
            return r
        if not tokstream.skip((tokens.Comma,)):
            return r
    
def readexpr(tokstream,required):
    ''' Parses an expression from the given token stream, an instance
    of tokenstream. Returns None if the current point doesn't look
    like an expression. Set required to true if absence of expression
    should fail dramatically, otherwise you'll just get None if the
    stream doesn't start like an expression. '''

    tok = tokstream.peek()

    if not tok:
        if required:
            print('Expression expected, got End of file')
        return None
    
    if tok[0] == tokens.OpeningBracket:
        next(tokstream)
        # Check if this is a cast
        tok = tokstream.peek()
        if tok and tok[0] == tokens.Type:
            t = next(tokstream)
            tokstream.require((tokens.ClosingBracket,),msg='to close cast brackets')
            currentexpr = (t,readexpr(tokstream,required=True))
        else:
            currentexpr = readexpr(tokstream,required=True)
            tokstream.require((tokens.ClosingBracket,),msg='after expression {0}'.format(prettyexpr(currentexpr)))
    elif tok[0] in tokens.atoms:
        next(tokstream)
        currentexpr = (tok,)
    elif tok[0] in [tokens.BuiltinFunction, tokens.FunctionName]:
        next(tokstream)
        currentexpr = [(tokens.FunctionCall,), tok] # a list, to permit adding parameters one at a time
# Having brackets and a parameter list is optional (because tok could be a *constant*, but now we can't make the difference between f() and f. Should really have a [list]
        if (tokstream.skip((tokens.OpeningBracket,))):
            currentexpr.extend(readexprseq(tokstream))
            tokstream.require((tokens.ClosingBracket,),msg='to close {0} function call'.format(tok[1]))
        # else:
        #     print('Warning: is {0} a constant or a keyword?'.format(tok[1]))

        currentexpr = tuple(currentexpr)
    elif tok[0] in tokens.unaryoperators:
        currentexpr = (next(tokstream),readexpr(tokstream,required=True))
    else:
        if required:
            print('{0}: WARNING: Expression expected, got {1}.'.format(tokstream.position(),tokens.prettyTok(tok)))
        return None

    while True:
    # currentexpr contains something, see if it is the first element of a binary/ternary expression...

        tok = tokstream.peek()
        if tok[0] == tokens.OpeningSquareBracket:
            next(tokstream)

            t = [(tokens.ArrayAccess,),currentexpr]
            t.extend(readexprseq(tokstream))
            currentexpr = tuple(t)
            tokstream.require((tokens.ClosingSquareBracket,))
        elif tok[0] == tokens.OpeningCurly:
            # As in: $string{characternumber}
            next(tokstream)

            t = [(tokens.ArrayAccess,),currentexpr]
            t.extend(readexprseq(tokstream))
            currentexpr = tuple(t)
            tokstream.require((tokens.ClosingCurly,),msg='for closing string character reference')
        elif tok[0] in tokens.postfixoperators:
            currentexpr = (next(tokstream), currentexpr)
        elif tok[0] in tokens.binaryoperators:
            currentexpr = (next(tokstream), currentexpr, readexpr(tokstream,required=True))
        elif tok[0] == tokens.Question:
            next(tokstream)
            t = readexpr(tokstream,required=True)
            tokstream.require((tokens.Colon,))
            currentexpr = (tok, currentexpr, t, readexpr(tokstream,required=True))
        else:
            return currentexpr

def prettyexpr(expr):
    if not expr:
        return '<error>'

    if expr[0][0] in tokens.binaryoperators:
        return prettyexpr(expr[1]) + tokens.shorttok(expr[0]) + prettyexpr(expr[2])
    elif expr[0][0] in tokens.unaryoperators:
        return tokens.shorttok(expr[0]) + prettyexpr(expr[1])
    elif expr[0][0] == tokens.Type:
        return tokens.shorttok(expr[0]) + prettyexpr(expr[1])
    elif expr[0][0] == tokens.Question:
        return prettyexpr(expr[1]) + '?' + prettyexpr(expr[2]) + ':' + prettyexpr(expr[3])
    elif expr[0][0] in tokens.atoms:
        return tokens.shorttok(expr[0])
    elif expr[0][0] == tokens.FunctionCall:
        r =  tokens.shorttok(expr[1]) + '('
        sep = ''
        for param in expr[2:]:
            r += sep + prettyexpr(param)
            sep = ','
        return r + ')'
    elif expr[0][0] == tokens.ArrayAccess:
        r =  prettyexpr(expr[1]) + '['
        sep = ''
        for param in expr[2:]:
            r += sep + prettyexpr(param)
            sep = ','
        return r + ']'
    else:
        return "Unknown Expression {0}".format(expr)

