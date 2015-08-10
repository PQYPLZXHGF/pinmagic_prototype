from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GtkFlow

import pinmagik.nodes

from pinmagik.nodes.source import Source

from pinmagik.raspi import RaspiContext, RaspiInNode, RaspiOutNode

# Placeholder function for gettext
def _(string):
    return string

try:
    import RPi.GPIO as GPIO
    IS_REAL_RASPI = True
except ImportError:
    IS_REAL_RASPI = False

PD_FIELD_ID = 0
PD_FIELD_NAME = 1
PD_FIELD_HUMAN_NAME = 2
PROJECT_TYPES = {
    "raspi" :      (0x01, "raspi",      _("Raspberry Pi Model A/B")),
    "raspi_plus" : (0x02, "raspi_plus", _("Raspberry Pi Model A+/B+")),
}

class Project(object):
    def __init__(self, typ):
        self._type = typ
        self._nodes = []

    def get_node_by_id(id_):
        for node in self._nodes:
            if id(node) == id_:
                return node
        return None

    def get_nodes(self):
        return self._nodes

    def get_type(self):
        return self._type

class PinMagic(object):
    NODE_INDEX = {}
    INSTANCE = None
    @staticmethod
    def get_node_classes():
        ret = []
        for x in dir(pinmagik.nodes):
            if not x.startswith("_") and x not in pinmagik.nodes.EXCLUDES:
                exec("ret.append(pinmagik.nodes.%s)"%(x,))
        return ret

    @classmethod
    def build_node_index(cls):
        ret = []
        for x in dir(pinmagik.nodes):
            if not x.startswith("_") and x not in pinmagik.nodes.EXCLUDES:
                exec("cls.NODE_INDEX[pinmagik.nodes.%s.ID] = pinmagik.nodes.%s"%(x,x))

    @classmethod
    def S(cls):
        if cls.INSTANCE is None:
            cls.INSTANCE = PinMagic()
        return cls.INSTANCE

    def __init__(self):
        Gtk.init([])

        PinMagic.build_node_index()

        self._current_project = None

        self.headerbar = Gtk.HeaderBar.new()
        self.headerbar.set_title("PinMagic")
        self.headerbar.set_subtitle("untitled")

        self.nodeview = GtkFlow.NodeView.new()
        self.nodeview.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.nodeview.connect("drag-data-received", self.on_new_node)
        self.nodeview.drag_dest_add_text_targets()

        self.builder = Gtk.Builder.new()
        self.builder.add_from_file("main.ui")
        window = self.builder.get_object("window")
        self.scrollarea = self.builder.get_object("scrolledwindow")
        self.nodestree = self.builder.get_object("nodestreeview")
        box = self.builder.get_object("box")
        revealer = self.builder.get_object("info_revealer")
        revealer.set_reveal_child(False)
        box.pack_start(self.headerbar, False, True, 0)
        box.reorder_child(self.headerbar,0)
        self.scrollarea.add_with_viewport(self.nodeview)

        crt = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Toolbox"), crt, text=0)
        self.nodestree.append_column(col)
        self.nodestree.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, [],
                                                Gdk.DragAction.COPY)
        self.nodestree.connect("drag-data-get", self.on_drag_toolbox)
        self.nodestree.drag_source_add_text_targets()

        self.export = Gtk.Button.new_from_icon_name("weather-fog", Gtk.IconSize.BUTTON)
        self.headerbar.pack_end(self.export)

        self.new = Gtk.MenuButton.new()
        self.new.set_popup(self._build_new_menu())
        self.new.set_image(Gtk.Image.new_from_icon_name("document-new", Gtk.IconSize.BUTTON))
        self.headerbar.pack_start(self.new)

        self.live = None
        if IS_REAL_RASPI:
            self.live = Gtk.Button.new_from_icon_name("media-playback-start", Gtk.IconSize.BUTTON)
            self.headerbar.pack_end(self.live)

        window.show_all()
        window.connect("destroy", self.quit)

        self.update_ui()

        PinMagic.get_node_classes()

        Gtk.main()

    def on_drag_toolbox(self, widget, darg_context, data, info, time):
        selected_path = self.nodestree.get_selection().get_selected_rows()[1][0]
        if len(selected_path) < 2:
            return
        m = self.nodestree.get_model()
        treeiter = m.get_iter(selected_path)
        data.set_text("node_"+str(m.get_value(treeiter,1)),-1)

    def on_new_node(self, widget, drag_context, x, y, data, info, time):
        txt = data.get_text()
        if txt is None or not txt.startswith("node_"):
            return

        node_cls_id = int(txt.replace("node_","",1))
        if not node_cls_id in PinMagic.NODE_INDEX:
            return
        node_cls = PinMagic.NODE_INDEX[node_cls_id]
        if node_cls is None:
            return

        new_node = node_cls()
        if new_node.childwidget:
            self.nodeview.add_with_child(new_node, new_node.childwidget)
        else:
            self.nodeview.add_node(new_node)
        #x_offset = self.nodeview.get_hadjustment().get_value()
        #y_offset = self.nodeview.get_vadjustment().get_value()
        self.nodeview.set_node_position(new_node, x, y)
        self.nodeview.set_show_types(False)

    def _build_new_model(self):
        if self._current_project:
            store = Gtk.TreeStore.new([GObject.TYPE_STRING,GObject.TYPE_INT])
            categories = {}
            for node in PinMagic.get_node_classes():
                if not pinmagik.nodes.supports(
                        node, self._current_project.get_type()[PD_FIELD_NAME]):
                    continue
                if not node.CATEGORY in categories:
                    categories[node.CATEGORY] = store.append(None, (node.CATEGORY,-1))
                store.append(categories[node.CATEGORY],(node.HR_NAME,node.ID))
        else:
            store = None
        self.nodestree.set_model(store)
        

    def _build_new_menu(self):
        menu = Gtk.Menu.new()
        for descriptor in PROJECT_TYPES.values():
            i = Gtk.MenuItem.new_with_label(descriptor[PD_FIELD_HUMAN_NAME])
            i.connect("activate", self.new_project, descriptor[PD_FIELD_NAME])
            menu.add(i)
        menu.show_all()
        return menu 
        
    def update_ui(self):
        has_project = self._current_project is not None
        self.export.set_sensitive(has_project)
        self.scrollarea.set_sensitive(has_project)
        self.nodeview.set_sensitive(has_project)
        if self.live:
            self.live.set_sensitive(has_project)
            self.live.set_visible(self._current_project.get_type()[PD_FIELDNMAE] == "raspi")
        self._build_new_model()

    def _clear_current_project(self):
        if self._current_project:
            for node in self._current_project.get_nodes():
                self.nodeview.remove(node)

    def new_project(self, widget=None, data=None):
        self._clear_current_project()
        self._current_project = Project(PROJECT_TYPES[data])
        self.update_ui()

        rc = RaspiContext(RaspiContext.REV_2)
        rin = RaspiInNode(rc)
        rin.add_to_nodeview(self.nodeview)
        ron = RaspiOutNode(rc)
        ron.add_to_nodeview(self.nodeview)
        self.nodeview.set_node_position(rin, 1, 1)
        self.nodeview.set_node_position(ron, 600, 1)

    def load_project(self):
        self._clear_current_project()
        self.update_ui()

    def quit(self, widget=None, data=None):
        Gtk.main_quit()

    @staticmethod
    def run():
        PinMagic.S()
