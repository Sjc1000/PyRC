#!/usr/bin/env python3


from gi.repository import Gtk
import html.entities
import re


class MOTD():

    servers = {}
    default_text = 'Welcome to PyRC. Thank you for using my software. :)'
    active_server = None
    active_channel = None

    def __init__(self, MainWindow):
        self.MainWindow = MainWindow
        self.position = [2, 0, 6, 1]

    def prebuild(self):
        self.MainWindow.ui_plugins['ChatBox'].position[1] += 1
        self.MainWindow.ui_plugins['ChatBox'].position[3] -= 1
        return None

    def build(self):
        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                      Gtk.PolicyType.NEVER)
        self.text = Gtk.Label()
        self.text.name = 'MOTD'
        self.text.set_text(self.default_text)
        self.scroll_window.add(self.text)
        self.MainWindow.grid.attach(self.scroll_window, *self.position)
        return None

    def add_server(self, server):
        self.servers[server] = {'channels': {}}
        return None

    def add_channel(self, server, channel):
        self.servers[server]['channels'][channel] = self.default_text
        return None

    def on332(self, connection, host, nickname, channel, *MOTD):
        print( MOTD )
        self.servers[connection.server]['channels'][channel] = ' '.join(MOTD)[1:]
        if channel == self.active_channel:
            self.activate_path(connection.server, channel)
        return None

    def activate_path(self, server, channel, clicked=None):
        self.active_server = server
        self.active_channel = channel
        if channel == None:
            self.text.set_text(self.default_text)
            return None
        if channel not in self.servers[server]['channels']:
            self.text.set_markup(self.default_text)
            return None
        text = self.servers[server]['channels'][channel]
        matches = re.findall(r'((?:https?:\/\/|www.)(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b(?:[-a-zA-Z0-9@:%_\+.~#?&//=]*))', text)
        if matches:
            for match in matches:
                text = text.replace(match, '<a href="{0}">{0}</a>'.format(match))
            self.text.set_markup(self.html_escape(text))
            return None
        self.text.set_text(text)
        return None

    def html_escape(self, text):
        codes = {'&': 'amp;'}
        for item in codes:
            text = text.replace(item, '&' + codes[item])
        print( text )
        return text