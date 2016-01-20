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
        res = True
        if len(self.inputs) == 0:
            self.result.invalidate()
            return
        for summand in self.inputs:
            try:
                val = summand.get_value()
                res = res and val
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
      and %s \\""" % sink.get_source().get_varname() )
        compiler.get_loop_buffer().write("""
      and True""")
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

class SevenSegmentEncoderNode(Node):
    CATEGORY = "Encoder/Decoder"
    ID = 0x0005
    HR_NAME = _("7SEG Encoder")
    def __init__(self):
        self.res_u = Source.new(False)
        self.res_u.set_name("upper")
        self.res_u.set_varname("%d_res_u"%(id(self),))
        self.add_source(self.res_u)
        self.res_ul = Source.new(False)
        self.res_ul.set_name("upper left")
        self.res_ul.set_varname("%d_res_ul"%(id(self),))
        self.add_source(self.res_ul)
        self.res_ur = Source.new(False)
        self.res_ur.set_name("upper right")
        self.res_ur.set_varname("%d_res_ur"%(id(self),))
        self.add_source(self.res_ur)
        self.res_m = Source.new(False)
        self.res_m.set_name("middle")
        self.res_m.set_varname("%d_res_m"%(id(self),))
        self.add_source(self.res_m)
        self.res_ll = Source.new(False)
        self.res_ll.set_name("lower left")
        self.res_ll.set_varname("%d_res_ll"%(id(self),))
        self.add_source(self.res_ll)
        self.res_lr = Source.new(False)
        self.res_lr.set_name("lower right")
        self.res_lr.set_varname("%d_res_lr"%(id(self),))
        self.add_source(self.res_lr)
        self.res_l  = Source.new(False)
        self.res_l.set_name("lower")
        self.res_l.set_varname("%d_res_l"%(id(self),))
        self.add_source(self.res_l)

        self.in_1 = GFlow.SimpleSink.new(False)
        self.in_1.set_name("1")
        self.add_sink(self.in_1)
        self.in_2 = GFlow.SimpleSink.new(False)
        self.in_2.set_name("2")
        self.add_sink(self.in_2)
        self.in_4 = GFlow.SimpleSink.new(False)
        self.in_4.set_name("4")
        self.add_sink(self.in_4)
        self.in_8 = GFlow.SimpleSink.new(False)
        self.in_8.set_name("8")
        self.add_sink(self.in_8)

        self.childwidget = None

        self.set_name("7SEG Encoder")

    def do_calculations(self, dock, val=None):
        try:
            i_1 = self.in_1.get_value()
            i_2 = self.in_2.get_value()
            i_4 = self.in_4.get_value()
            i_8 = self.in_8.get_value()
        except ValueError as e:
            self.res_u.set_invalid()
            self.res_ul.set_invalid()
            self.res_ur.set_invalid()
            self.res_m.set_invalid()
            self.res_ll.set_invalid()
            self.res_lr.set_invalid()
            self.res_l.set_invalid()
            return

        num = (i_8 << 3) | (i_4 << 2) | (i_2 << 1) | i_1

        self.res_u.set_value(  num in (0x0,0x2,0x3,0x5,0x6,0x7,0x8,0x9,0xA,0xC,0xE,0xF))
        self.res_ul.set_value( num in (0x0,0x1,0x4,0x5,0x6,0x8,0x9,0xA,0xB,0xC,0xE,0xF))
        self.res_ur.set_value( num in (0x0,0x1,0x2,0x3,0x4,0x7,0x8,0x9,0xA,0xD))
        self.res_m.set_value(  num in (0x2,0x3,0x4,0x5,0x6,0x8,0x9,0xA,0xB,0xD,0xE,0xF))
        self.res_ll.set_value( num in (0x0,0x2,0x6,0x8,0xA,0xB,0xC,0xD,0xE,0xF))
        self.res_lr.set_value( num in (0x0,0x1,0x3,0x4,0x5,0x6,0x7,0x8,0x9,0xA,0xB,0xD))
        self.res.l.set_value(  num in (0x0,0x2,0x3,0x5,0x6,0x8,0x9,0xB,0xC,0xD,0xE))

    def generate_raspi_init(self, compiler):
        if compiler.rendered_as_init(self):
            return

        self.in_1.get_source().get_node().generate_raspi_init(compiler)
        self.in_2.get_source().get_node().generate_raspi_init(compiler)
        self.in_4.get_source().get_node().generate_raspi_init(compiler)
        self.in_8.get_source().get_node().generate_raspi_init(compiler)

        compiler.get_init_buffer().write("""
    %s = None
    %s = None
    %s = None
    %s = None
    %s = None
    %s = None
    %s = None"""% (
            self.res_u.get_varname(),
            self.res_ul.get_varname(),
            self.res_ur.get_varname(),
            self.res_m.get_varname(),
            self.res_ll.get_varname(),
            self.res_lr.get_varname(),
            self.res_l.get_varname()
        ))
        compiler.set_rendered_init(self)


    def generate_raspi_loop(self, compiler):
        if compiler.rendered_as_loop(self):
            return

        self.in_1.get_source().get_node().generate_raspi_loop(compiler)
        self.in_2.get_source().get_node().generate_raspi_loop(compiler)
        self.in_4.get_source().get_node().generate_raspi_loop(compiler)
        self.in_8.get_source().get_node().generate_raspi_loop(compiler)

        compiler.get_loop_buffer().write("""
    v%(node_id)s_number = (%(i_8)s << 3) | (%(i_4)s << 2) | (%(i_2)s << 1) | %(i_1)s
    %(res_u)s = v%(node_id)s_number in (0x0,0x2,0x3,0x5,0x6,0x7,0x8,0x9,0xA,0xC,0xE,0xF)
    %(res_ul)s = v%(node_id)s_number in (0x0,0x1,0x4,0x5,0x6,0x8,0x9,0xA,0xB,0xC,0xE,0xF)
    %(res_ur)s = v%(node_id)s_number in (0x0,0x1,0x2,0x3,0x4,0x7,0x8,0x9,0xA,0xD)
    %(res_m)s = v%(node_id)s_number in (0x2,0x3,0x4,0x5,0x6,0x8,0x9,0xA,0xB,0xD,0xE,0xF)
    %(res_ll)s = v%(node_id)s_number in (0x2,0x6,0x8,0xA,0xB,0xC,0xD,0xE,0xF)
    %(res_lr)s = v%(node_id)s_number in (0x1,0x3,0x4,0x5,0x6,0x7,0x8,0x9,0xA,0xB,0xD)
    %(res_l)s = v%(node_id)s_number in (0x2,0x3,0x5,0x6,0x8,0x9,0xB,0xC,0xD,0xE)
        """%{
                "node_id" : id(self),
                "i_8" : self.in_8.get_source().get_varname(),
                "i_4" : self.in_4.get_source().get_varname(),
                "i_2" : self.in_2.get_source().get_varname(),
                "i_1" : self.in_1.get_source().get_varname(),
                "res_u" : self.res_u.get_varname(),
                "res_ul" : self.res_ul.get_varname(),
                "res_ur" : self.res_ur.get_varname(),
                "res_m" : self.res_m.get_varname(),
                "res_ll" : self.res_ll.get_varname(),
                "res_lr" : self.res_lr.get_varname(),
                "res_l" : self.res_l.get_varname()
            })

        compiler.set_rendered_loop(self)

    def serialize(self, serializer):
        if serializer.is_serialized(self):
            return

        if self.in_1.get_source() is not None:
            self.in_1.get_source().get_node().serialize(serializer)
        if self.in_2.get_source() is not None:
            self.in_2.get_source().get_node().serialize(serializer)
        if self.in_4.get_source() is not None:
            self.in_4.get_source().get_node().serialize(serializer)
        if self.in_8.get_source() is not None:
            self.in_8.get_source().get_node().serialize(serializer)

        serialized = serializer.serialize_node(self)
        serializer.set_serialized(self, serialized)

    def deserialize(self, node_info):
        pass

class OrNode(Node):
    CATEGORY = "Digital"
    ID = 0x0002
    HR_NAME = _("Logical OR")
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

        self.set_name("OR")

    def do_calculations(self,dock,val=None):
        res = True
        if len(self.inputs) == 0:
            self.result.invalidate()
            return
        for summand in self.inputs:
            try:
                val = summand.get_value()
                res = res or val
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
    %s = False \\""" % self.result.get_varname())
        for sink in self.inputs:
            compiler.get_loop_buffer().write("""
      or %s \\""" % sink.get_source().get_varname() )
        compiler.get_loop_buffer().write("""
      or False""")
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

class XorNode(Node):
    CATEGORY = "Digital"
    ID = 0x0003
    HR_NAME = _("Logical XOR")

class NotNode(Node):
    CATEGORY = "Digital"
    ID = 0x0004
    HR_NAME = _("Logical NOT")

    def __init__(self):
        self.result = Source.new(False)
        self.result.set_name("result")
        self.result.set_varname("%d_result"%(id(self),))
        self.add_source(self.result)

        self.inp = GFlow.SimpleSink.new(False)
        self.inp.set_name("input")
        self.add_sink(self.inp)

        self.set_name("NOT")

    def do_calculations(self, dock, val=None):
        try:
            val = self.inp.get_value()
            self.result.set_value(not val)
        except:
            self.result.invalidate()

    def generate_raspi_init(self, compiler):
        if compiler.rendered_as_init(self):
            return

        self.inp.get_source().get_node().generate_raspi_init(compiler)

        compiler.get_init_buffer().write("""
    %s = None"""% self.result.get_varname())
        compiler.set_rendered_init(self)

    def generate_raspi_loop(self, compiler):
        if compiler.rendered_as_loop(self):
            return
        self.inp.get_source().get_node().generate_raspi_loop(compiler)

        compiler.get_loop_buffer().write("""
    %s = not %s""" % (self.result.get_varname(),
                     self.inp.get_source().get_varname()))
        compiler.set_rendered_loop(self)

    def serialize(self, serializer):
        if serializer.is_serialized(self):
            return

        self.inp.get_source().get_node().serialize(serializer)

        serialized = serializer.serialize_node(self)
        serializer.set_serialized(self, serialized)

    def deserialize(self, node_info):
        pass
