import types
import reporting

class TypingContext:
    ''' A description of a particular scope, that can be either the
    top-level scope or (when created as a localtypingcontext) the
    scope of a function. '''

    def __init__(self):
        self.td={}

    def settype(self,varname,vartype):
        ''' Set the type of the given variable. If the variable was
        declared as global, will be set it in the global scope
        instead. If the variable was already defined, will replace the
        old type [PREVIOUSLY: unify the existing and given types] '''
        # if varname in self.td:
        #     self.td[varname] = self.td[varname] | vartype
        # else:
        self.td[varname] = vartype

    def settypes(self,d):
        ''' Like settype but takes a dictionary name->type '''
        # if varname in self.td:
        #     self.td[varname] = self.td[varname] | vartype
        # else:
        self.td.update(d)

    def setreturntype(self,vartype):
        ''' Tell the typing context you just encountered a "return" statement '''
        # The following test was needed because of bugs in phpsafe
        # if not vartype:
        #     print('Setting a None return type!')
        self.settype(-1,vartype)

    def gettype(self,varname,warn):
        if varname in self.td:
            # if not self.td[varname]:
            #     print("Warning, ${0} has bad type None.".format(varname))
            return self.td[varname]
        else:
            warn.warning("${0} may not have been initialised.".format(varname))
            return types.UnsetType()

    def __contains__(self,item):
        return item in self.td

    def hasreturntype(self):
        return -1 in self

    def getreturntype(self,warn):
        return self.gettype(-1,warn)

    # def solve(self):
    #     ''' Attempts to solve all typing constraints constructed when
    #     analysing the source code. '''
    #     changeoccurred=True # true, to kickstart the loop
        
    #     while changeoccurred:
    #         changeoccurred=False
    #         for v,t in self.td.items():
    #             self.td[v] = t.reduce()

    def printall(self):
        for v,t in sorted(self.td.items()):
            print('${0} : {1}'.format(v,t))

    # print('Variables of unknown type:')

    # for v,t in td.items():
    #     if t==['unknown']:
    #         print(v)

class ContextOverlay(TypingContext):
    ''' Overlays permit simulating the effects of a bit of code on a
    Typing Context, without actually modifying it. Used for instance
    when typing an if-else statement. An overlay is made for each
    branch, overlays are merged and then only applied to the typing
    context. '''
    def __init__(self,bg):
        ''' bg: (as in background) the context on which to apply this
        overlay.'''
        self.bg = bg
        TypingContext.__init__(self)

    def gettype(self,varname,warn):
        if varname in self.td:
            return TypingContext.gettype(self,varname,warn)
        else:
            return self.bg.gettype(varname,warn)

    def __contains__(self,item):
        return (item in self.td) or (item in self.bg)

    def apply(self):
        ''' Apply the changes described in this overlay to the
        background context. '''
        for (n,t) in self.td.items():
            self.bg.settype(n,t)

    def __or__(self,other):
        ''' Constructs the union overlay of self and other. When they
        specify different types for a single variable, the types
        themselves are or-ed.

        Return value is only meaningful if self and other have the
        same background. '''
        r = ContextOverlay(self.bg)
        for n in set(self.td) | set(other.td):
            r.settype(n,self.gettype(n,reporting.noWarn) |
                      other.gettype(n,reporting.noWarn))
        return r
            

class AutoTypingContext(TypingContext):
    ''' A Typing Context where variables are automatically initialised
    to a ParamType when referenced, instead of throwing
    uninitialised-variable errors '''
    def __init__(self):
        TypingContext.__init__(self)
        # itypes maps "auto-initialised" names to their initial type
        # Warning, LocalTypingContext.getfuntype relies on this being
        # named that way
        self.itypes = {}

    def copy(self):
        ''' Returns a shallow copy of self '''
        r = AutoTypingContext()
        r.itypes = self.itypes[:]
        r.td = self.td[:]
        return r

    def gettype(self,varname,warn):
        ''' warn is interpreted as follows: if not enabled, you don't
        actually care whether the variable is initialised, so no
        ParamType is created if it doesn't exist already...'''
        if warn.enabled and varname not in self.td:
            p = types.ParamType('$'+varname)
            self.itypes[varname] = p
            self.settype(varname,p)
        return TypingContext.gettype(self,varname,warn)

    def loop(self,warn):
        ''' Compute the fixpoint of self = self | self.applyto(self)
        to simulate an unknown number of repetition of the sequence
        corresponding to this context, for loops and recursion.'''
        prev=None
        curr=self
        while prev != curr:
            prev = curr
            curr = curr | curr.applyto(curr.copy(),warn)

    def applyto(self,other,warn):
        ''' Apply the self context to other, to simulate what would
        have happened if the sequence of gettype and settype done on
        self had actually been done on other. Returns other, for
        convenience. '''
        # Note striking similarity to types.FunType.apply. Could these
        # two be merged somehow?
        typemap={}
        for id,tp in self.itypes.items():
            tp.match(other.gettype(id,warn),typemap,warn)
        other.settypes({n: t.instantiate(typemap) for n,t in self.td.items()})
        return other

    def __eq__(self,other):
        return  (self.itypes == other.itypes) and (self.td == other.td)

    def __or__(self,other):
        ''' Constructs the union of (Auto)TypingContexts self and
        other. When they specify different types for a single
        variable, the types themselves are or-ed. '''
        r = AutoTypingContext()
        # parammap maps ParamTypes of self and other to the
        # corresponding ParamType of the union. Needed for renaming
        # the output types.
        parammap = {}
        # INTERSECT input types
        for n in set(self.itypes) | set(other.itypes):
            # Create new ParamTypes for the union type so that self
            # and other don't get mysteriously affected by this or
            # future calls on r
            pt = r.gettype(n)
            for i in {self.itypes, other.itypes}:
                if n in i:
                    parammap[i[n]] = pt
                    pt.assign(i[n])
        # UNION output types 
        for n in set(self.td) | set(other.td):
            r.settype(n,(self.gettype(n,reporting.noWarn) |
                      other.gettype(n,reporting.noWarn)).instantiate(parammap))
        return r

class LocalTypingContext(TypingContext):
    ''' the typing context within a function. It aggregates two typing
    contexts, one for global variables and one for locals (which
    includes parameter types and the return value, if any). '''

    def __init__(self,pnames,name='anonymous'):
        ''' pnames: a list of parameter names as strings.
        
        name: the function name for which this is a context, if you
        have one (only used for error messages) '''

        self.name = name

        # Contains all global variables that are used from this
        # TypingContext. self.td contains local variables.
        self.globals = AutoTypingContext()

        # globalnames: a set of names declared as global.
        # Note that the domain of globals.itypes is distinct
        # from globalnames. globals.itypes only gets extended when a global
        # is used (and globals is extended when a global is
        # *assigned*). This avoids uninitialised errors when a
        # function initialises a global variable without relying on a
        # pre-existing value.

        # Inversely, when calling a function b() from a function a(),
        # b() may cause a() to have input (globals.itypes) or output
        # (globals) global parameters that are not declared in
        # globalnames

        self.globalnames = set()
        # The initial types of local variables, i.e. parameters. I
        # don't want to have LocalTypingContext inherit from
        # AutoTypingContext because only declared parameters become
        # ParamTypes. References to undeclared variables must be an
        # error

        # A list, because we need the order in getfuntype
        self.pitypes = [(n,types.ParamType('$'+n)) for n in pnames]
        # When the function starts, all that is available are the parameters
        self.td = dict(self.pitypes)
        # Super globals
        self.markglobal({"_GET","_POST","_SERVER"})

    def markglobal(self,names):
        ''' mark all variables in names (a list of strings) as
        global. WARNING: if one of those variables had already been
        defined, its current type is lost. '''
        self.globalnames.update(names)

    def gettype(self,varname,warn):
        if varname in self.globalnames:
            return self.globals.gettype(varname,warn)
        else:
            return TypingContext.gettype(self,varname,warn)

    def __contains__(self,item):
        return (item in self.td) or (item in self.globals)

    def settype(self,varname,vartype):
        if varname in self.globalnames:
            return self.globals.settype(varname,vartype)
        else:
            return TypingContext.settype(self,varname,vartype)

    def settypes(self,d):
        for n,t in d.items():
            self.settype(n,t)

    # def settype(self,varname,vartype):
    #     if varname in self.inherited:
    #         globalTypingContext.settype(varname,vartype)
    #     else:
    #         TypingContext.settype(self,varname,vartype)

# WARNING, if settype gets overriden here, either override settypes as
# well, or make TypingContext.settypes() call settype()

    # def gettype(self,varname):
    #     if varname in self.inherited:
    #         return globalTypingContext.gettype(varname)
    #     else:
    #         return TypingContext.gettype(self,varname)

    def getfuntype(self):
        ''' Return the function type corresponding to this context. '''
        inp = {num:ptype for num,(name,ptype) in enumerate(self.pitypes)}
        inp.update(self.globals.itypes)

        out = {}
        if self.hasreturntype():
            out[-1] = self.getreturntype(reporting.noWarn)
        out.update(self.globals.td)

        return types.FunType(inp,out,self.name)

