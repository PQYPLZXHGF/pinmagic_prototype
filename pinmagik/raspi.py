
from gi.repository import GLib, GFlow, Gdk, Gtk, GtkFlow, Pango

from functools import reduce 
from math import pi

from pinmagik.nodes import Node
from pinmagik.nodes.source import Source

class RaspiContext(object):
    REV_1 = 0
    REV_2 = 1
    class Pin(object):
        OUTPUT = 0
        INPUT = 1
        def __init__(self, gpio_nr, pinnr):
            self.used_as = None
            self.gpio_nr = gpio_nr
            self.pinnr = pinnr
        def codify(self):
            ret = ""
            if self.used_as is not None:
                conf = ("RPi.GPIO.IN","RPi.GPIO.OUT")
                ret = "RPi.GPIO.setup(%d, %s)"%(self.gpio_nr,conf[self.used_as])
            return ret

    PINS_REV1 = [(0,3),(1,5),
                 (4,7),(7,26),
                 (8,24),(9,21),
                 (10,19),(11,23),
                 (14,8),(15,10),
                 (17,11),(18,12),
                 (21,13),(22,15),
                 (23,16),(24,18),
                 (25,22)]
    PINS_REV2 = [(2,3),(3,5),
                 (4,7),(7,26),
                 (8,24),(9,21),
                 (10,19),(11,23),
                 (14,8),(15,10),
                 (17,11),(18,12),
                 (27,13),(22,15),
                 (23,16),(24,18),
                 (25,22)]
    def __init__(self, revision):
        self.nodes = []
        self.pins = {} 
        if revision not in (RaspiContext.REV_1, RaspiContext.REV_2):
            print("You must supply a valid revision when constructing a raspi context")
            return
        self.revision = revision
        if self.revision == RaspiContext.REV_1:
            for gpio_nr, pinnr in RaspiContext.PINS_REV1:
                self.pins[gpio_nr] = RaspiContext.Pin(gpio_nr, pinnr)
        if self.revision == RaspiContext.REV_2:
            for gpio_nr, pinnr in RaspiContext.PINS_REV2:
                self.pins[gpio_nr] = RaspiContext.Pin(gpio_nr, pinnr)

    def get_pins(self):
        return self.pins

    def register_node(self, node):
        """ register a new node that works with this context """
        if not node in self.nodes:
            self.nodes.append(node)
 
    def set_pin_mode(self, gpio_nr, used_as):
        if used_as not in (None, RaspiContext.Pin.OUTPUT, RaspiContext.Pin.INPUT):
            print("You can only set a pin as OUTPUT, INPUT or None")
        self.pins[gpio_nr].used_as = used_as
   

class RaspiOutNode(Node):
    def __init__(self, raspi_context):
        raspi_context.register_node(self)
        self.context = raspi_context

        self.sinks = {}
        self.switches = {}

        for pin in self.context.get_pins():
            self.sinks[pin] = GFlow.SimpleSink.new(False)
            self.sink[pin].set_name("GPIO %02d"%pin)
            self.add_sink(self.sinks[pin])
            self.switches[pin] = Gtk.Switch.new()
            

    def generate_raspi_init(self):
        pass
    def generate_raspi_loop(self):
        pass

class RaspiInNode(Node):
    def __init__(self, raspi_context):
        raspi_context.register_node(self)
        self.context = raspi_context

        self.sources = {}
        self.switches = {}

        for pin in self.context.get_pins().keys():
            self.sources[pin] = Source.new(False)
            self.sources[pin].set_name("GPIO %02d"%pin)
            self.sources[pin].set_varname("%d_%d"%(id(self),pin))
            self.add_source(self.sources[pin])
            self.switches[pin] = Gtk.Switch.new()
            self.switches[pin].set_name("switch_%d"%(pin,))
            self.switches[pin].connect("notify::active", self.on_pin_switched, pin)

    def on_pin_switched(self, widget=None, data=None, pinnr=None):
        pin = self.context.get_pins()[pinnr]
        if self.switches[pinnr].get_active():
            self.context.set_pin_mode(pin.gpio_nr, pin.INPUT)
        else:
            self.context.set_pin_mode(pin.gpio_nr, None)

    def add_to_nodeview(self, nodeview):
        nodeview.add_node(self)
        for switch in self.switches.values():
            nodeview.register_child(self, switch)
        nr = RaspiInRenderer()
        nr.set_raspi_context(self.context)
        nodeview.set_node_renderer(self,nr)     

    def generate_raspi_init(self):
        pass
    def generate_raspi_loop(self):
        pass

class RaspiRenderer(object):
    HEADER_PIN_SPACING = 5
    HEADER_PIN_SIZE = 16
    HEADER_BORDER_PADDING = 10
    HEADER_BORDER_WIDTH = 2
    HEADER_SWITCH_DISTANCE = 30
    SWITCH_DOCK_DISTANCE = 10

    PIN_COLORS = {
        1  : "#f7bd21",
        2  : "#d62910",
        3  : "#42adff",
        4  : "#d62910",
        5  : "#42adff",
        6  : "#000000",
        7  : "#317310",
        8  : "#f7f721",
        9  : "#000000",
        10 : "#f7f721",
        11 : "#317310",
        12 : "#317310",
        13 : "#317310",
        14 : "#000000",
        15 : "#317310",
        16 : "#317310",
        17 : "#f7bd21",
        18 : "#317310",
        19 : "#c639ff",
        20 : "#000000",
        21 : "#c639ff",
        22 : "#317310",
        23 : "#c639ff",
        24 : "#c639ff",
        25 : "#000000",
        26 : "#c639ff"
    }
    @classmethod
    def get_color(cls, nr):
        def h2d(x):
            c = (int(x,16)/255.0)*20
            return round(c,2)
        c = cls.PIN_COLORS[nr][1:]
        c.strip("#")
        r = c[0:1]
        g = c[2:3]
        b = c[4:5]
        return (h2d(r),h2d(g),h2d(b),1.0)
        

class RaspiInRenderer(GtkFlow.NodeRenderer):
    __gtype_name__ = 'RaspiInRenderer'
    def __init__(self):
        super(RaspiInRenderer, self).__init__()
        self.switch_height = 30

    def set_raspi_context(self, ctx):
        self.raspi_ctx = ctx 

    def get_header_pin_pos(self, pin):
        pass

    def _get_header_height(self):
        return  13 * RaspiRenderer.HEADER_PIN_SIZE \
              + 12 * RaspiRenderer.HEADER_PIN_SPACING \
              +  2 * RaspiRenderer.HEADER_BORDER_PADDING \
              +  2 * RaspiRenderer.HEADER_BORDER_WIDTH

    def draw_pin_connections(self, cr, sc, alloc, border_width):
        #determine whether this connection is to be drawn
        y_offset = border_width
        x_offset =   2 * RaspiRenderer.HEADER_PIN_SIZE \
                  +  2 * RaspiRenderer.HEADER_PIN_SPACING \
                  +  2 * RaspiRenderer.HEADER_BORDER_PADDING \
                  +  2 * RaspiRenderer.HEADER_BORDER_WIDTH \
                  +  RaspiRenderer.HEADER_SWITCH_DISTANCE / 2 \
                  +  border_width
        for pin in self.raspi_ctx.get_pins().values():
            nr = pin.pinnr

            pin_y = alloc.height / 2 - (self._get_header_height() + border_width) / 2 \
                       + RaspiRenderer.HEADER_BORDER_PADDING
            pin_y += (int((nr+1) / 2)  \
                        * (RaspiRenderer.HEADER_PIN_SIZE + RaspiRenderer.HEADER_PIN_SPACING)) \
                        - RaspiRenderer.HEADER_PIN_SPACING
            pin_x = ((1-(nr % 2)) * (RaspiRenderer.HEADER_PIN_SIZE + RaspiRenderer.HEADER_PIN_SPACING)) \
                        + border_width + RaspiRenderer.HEADER_BORDER_WIDTH \
                        + RaspiRenderer.HEADER_BORDER_PADDING

            cr.save()
            col = RaspiRenderer.get_color(nr)
            cr.set_source_rgba(*col)
            cr.move_to(alloc.x+pin_x + RaspiRenderer.HEADER_PIN_SIZE / 2,
                       alloc.y+pin_y + RaspiRenderer.HEADER_PIN_SIZE / 2)
            cr.line_to(alloc.x+x_offset,
                       alloc.y+y_offset + self.switch_height / 2)
            cr.line_to(alloc.x+x_offset + RaspiRenderer.HEADER_SWITCH_DISTANCE / 2,
                       alloc.y+y_offset + self.switch_height / 2)
            cr.stroke()
            cr.restore()

            y_offset += self.switch_height

    def draw_pin(self, cr, sc, alloc, nr, border_width):
        offset_y = alloc.height / 2 - (self._get_header_height() + border_width) / 2 \
                   + RaspiRenderer.HEADER_BORDER_PADDING
        offset_y += (int((nr+1) / 2)  \
                    * (RaspiRenderer.HEADER_PIN_SIZE + RaspiRenderer.HEADER_PIN_SPACING)) \
                    - RaspiRenderer.HEADER_PIN_SPACING
        offset_x = ((1-(nr % 2)) * (RaspiRenderer.HEADER_PIN_SIZE + RaspiRenderer.HEADER_PIN_SPACING)) \
                    + border_width + RaspiRenderer.HEADER_BORDER_WIDTH \
                    + RaspiRenderer.HEADER_BORDER_PADDING

        cr.save()
        cr.set_source_rgba(0,0,0,1)
        if nr == 1:
            cr.rectangle(alloc.x + offset_x, alloc.y + offset_y,
                         RaspiRenderer.HEADER_PIN_SIZE, RaspiRenderer.HEADER_PIN_SIZE)
        else:
            cr.arc(alloc.x + offset_x + RaspiRenderer.HEADER_PIN_SIZE/2,
                   alloc.y + offset_y + RaspiRenderer.HEADER_PIN_SIZE/2,
                   RaspiRenderer.HEADER_PIN_SIZE/2,
                   0 , 2*pi)
        cr.stroke()
        col = RaspiRenderer.get_color(nr)
        cr.set_source_rgba(*col)
        if nr == 1:
            cr.rectangle(alloc.x + offset_x, alloc.y + offset_y,
                         RaspiRenderer.HEADER_PIN_SIZE, RaspiRenderer.HEADER_PIN_SIZE)
        else:
            cr.arc(alloc.x + offset_x + RaspiRenderer.HEADER_PIN_SIZE/2,
                   alloc.y + offset_y + RaspiRenderer.HEADER_PIN_SIZE/2,
                   RaspiRenderer.HEADER_PIN_SIZE/2,
                   0 , 2*pi)
        cr.fill()
        cr.restore()
        
    def draw_header(self, cr, sc, alloc, border_width):
        offset = alloc.height / 2 - (self._get_header_height() + border_width) / 2
        width = 2 * RaspiRenderer.HEADER_BORDER_PADDING \
              + 2 * RaspiRenderer.HEADER_PIN_SIZE \
                  + RaspiRenderer.HEADER_PIN_SPACING
        cr.save()
        cr.set_source_rgba(0.0,0.0,0.0,1.0)
        cr.rectangle(alloc.x + border_width, alloc.y + border_width + offset,
                     width, self._get_header_height())
        cr.stroke()
        cr.restore()
        for pin in range(26):
            pin += 1
            self.draw_pin(cr, sc,alloc, pin, border_width)
        self.draw_pin_connections(cr, sc, alloc, border_width)

    def do_draw_node(self, cr, sc, alloc, dock_renderers, children, 
                  border_width, editable):
        sc.save()
        sc.add_class(Gtk.STYLE_CLASS_BUTTON)
        Gtk.render_background(sc, cr, alloc.x, alloc.y, alloc.width, alloc.height)
        Gtk.render_frame(sc, cr, alloc.x, alloc.y, alloc.width, alloc.height)
        sc.restore()


        y_offset = 0 
        for child in sorted(children, key=lambda child: int(child.get_name().replace("switch_",""))):
            child_alloc = child.get_allocation()
            _, mw = child.get_preferred_width()
            _, mh = child.get_preferred_height()
            self.switch_height = mh
            child_alloc.x = border_width + 2*RaspiRenderer.HEADER_BORDER_WIDTH \
                                         + 2*RaspiRenderer.HEADER_PIN_SIZE \
                                         + 2*RaspiRenderer.HEADER_BORDER_PADDING \
                                         + 2*RaspiRenderer.HEADER_BORDER_WIDTH \
                                         +   RaspiRenderer.HEADER_PIN_SPACING \
                                         +   RaspiRenderer.HEADER_SWITCH_DISTANCE
            child_alloc.y = border_width + y_offset 
            child_alloc.width = mw
            child_alloc.height = mh
            child.size_allocate(child_alloc)
            child.show()
            self.emit("child-redraw", child)
            y_offset += mh
            
        y_offset = border_width+mh/3
        x_offset = border_width + 2*RaspiRenderer.HEADER_BORDER_WIDTH \
                                         + 2*RaspiRenderer.HEADER_PIN_SIZE \
                                         + 2*RaspiRenderer.HEADER_BORDER_PADDING \
                                         + 2*RaspiRenderer.HEADER_BORDER_WIDTH \
                                         +   RaspiRenderer.HEADER_PIN_SPACING \
                                         +   RaspiRenderer.HEADER_SWITCH_DISTANCE
        for dock in sorted(dock_renderers, key=lambda dr: int(dr.get_dock().get_name().replace("GPIO ",""))):
            
            dock.draw_dock(cr, sc, alloc.x-border_width, alloc.y+y_offset, alloc.width)
            y_offset += mh
    
        self.draw_header(cr, sc, alloc, border_width)


    def do_get_dock_on_position(self, point, dock_renderers, 
                                border_width, alloc):
        mh = self.switch_height
        y_offset = border_width+mh/3
        for dock in sorted(dock_renderers, key=lambda dr: int(dr.get_dock().get_name().replace("GPIO ",""))):
            dph = dock.get_dockpoint_height()
            if alloc.x+alloc.width-border_width-dph < point.x < alloc.x+alloc.width-border_width \
                    and alloc.y+y_offset < point.y < alloc.y+y_offset+dph:
                return dock.get_dock()
            y_offset += mh
        return None

    def do_get_dock_position(self, dock, dock_renderers, border_width, alloc):
        mh = self.switch_height
        y_offset = border_width+mh/3
        for idock in sorted(dock_renderers, key=lambda dr: int(dr.get_dock().get_name().replace("GPIO ",""))):
            if idock.get_dock() == dock:
                dph = idock.get_dockpoint_height()
                return True, alloc.x+alloc.width-border_width - (dph / 2), alloc.y + y_offset + (dph / 2)
            y_offset += mh
        return False , 0 , 0

    def do_is_on_closebutton(self, point, alloc, border_width):
        return False

    def do_is_on_resize_handle(self, point, alloc, border_width):
        return False

    def do_get_min_width(self, dock_renderers, children, border_width):
        mw = 2 * border_width
        switch_w, _ = children[0].get_preferred_width()
        dockwidths = [x.get_min_width() for x in dock_renderers]
        mw += max(*dockwidths)
        mw += RaspiRenderer.SWITCH_DOCK_DISTANCE
        mw += switch_w
        mw += RaspiRenderer.HEADER_SWITCH_DISTANCE
        mw += RaspiRenderer.HEADER_BORDER_WIDTH*2
        mw += RaspiRenderer.HEADER_PIN_SIZE*2
        mw += RaspiRenderer.HEADER_BORDER_PADDING*2
        mw += RaspiRenderer.HEADER_PIN_SPACING
        return abs(mw)

    def do_get_min_height(self, dock_renderers, children, border_width):
        mh = 2 * border_width
        switch_h, _ = children[0].get_preferred_height()
        dockheights = reduce(lambda x,y:x+y,
                        [max(x.get_min_height(), switch_h) for x in dock_renderers]
        )
        return mh + max(dockheights,self._get_header_height())

    def do_update_name_layout(self, name):
        return

class RaspiOutRenderer(GtkFlow.NodeRenderer):
    def __init__(self):
        pass

    def draw_node(self, context):
        return

    def get_dock_on_position(self, point):
        return None

    def get_dock_position(self, dock):
        return (0,0)

    def is_on_closebutton(self, point):
        return False

    def is_on_resize_handle(self, point):
        return False

    def get_min_width(self):
        return 0

    def get_min_height(self):
        return 0

    def update_name_layout(self):
        return
        
