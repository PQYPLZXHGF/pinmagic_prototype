from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import GFlow
from gi.repository import GtkFlow

from pinmagik.nodes.source import Source
# Placeholder function for gettext
def _(string):
    return string

EXCLUDES = [
    "EXCLUDES",
    "supports",
    "GLib",
    "Gtk",
    "GFlow",
    "GtkFlow",
    "source",
    "Source",
    "Node"
]

def supports(node, project_type):
    found_init = found_loop = False
    for x in dir(node):
        if x.find("generate_%s_init"%project_type) != -1:
            found_init = True
        if x.find("generate_%s_loop"%project_type) != -1:
            found_loop = True
    return found_init and found_loop

class Node(GFlow.SimpleNode):
    def __new__(cls, *args, **kwargs):
        x = GFlow.SimpleNode.new()
        x.__class__ = cls
        return x

"""
The childwidget of any node shall always be called childwidget
"""

class AndNode(Node):
    CATEGORY = "Digital"
    ID = 0x0001
    HR_NAME = _("Logical AND")
    def add_summand(self, widget=None, data=None):
        new_in = GFlow.SimpleSink.new(False)
        new_in.set_name("in")
        self.add_sink(new_in)
        new_in.connect("changed", self.do_calculations)
        self.inputs.append(new_in)
        self.do_calculations(None)
 
    def remove_summand(self, widget=None, data=None):
        if len(self.inputs) == 0:
            return
        inp = self.inputs[len(self.inputs)-1]
        inp.unlink_all()
        self.remove_sink(inp)
        self.inputs.remove(inp)
        inp.destroy()
        self.do_calculations(None)
       
    def __init__(self):
        self.inputs = []
    
        self.result = Source.new(False)
        self.result.set_name("result")
        self.result.set_varname("%d_result"%(id(self),))
        self.add_source(self.result)

        self.add_button = Gtk.Button.new_with_mnemonic("Add")
        self.remove_button = Gtk.Button.new_with_mnemonic("Rem")
        self.childwidget = Gtk.Box.new(Gtk.Orientation.HORIZONTAL,0)
        self.childwidget.add(self.add_button)
        self.childwidget.add(self.remove_button)
        self.add_button.connect("clicked", self.add_summand)
        self.remove_button.connect("clicked", self.remove_summand)

        self.set_name("AND")

    def do_calculations(self, dock, val=None):
        res = 0
        if len(self.inputs) == 0:
            self.result.invalidate()
            return
        for summand in self.inputs:
            try:
                val = summand.get_value()
                res += val
            except:
                self.result.invalidate()
                return
    
        self.result.set_value(res)

    def generate_raspi_init(self, compiler):
        if compiler.rendered_as_init(self):
            return

        for sink in self.inputs:
            sink.get_source().get_node().generate_raspi_init(compiler)

        compiler.get_init_buffer().write("""
    %s = None"""% self.result.get_varname())
        compiler.set_rendered_init(self)

    def generate_raspi_loop(self, compiler):
        if compiler.rendered_as_loop(self):
            return
        for sink in self.inputs:
            sink.get_source().get_node().generate_raspi_loop(compiler)

        compiler.get_loop_buffer().write("""
    %s = True \\""" % self.result.get_varname())
        for sink in self.inputs:
            compiler.get_loop_buffer().write("""
      && %s \\""" % sink.get_source().get_varname() )
        compiler.get_loop_buffer().write("""
      && True""")
        compiler.set_rendered_loop(self)

    def serialize(self, serializer):
        if serializer.is_serialized(self):
            return

        for sink in self.inputs:
            if sink.get_source() is None:
                continue
            sink.get_source().get_node().serialize(serializer)

        serialized = serializer.serialize_node(self)
        serialized["node_info"]["inputcount"] = len(self.inputs)
        serializer.set_serialized(self, serialized)

    def deserialize(self, node_info):
        for x in range(node_info["inputcount"]):
            self.add_summand()

class OrNode(Node):
    CATEGORY = "Digital"
    ID = 0x0002
    HR_NAME = _("Logical OR")

class XorNode(Node):
    CATEGORY = "Digital"
    ID = 0x0003
    HR_NAME = _("Logical XOR")

class NotNode(Node):
    CATEGORY = "Digital"
    ID = 0x0004
    HR_NAME = _("Logical NOT")
