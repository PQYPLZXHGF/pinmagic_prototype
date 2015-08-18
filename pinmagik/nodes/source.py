from gi.repository import GFlow

#TODO: write generally applicable GI-constructor decorator

class Source(GFlow.SimpleSource):
    @classmethod
    def new(cls, typ):
        x = GFlow.SimpleSource.new(typ)
        cls.__init__(x)
        x.__class__ = cls
        x._varname = ""
        return x

    def get_varname(self):
        return "v"+self._varname

    def set_varname(self, varname):
        self._varname = varname
