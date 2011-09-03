class ErrorInfo:
    ''' Contains information about how we got to wherever we are,
    so that error messages can be explicit enough '''
    def __init__(self,tokstream,enabled=True,msg=''):
        ''' If enabled is set to False, error reporting is disabled
        through this object.
        '''
        # For now we just pass a token stream. Eventually, the token
        # stream itself will maintain an immutable errorinfo property
        # itself.
        self.tokstream = tokstream
        self.enabled = enabled
        self.msg = msg

    def warning(self,msg):
        if self.enabled:
            print('{0}: {1}Warning, {2}'.format(
                    self.tokstream.position(),self.msg,msg))

    def at(self,msg):
        ''' Return a copy of this object, enabled, and with the given
        extra piece of context/information'''
        return ErrorInfo(self.tokstream,True,self.msg + msg + ': ')

    def on(self):
        ''' Return a copy of this object, with warnings enabled '''
        if self.enabled:
            return self
        else:
            return ErrorInfo(self.tokstream,True,self.msg)

class WithoutWarning:
    ''' Pass this to those expecting ErrorInfo instances when you
    *never* want to output anything '''
    def __init__(self):
        pass

    def warning(self,msg):
        pass

    def at(self,msg):
        return self

    def on(self):
        return self

noWarn = WithoutWarning()
