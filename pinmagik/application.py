from gi.repository import Gtk
from gi.repository import GtkFlow

import pinmagik.nodes

class Project(object):
    def __init__(self):
        pass

class RaspiContext(object):
    def __init__(self):
        pass

class PinMagic(object):
    def __init__(self):
        Gtk.init([])
        self.headerbar = Gtk.HeaderBar.new()
        self.headerbar.set_title("PinMagic")
        self.headerbar.set_subtitle("untitled")

        self.nodeview = GtkFlow.NodeView.new()

        self.builder = Gtk.Builder.new()
        self.builder.add_from_file("main.ui")
        window = self.builder.get_object("window")
        scrollarea = self.builder.get_object("scrolledwindow")
        box = self.builder.get_object("box")
        revealer = self.builder.get_object("info_revealer")
        revealer.set_reveal_child(False)
        box.pack_start(self.headerbar, False, True, 0)
        box.reorder_child(self.headerbar,0)
        scrollarea.add(self.nodeview)

        self.export = Gtk.Button.new_from_icon_name("weather-fog", Gtk.IconSize.BUTTON)
        self.headerbar.pack_end(self.export)

        self.live = Gtk.Button.new_from_icon_name("media-playback-start", Gtk.IconSize.BUTTON)
        self.headerbar.pack_end(self.live)

        window.show_all()
        window.connect("destroy", self.quit)

        Gtk.main()

    def quit(self, widget=None, data=None):
        Gtk.main_quit()

    @staticmethod
    def run():
        PinMagic()
