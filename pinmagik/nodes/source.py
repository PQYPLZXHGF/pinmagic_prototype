from gi.repository import GtkFlow

#TODO: write generally applicable GI-constructor decorator

class Source(GtkFlow.Source):
    @classmethod
    def new(cls, typ):
        x = GtkFlow.Source.new(typ)
        cls.__init__(x)
        x.__class__ = cls
        x._varname = ""
        return x

    def get_varname(self):
        return self._varname

    def set_varname(self, varname):
        self._varname = varname
