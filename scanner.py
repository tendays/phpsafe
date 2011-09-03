import tokens

class charstream:
    ''' An iterator on characters that supports arbitrary long
    readahead '''
    def __init__(self,filename):
        self.filename = filename

    def __iter__(self):
        self.linestream = open(self.filename)
        # currentline may be more than one line when readahead is used
        self.currentline = ""
        self.ln = 1 # Line number
        self.col = 0 # next character we'll read from currentline
        return self

    def __next__(self):
        if self.col >= len(self.currentline):
            self.currentline = next(self.linestream)
            # if this fails, we reached the end of the file and
            # chars() itself will terminate.
            self.col = 0

        if self.currentline[self.col] == '\n':
            self.ln += 1

        self.col += 1
        return self.currentline[self.col-1]

    def skip(self,count):
        self.ln += self.currentline[self.col:self.col+count].count("\n")
        self.col += count

    def linenumber(self):
        return self.ln

    def readahead(self,count):
        ''' Return the count next characters without consuming them,
        or None if there aren't that many characters left in the file
        '''
        try:
            while len(self.currentline)-self.col < count:
                self.currentline += next(self.linestream)

            return self.currentline[self.col:self.col+count]
        except StopIteration:
            return None

    def startswith(self,prefix):
        ''' if the next few characters are equal to the prefix,
        consume them and return True. Otherwise do nothing and return
        False. '''
        if self.readahead(len(prefix)) == prefix:
            self.skip(len(prefix))
            return True
        else:
            return False

    def startswithwhite(self):
        ''' return True if the next character is a whitespace '''
        c = self.readahead(1)
        return c in ' \t\n'

    def startswithnumeric(self):
        ''' return True if the next character is a number '''
        c = self.readahead(1)
        return c in '0123456789'

    def startswithalpha(self):
        ''' return True if the next character can _start_ a keyword or
        function name '''
        c = self.readahead(1)
        return c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'

    def startswithalphanumeric(self):
        ''' return True if the next character can _continue_ an
        identifier, keyword or function name '''
        c = self.readahead(1)
        return c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_012356789'

def scanfile(stream):
    try:
        while True:
            if stream.startswith('<?php'):
                # print('starting php block')
                while not stream.startswith('?>'):
                    if stream.startswithwhite():
                        next(stream)
                    elif stream.startswith('/*'):
                        while not stream.startswith('*/'):
                            next(stream)
                        # yield (tokens.Comment,)
                    elif stream.startswith('//'):
                        while not stream.startswith('\n'):
                            next(stream)
                        # yield (tokens.Comment,)
                    elif stream.startswith(';'):
                        yield (tokens.Semicolon,)
                    elif stream.startswith(','):
                        yield (tokens.Comma,)
                    elif stream.startswith('.='):
                        yield (tokens.CatAssign,)
                    elif stream.startswith('.'):
                        yield (tokens.Period,)
                    elif stream.startswith('('):
                        yield (tokens.OpeningBracket,)
                    elif stream.startswith(')'):
                        yield (tokens.ClosingBracket,)
                    elif stream.startswith('['):
                        yield (tokens.OpeningSquareBracket,)
                    elif stream.startswith(']'):
                        yield (tokens.ClosingSquareBracket,)
                    elif stream.startswith('{'):
                        yield (tokens.OpeningCurly,)
                    elif stream.startswith('}'):
                        yield (tokens.ClosingCurly,)
                    elif stream.startswith('<='):
                        yield (tokens.LessOrEqual,)
                    elif stream.startswith('<'):
                        yield (tokens.LessThan,)
                    elif stream.startswith('>='):
                        yield (tokens.GreaterOrEqual,)
                    elif stream.startswith('>'):
                        yield (tokens.GreaterThan,)
                    elif stream.startswith('==='):
                        yield (tokens.EqualsExactly,)
                    elif stream.startswith('=='):
                        yield (tokens.Equals,)
                    elif stream.startswith('=>'):
                        yield (tokens.MapsTo,)
                    elif stream.startswith('='):
                        yield (tokens.Assign,)
                    elif stream.startswith('++'):
                        yield (tokens.Increment,)
                    elif stream.startswith('+='):
                        yield (tokens.PlusAssign,)
                    elif stream.startswith('+'):
                        yield (tokens.Plus,)
                    elif stream.startswith('-='):
                        yield (tokens.MinusAssign,)
                    elif stream.startswith('--'):
                        yield (tokens.Decrement,)
                    elif stream.startswith('-'):
                        yield (tokens.Minus,)
                    elif stream.startswith('*'):
                        yield (tokens.Times,)
                    elif stream.startswith('/'):
                        yield (tokens.Divide,)
                    elif stream.startswith('%'):
                        yield (tokens.Modulo,)
                    elif stream.startswith('&&'):
                        yield (tokens.BooleanAnd,)
                    elif stream.startswith('&'):
                        yield (tokens.Ampersand,)
                    elif stream.startswith('||'):
                        yield (tokens.BooleanOr,)
                    elif stream.startswith('|'):
                        yield (tokens.Pipe,)
                    elif stream.startswith('!=='):
                        yield (tokens.NotEqualsExactly,)
                    elif stream.startswith('!='):
                        yield (tokens.NotEquals,)
                    elif stream.startswith('!'):
                        yield (tokens.BooleanNot,)
                    elif stream.startswith('?'):
                        yield (tokens.Question,)
                    elif stream.startswith(':'):
                        yield (tokens.Colon,)
                    elif stream.startswith('"'):
                        s=''
                        while not stream.startswith('"'):
                            if stream.startswith('\\'):
                                # when seeing a backslash, reading the
                                # next char even if it's a "
                                pass
                            s += next(stream)
                        yield (tokens.String,s)
                    elif stream.startswith("'"):
                        s=''
                        while not stream.startswith("'"):
                            if stream.startswith('\\'):
                                # when seeing a backslash, reading the
                                # next char even if it's a "
                                pass
                            s += next(stream)
                        yield (tokens.String,s)
                    elif stream.startswithalpha():
                        s=''
                        while stream.startswithalphanumeric():
                            s += next(stream)

                        if s in tokens.builtin_functions:
                            yield (tokens.BuiltinFunction,s)
                        elif s in tokens.builtin_keywords:
                            yield (tokens.Keyword,s)
                        elif s in tokens.builtin_constants:
                            yield (tokens.BuiltinConstant,s)
                        elif s in tokens.builtin_types:
                            yield (tokens.Type,s)
                        else:
                            yield (tokens.FunctionName,s)
                    elif stream.startswithnumeric():
                        s=''
                        # Exponent notation not (yet) supported
                        while stream.startswithnumeric():
                            s += next(stream)
                        if stream.startswith('.'):
                            s += '.'
                        while stream.startswithnumeric():
                            s += next(stream)

                        yield (tokens.Number,s)
                    elif stream.startswith('$'):
                        s=''
                        while stream.startswithalphanumeric():
                            s += next(stream)
                        yield (tokens.Variable,s)

                    else:
                        yield (tokens.BadChar,next(stream))
                # print('ending php block')
            else:
                char = next(stream)
                # print('col {0}: {1}'.format(col,char))
    except StopIteration:
        pass
        # print('end of file')

class tokenstream:
    ''' Takes a filename string and returns a stream of tokens that
    supports reading one token ahead '''
    def __init__(self,filename):
        self.filename=filename

    def __iter__(self):
        # character stream with readahead
        self.charstream = iter(charstream(self.filename))
        # token stream with no readahead
        self.stream=iter(scanfile(self.charstream))
        self.nexttok = None
        return self

    def __next__(self):
        if self.nexttok:
            nexttok = self.nexttok
            self.nexttok = None
            return nexttok
        else:
            return next(self.stream)

    def position(self):
        ''' Return the filename and line number of the latest returned
        (or peeked!) token'''
        return '{0}:{1}'.format(self.filename,self.charstream.linenumber())

    def peek(self):
        ''' Return the next token without consuming it, or None if
        we're a the end of the file. Unlike next() itself, this never
        raises StopIteration '''
        try:
            if not self.nexttok:
                self.nexttok = next(self.stream)
                # print('Peeking {0}'.format(tokens.shorttok(self.nexttok)))
        except StopIteration:
            return (tokens.EndOfFile,)
        
        return self.nexttok

    def skip(self,tok):
        ''' if the next token it is equal to tok, consume it and
        return True. Otherise do nothing and return False'''
        if self.peek()==tok:
            next(self)
            return True
        else:
            return False

    def require(self,tok,msg=''):
        ''' Like skip but prints a warning if said token wasn't found. msg can detail why that particular token is needed. '''
        if self.skip(tok):
            return True
        else:
            print('{0}: WARNING, {1} expected {3}, got {2}.'.format(self.position(), tokens.prettyTok(tok), tokens.prettyTok(self.peek()),msg))
            return False

