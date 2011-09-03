#!/usr/bin/python3

import sys

import contexts
import parser
import reporting
import scanner
import tokens
import types

# The list of files we've opened (for include/require_once)
included=[]

def readblock(tokstream,context):
    ''' read a block, for instance what follows an if
    (something). Returns whether at least one token was consumed. '''

    tok = tokstream.peek()

    warn = reporting.ErrorInfo(tokstream)

    if tokstream.skip((tokens.Keyword,"require_once")):
        e = parser.readexpr(tokstream,required=True)
        types.analyseexpr(e,context,warn)
        if e[0][0]==tokens.String and e[0][1] not in included:
            readfile(e[0][1],context)
        # print('Reading Included File {0}'.format(parser.prettyexpr(e)))
        tokstream.require((tokens.Semicolon,))
    elif tokstream.skip((tokens.Keyword,"include")):
        e = parser.readexpr(tokstream,required=True)
        types.analyseexpr(e,context,warn)
        if e[0][0]==tokens.String:
            readfile(e[0][1],context)
        # print('Reading Included File {0}'.format(parser.prettyexpr(e)))
        tokstream.require((tokens.Semicolon,))
    elif tokstream.skip((tokens.Keyword,"exit")):
        e = parser.readexpr(tokstream,required=False)
        if e:
            types.analyseexpr(e,context,warn)

        tokstream.require((tokens.Semicolon,))
    elif tokstream.skip((tokens.Keyword,"echo")):
        e = parser.readexpr(tokstream,required=True)
        types.analyseexpr(e,context,warn)
        # print('Output to client: {0}'.format(parser.prettyexpr(e)))
        tokstream.require((tokens.Semicolon,))
    elif tokstream.skip((tokens.Keyword,"global")):
        context.markglobal([expr[0][1] for expr in parser.readexprseq(tokstream) if expr[0][0] == tokens.Variable])
        tokstream.require((tokens.Semicolon,))
    elif tokstream.skip((tokens.Keyword,"return")):
        e = parser.readexpr(tokstream,required=False)
        if e:
            context.setreturntype(
                types.analyseexpr(e,context,warn))
            
        # print('Function returning: {0}'.format(parser.prettyexpr(e)))
        tokstream.require((tokens.Semicolon,))
    elif tokstream.skip((tokens.OpeningCurly,)):
        readcode(tokstream,context)
        tokstream.require((tokens.ClosingCurly,),msg='for ending block')
    elif tokstream.skip((tokens.Keyword,"if")):
        tokstream.require((tokens.OpeningBracket,))
        cond = parser.readexpr(tokstream,required=True)
        tokstream.require((tokens.ClosingBracket,))
        types.analyseexpr(cond,context,warn)

        tcontext = contexts.ContextOverlay(context)
        fcontext = contexts.ContextOverlay(context)
        # True part
        readblock(tokstream,tcontext)
        if tokstream.skip((tokens.Keyword,"else")):
            # False part
            readblock(tokstream,fcontext)

        (tcontext | fcontext).apply()

    elif tokstream.skip((tokens.Keyword,"while")):
        tokstream.require((tokens.OpeningBracket,))
        cond = parser.readexpr(tokstream,required=True)
        tokstream.require((tokens.ClosingBracket,))
        types.analyseexpr(cond,context,warn)
        # print('starting while loop')
        # body
        readblock(tokstream,context)

    elif tokstream.skip((tokens.Keyword,"switch")):
        tokstream.require((tokens.OpeningBracket,))
        var = parser.readexpr(tokstream,required=True)
        tokstream.require((tokens.ClosingBracket,))
        types.analyseexpr(var,context,warn)
        tokstream.require((tokens.OpeningCurly,))
        while not tokstream.skip((tokens.ClosingCurly,)):
            if tokstream.skip((tokens.Keyword,"case")):
                val = parser.readexpr(tokstream,required=True)
            else:
                tokstream.require((tokens.Keyword,"default"))
            tokstream.require((tokens.Colon,))
            readcode(tokstream,context)

    elif tokstream.skip((tokens.Keyword,"for")):
        tokstream.require((tokens.OpeningBracket,))
        parser.readexprseq(tokstream) # initial state
        tokstream.require((tokens.Semicolon,))
        parser.readexprseq(tokstream) # test
        tokstream.require((tokens.Semicolon,))
        parser.readexprseq(tokstream) # increment
        tokstream.require((tokens.ClosingBracket,))
        # body
        readblock(tokstream,context)

    elif tokstream.skip((tokens.Keyword,"foreach")):
        tokstream.require((tokens.OpeningBracket,))
        arr = parser.readexpr(tokstream,required=True)
        tokstream.require((tokens.Keyword,"as"))
        var = parser.readexpr(tokstream,required=True)
        if tokstream.skip((tokens.MapsTo,)):
            key=var
            var=parser.readexpr(tokstream,required=True)
        tokstream.require((tokens.ClosingBracket,))
        types.analyseexpr(arr,context,warn)
        
        if var[0][0]==tokens.Variable:
            context.settype(var[0][1],
                            types.analyseexpr(arr,context,warn)
                            .arrayelttype(warn))

        lcontext = contexts.AutoTypingContext();

        readblock(tokstream,lcontext)

        lcontext.applyto(context,warn);

        # print('ending foreach')
    elif tokstream.skip((tokens.Keyword,"function")):
        tok = tokstream.peek()
        if tok[0] != tokens.FunctionName:
            print('{0}: WARNING, function name expected.'.format(tokstream.position()))
        else:
            next(tokstream)
            tokstream.require((tokens.OpeningBracket,))
            pnames = [e[0][1] for e in parser.readexprseq(tokstream) if e[0][0] == tokens.Variable]
            tokstream.require((tokens.ClosingBracket,))
            # body
            ctxt = contexts.LocalTypingContext(pnames,tok[1])
            readblock(tokstream,ctxt)
            types.funcs[tok[1]] = ctxt.getfuntype()
    else:
        e = parser.readexpr(tokstream,required=False)
        if e:
            # print(parser.prettyexpr(e))
            tokstream.require((tokens.Semicolon,))
            types.analyseexpr(
                e,context,reporting.ErrorInfo(tokstream,enabled=False))
        else:
            return False
    return True

def readcode(tokstream,context):
    while readblock(tokstream,context):
        pass

def readfile(fn,context):
    included.append(fn)
    print('Reading {0}...'.format(fn))
    try:
        tokenstream = iter(scanner.tokenstream(fn))
        while True:
            readcode(tokenstream,context)
            if tokenstream.peek() != (tokens.EndOfFile,):
                print('UNEXPECTED {0}'.format(tokens.prettyTok(next(tokenstream))))
            else:
                break
    except IOError:
        print('WARNING: problem reading {0}, giving up'.format(fn))
        return
    # print('Done with {0}.'.format(fn))


def main(argv):
    if len(argv) < 2:
        print("Usage: {0} <php file>".format(argv[0]))
        return 1
    
    globalTypingContext = contexts.TypingContext()
    globalTypingContext.settype('_GET',types.ArrType(types.PrimType('string')))
    globalTypingContext.settype('_POST',types.ArrType(types.PrimType('string')))
    globalTypingContext.settype('_SERVER',types.ArrType(
            types.TrustedType(types.PrimType('string'))))

    readfile(argv[1],globalTypingContext)

    # types.globalTypingContext.solve()

    globalTypingContext.printall()

    for n,t in types.funcs.items():
        print('{0} : {1}'.format(n,t))

    # print(types.consts)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
