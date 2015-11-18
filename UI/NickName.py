#!/usr/bin/env python3


from gi.repository import Gtk, Pango


class NickName():

    servers = {}
    active_server = None
    active_channel = None

    def __init__(self, MainWindow):
        self.MainWindow = MainWindow
        self.position = [0, 9, 1, 1]

    def prebuild(self):
        self.MainWindow.ui_plugins['ServerList'].position[3] -= 1
        return None

    def build(self):
        self.text = Gtk.Label()
        self.text.set_text('')
        self.MainWindow.grid.attach(self.text, *self.position)
        return None

    def add_server(self, server):
        self.servers[server] = ''
        return None

    def change_nickname(self, server, new_nickname):
        self.servers[server] = new_nickname
        self.text.set_markup('<span weight="ultrabold">' + new_nickname + '</span>')
        return None

    def activate_path(self, server, channel, clicked=False):
        self.active_channel = channel
        self.active_server = server
        self.change_nickname(server, self.servers[server])
        return None