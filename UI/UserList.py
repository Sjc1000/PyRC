#!/usr/bin/env python3


from gi.repository import Gtk, GLib
import threading


class IdleCall():
    def __init__(self):
        pass

    def __call__(self, function):
        def run(*args, **kwargs):
            GLib.idle_add(function, *args, **kwargs)
            return None
        return run


class asthread(object):

    def __init__(self, daemon=False):
        self.daemon = daemon

    def __call__(self, function):
        def inner(*args, **kwargs):
            thread = threading.Thread(target=function, args=args, 
                                      kwargs=kwargs)
            if self.daemon:
                thread.daemon = True
            thread.start()
            return None
        return inner


class UserList():

    servers = {}
    active_server = None
    active_channel = None

    def __init__(self, MainWindow):
        self.MainWindow = MainWindow
        self.position = [8, 0, 1, 9]

    def build(self):
        self.scroll_window = Gtk.ScrolledWindow()
        self.list = Gtk.ListStore(str)
        self.view = Gtk.TreeView(self.list)
        self.view.set_rules_hint(True)
        self.view.set_activate_on_single_click(True)
        self.view.set_hexpand(True)
        #self.view.set_vexpand(True)
        self.view.connect('row-activated', self.clicked)
        text_render = Gtk.CellRendererText()
        username = Gtk.TreeViewColumn('Username', text_render, text=0, foreground=1)
        self.view.append_column(username)
        self.scroll_window.add(self.view)
        self.MainWindow.grid.attach(self.scroll_window, *self.position)
        return None

    def clicked(self, TreeView, TreePath, TreeViewColumn):
        print('User list clicked')
        return None

    @asthread()
    def update(self, server, channel):
        self.redraw(server, channel)
        return None

    @IdleCall()
    def redraw(self, server, channel):
        self.MainWindow.ui_action('InputBox', 'nick_list_clear')
        self.list.clear()
        if channel == None:
            return None
        channel = channel.strip()
        users = self.servers[server]['channels'][channel]
        users = [(x,users[x]) for x in users]
        for index, user in enumerate(users):
            if user[0][0] in self.MainWindow.ui_plugins['ServerList'].servers[server]['prefixes'].values():
                users[index] = (user[0][1:],user[1])
        users_sorted = sorted(users, key=self.sort)
        for user in users_sorted:
            username = user[0]
            if user[1] is not None:
                prefix = self.MainWindow.ui_plugins['ServerList'].servers[server]['prefixes'][user[1]]
            else:
                prefix = ''
            self.list.append([prefix + username])
            self.MainWindow.ui_action('InputBox', 'nick_list_append', username)
        return None

    def on353(self, connection, host, nickname, eq, channel, *userlist):
        ServerList = self.MainWindow.ui_plugins['ServerList']
        for index, user in enumerate(userlist):
            if index == 0:
                user = user[1:]
            if user == '\r' or user == '':
                continue
            user = user.strip()
            prefixes = list(ServerList.servers[connection.server]['prefixes'].values())
            if user[0] in prefixes:
                status = list(ServerList.servers[connection.server]['prefixes'])[prefixes.index(user[0])]
                user = user[1:]
            else:
                status = None
            self.servers[connection.server]['channels'][channel][user] = status
        return None

    def add_server(self, server):
        self.servers[server] = {'channels': {}}
        return None

    def add_channel(self, server, channel):
        self.servers[server]['channels'][channel] = {}
        return None

    def add_user(self, server, channel, username, status=None):
        self.servers[server]['channels'][channel][username] = status
        return None

    def onPRIVMSG(self, connection, host, channel, *message):
        if channel == connection.nickname:
            channel = host.split('!')[0][1:]
        if channel not in self.servers[connection.server]['channels']:
            self.add_channel(connection.server, channel)
            self.servers[connection.server]['channels'][channel][connection.nickname] = None
            self.servers[connection.server]['channels'][channel][channel] = None
        return None

    def onJOIN(self, connection, host, channel):
        channel = channel.strip().replace(':', '')
        if connection.nickname == host.split('!')[0][1:]:
            pass
        else:
            self.servers[connection.server]['channels'][channel][host.split('!')[0][1:]] = None
        if connection.server == self.active_server and channel == self.active_channel:
            self.update(connection.server, channel)
        if connection.server == self.active_server and host.split('!')[0][1:] == connection.nickname:
            self.activate_path(connection.server, channel)
        return None

    def onNICK(self, connection, host, new_nickname):
        new_nickname = new_nickname[1:]
        print( self.servers[connection.server] )
        for channel in self.servers[connection.server]['channels']:
            for nickname in self.servers[connection.server]['channels'][channel]:
                if nickname == host.split('!')[0][1:]:
                    self.servers[connection.server]['channels'][channel][new_nickname] = self.servers[connection.server]['channels'][channel][nickname]
                    del self.servers[connection.server]['channels'][channel][nickname]
            if channel == self.active_channel and connection.server == self.active_server:
                self.redraw(connection.server, channel)
        return None

    def onPART(self, connection, host, channel, *message):
        if connection.nickname == host.split('!')[0][1:]:
            pass
        else:
            for channel in dict(self.servers[connection.server]['channels']):
                if host.split('!')[0][1:] in self.servers[connection.server]['channels'][channel]:
                    del self.servers[connection.server]['channels'][channel][host.split('!')[0][1:]]
        if connection.server == self.active_server and channel == self.active_channel:
            self.redraw(connection.server, channel)
        return None

    def onQUIT(self, connection, host, channel, *message):
        if connection.nickname != host.split('!')[0][1:]:
            for channel in dict(self.servers[connection.server]['channels']):
                if host.split('!')[0][1:] in self.servers[connection.server]['channels'][channel]:
                    del self.servers[connection.server]['channels'][channel][host.split('!')[0][1:]]
        if connection.server == self.active_server and channel == self.active_channel:
            self.redraw(connection.server, channel)
        return None

    def activate_path(self, server, channel, clicked=False):
        self.active_channel = channel
        self.active_server = server
        self.update(server, channel)
        return None

    def sort(self, user):
        username = user[0]
        mode = None if user[1] is None else user[1][0]
        if mode == 'o':
            return '1_' + username
        if mode == 'v':
            return '2_' + username
        return username