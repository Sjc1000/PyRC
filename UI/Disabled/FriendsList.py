#!/usr/bin/env python3


from gi.repository import Gtk, Gdk
import json


class FriendsList():

    servers = {}
    active_server = None

    def __init__(self, MainWindow):
        self.MainWindow = MainWindow
        self.position = [8, 5, 1, 4]

    def prebuild(self):
        self.MainWindow.ui_plugins['UserList'].position = (8, 0, 1, 5)
        return None

    def build(self):
        self.scroll_window = Gtk.ScrolledWindow()
        self.list = Gtk.ListStore(str, str)
        self.view = Gtk.TreeView(self.list)
        self.view.set_activate_on_single_click(True)
        self.view.set_hexpand(True)
        self.view.connect('row-activated', self.clicked)
        text_render = Gtk.CellRendererText()
        username = Gtk.TreeViewColumn('Friends', text_render, text=0, foreground=1)
        self.view.append_column(username)
        self.scroll_window.add(self.view)
        self.MainWindow.grid.attach(self.scroll_window, *self.position)
        return None

    def clicked(self, TreeView, TreePath, TreeViewColumn):
        print('User list clicked')
        return None

    def add_friend(self, connection, nickname):
        connection.send('MONITOR + ' + nickname)
        self.servers[connection.server]['friends'][nickname] = {'iter': None, 'online': False}
        if connection.server == self.active_server:
            iter = self.list.append([nickname, 'grey'])
            self.servers[connection.server]['friends'][nickname]['iter'] = iter
        return None

    def activate_path(self, server, channel, clicked=False):
        self.active_server = server
        #redraw
        return None

    def on376(self, connection, *junk):
        with open('UI/friends.json', 'r') as ffile:
            friends = json.loads(ffile.read())
        if connection.server not in friends:
            return None
        self.servers[connection.server] = {'friends': {}}
        for nickname in sorted(friends[connection.server]):
            self.add_friend(connection, nickname)
        connection.send('MONITOR s')
        return None

    def on730(self, connection, host, nickname, uhost):
        if nickname == connection.nickname:
            return None
        print( uhost )
        return None