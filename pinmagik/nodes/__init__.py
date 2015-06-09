from gi.repository import Gtk
from gi.repository import GtkFlow

from pinmagik.nodes.source import Source
# Placeholder function for gettext
def _(string):
    return string

EXCLUDES = [
    "EXCLUDES",
    "supports",
    "Gtk",
    "GtkFlow",
    "source",
    "Source"
]

def supports(node, project_type):
    found_init = found_loop = False
    for x in dir(node):
        if x.find("generate_%s_init"%project_type) != -1:
            found_init = True
        if x.find("generate_%s_loop"%project_type) != -1:
            found_loop = True
    return found_init and found_loop

class AndNode(GtkFlow.Node):
    CATEGORY = "Digital"
    ID = 0x0001
    HR_NAME = _("Logical AND")
    def add_summand(self, widget=None, data=None):
        new_in = GtkFlow.Sink.new(False)
        new_in.set_label("in")
        self.add_sink(new_in)
        new_in.connect("changed", self.do_calculations)
        self.inputs.append(new_in)
        self.do_calculations(None)
 
    def remove_summand(self, widget=None, data=None):
        inp = self.inputs[len(self.inputs)-1]
        inp.unset_source()
        self.remove_sink(inp)
        self.inputs.remove(inp)
        inp.destroy()
        self.do_calculations(None)
       
    def __init__(self):
        GtkFlow.Node.__init__(self)

        self.inputs = []
    
        self.result = Source.new(False)
        self.result.set_label("result")
        self.result.set_varname("%d_result"%(id(self),))
        self.add_source(self.result)

        self.add_button = Gtk.Button.new_with_mnemonic("Add")
        self.remove_button = Gtk.Button.new_with_mnemonic("Rem")
        self.btnbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL,0)
        self.btnbox.add(self.add_button)
        self.btnbox.add(self.remove_button)
        self.add_button.connect("clicked", self.add_summand)
        self.remove_button.connect("clicked", self.remove_summand)
        self.add(self.btnbox)
        self.show_all()

        self.set_title("Operation")
    
        self.set_border_width(10)

    def do_calculations(self, dock, val=None):
        res = 0
        for summand in self.inputs:
            try:
                val = summand.get_value()
                res += val
            except:
                self.result.invalidate()
                return
    
        self.result.set_value(res)

    def generate_raspi_init(self):
        pass

    def generate_raspi_loop(self):
        pass

class OrNode(GtkFlow.Node):
    CATEGORY = "Digital"
    ID = 0x0002
    HR_NAME = _("Logical OR")

class XorNode(GtkFlow.Node):
    CATEGORY = "Digital"
    ID = 0x0003
    HR_NAME = _("Logical XOR")

class NotNode(GtkFlow.Node):
    CATEGORY = "Digital"
    ID = 0x0004
    HR_NAME = _("Logical NOT")
