from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import GtkFlow

import pinmagik.nodes

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

    def get_nodes(self):
        return self._nodes

    def get_type(self):
        return self._type

class RaspiContext(object):
    def __init__(self):
        pass

class PinMagic(object):
    @staticmethod
    def get_node_classes():
        ret = []
        for x in dir(pinmagik.nodes):
            if not x.startswith("_") and x not in pinmagik.nodes.EXCLUDES:
                exec("ret.append(pinmagik.nodes.%s)"%(x,))
        return ret


    def __init__(self):
        Gtk.init([])

        self._current_project = None

        self.headerbar = Gtk.HeaderBar.new()
        self.headerbar.set_title("PinMagic")
        self.headerbar.set_subtitle("untitled")

        self.nodeview = GtkFlow.NodeView.new()

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
        self.scrollarea.add(self.nodeview)

        crt = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn("Toolbox", crt, text=0)
        self.nodestree.append_column(col)
        #self.nodestree.insert_column_with_attributes(1, "foobar", crt)

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

    def load_project(self):
        self._clear_current_project()
        self.update_ui()

    def quit(self, widget=None, data=None):
        Gtk.main_quit()

    @staticmethod
    def run():
        PinMagic()
