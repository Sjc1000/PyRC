#!/usr/bin/env python3


from gi.repository import Gtk, GLib


class IdleCall():
    def __init__(self):
        pass

    def __call__(self, function):
        def run(*args, **kwargs):
            GLib.idle_add(function, *args, **kwargs)
            return None
        return run


class ServerList():

    servers = {}
    active_server = None
    active_channel = None

    def __init__(self, MainWindow):
        self.MainWindow = MainWindow
        self.position = [0, 0, 1, 10]

    def build(self):
        self.scroll_window = Gtk.ScrolledWindow()
        self.list = Gtk.TreeStore(str, str)
        self.view = Gtk.TreeView(self.list)
        self.view.name = 'ServerList'
        self.view.set_activate_on_single_click(True)
        self.view.set_hexpand(True)
        self.view.connect('row-activated', self.clicked)
        text_render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Servers', text_render, text=0, foreground=1)
        self.view.append_column(column)
        self.scroll_window.add(self.view)
        self.MainWindow.grid.attach(self.scroll_window, *self.position)
        return None

    @IdleCall()
    def clicked(self, TreeView, TreePath, TreeViewColumn):
        model = TreeView.get_model()
        iter = model.get_iter(TreePath)
        string = model.get_value(iter, 0)
        if ':' in str(TreePath):
            channel = string
            server = model.get_value(model.iter_parent(iter), 0)
        else:
            channel = None
            server = string
        if server == self.active_server and channel == self.active_channel:
            return None
        self.MainWindow.ui_plugins['ChatBox'].force_scroll_window = True
        self.MainWindow.global_action('activate_path', server, channel, True)
        self.MainWindow.ui_action('InputBox', 'focus')
        return None

    def add_server(self, server_name):
        itr = self.list.append(None, [server_name, None])
        self.servers[server_name] = {'channels': {}, 'iter': itr, 'prefixes': {}}
        return None

    def add_channel(self, server_name, channel_name):
        channel_name = channel_name.strip()
        if server_name in self.servers:
            itr = self.servers[server_name]['iter']
            ch_iter = self.list.append(itr, [channel_name, None])
            self.servers[server_name]['channels'][channel_name] = {
                    'iter': ch_iter, 'users': {}}
        if server_name == self.active_server:
            self.activate_path(server_name, channel_name)
        else:
            path = self.list.get_path(ch_iter)
            self.view.expand_to_path(path)
        return None

    @IdleCall()
    def remove_channel(self, server_name, channel_name):
        self.MainWindow.global_action('activate_path', server_name, None)
        iter = self.servers[server_name]['channels'][channel_name]['iter']
        del self.servers[server_name]['channels'][channel_name]
        self.list.remove(iter)
        return None

    @IdleCall()
    def activate_path(self, server, channel=None, clicked=False):
        self.active_server = server
        if channel == None:
            self.active_channel = None
            iter = self.servers[server]['iter']
            self.list.set_value(iter, 1, None)
        else:
            iter = self.servers[server]['channels'][channel.strip()]['iter']
            self.list.set_value(iter, 1, None)
            self.active_channel = channel.strip()
        path = self.list.get_path(iter)
        self.view.expand_to_path(path)
        self.view.set_cursor(path)
        return None

    @IdleCall()
    def activity(self, server, channel=None):
        if server == self.active_server and channel == self.active_channel:
            return None
        return None

    @IdleCall()
    def onPRIVMSG(self, connection, host, channel, *message):
        if channel == connection.nickname:
            channel = host.split('!')[0][1:]
        if all(channel.lower() != x.lower() for x in self.servers[connection.server]['channels']):
            self.add_channel(connection.server, channel)
        if channel != self.active_channel:
            iter = self.servers[connection.server]['channels'][channel]['iter']
            string = self.list.get_value(iter, 0)
            #color = self.list.get_value(iter, 1)
            print( self.MainWindow.theme['ServerList']['PRIVMSG'] )
            self.list.set_value(iter, 1, self.MainWindow.theme['ServerList']['PRIVMSG'])
        return None

    def on005(self, connection, *data):
        for info in data:
            if info.startswith('PREFIX='):
                prefixes = info.split('=')[1]
                letters = prefixes.split(')')[0][1:]
                symbols = prefixes.split(')')[1]
                for index, letter in enumerate(letters):
                    self.servers[connection.server]['prefixes'][letter] = symbols[index]
        return None

    def onJOIN(self, connection, host, channel):
        channel = channel.strip().replace(':', '')
        if channel != self.active_channel and host.split('!')[0][1:] != connection.nickname:
            self.servers[connection.server]['channels'][channel]['users'][host.split('!')[0][1:]] = None
            iter = self.servers[connection.server]['channels'][channel]['iter']
            string = self.list.get_value(iter, 0)
            color = self.list.get_value(iter, 1)
            if color != None:
                return None
            self.list.set_value(iter, 1, self.MainWindow.theme['ServerList']['JOIN'])
        return None

    def onNICK(self, connection, host, new_nick):
        if connection.nickname == host.split('!')[0][1:]:
            return None
        for channel in self.servers[connection.server]['channels']:
            if user in self.servers[connection.server]['channels'][channel]['users']:
                self.servers[connection.server]['channels'][channel]['users'][new_nick] = None
                del self.servers[connection.server]['channels'][channel]['users'][user]
        return None

    def onQUIT(self, connection, host, *quit_message):
        for channel in self.servers[connection.server]['channels']:
            if host.split('!')[0][1:] in self.servers[connection.server]['channels'][channel]['users']:
                if channel != self.active_channel and host.split('!')[0][1:] != connection.nickname:
                    iter = self.servers[connection.server]['channels'][channel]['iter']
                    string = self.list.get_value(iter, 0)
                    color = self.list.get_value(iter, 1)
                    if color != None:
                        return None
                    self.list.set_value(iter, 1, self.MainWindow.theme['ServerList']['JOIN'])
        return None

    def onPART(self, connection, host, channel, *quit_message):
        channel = channel.strip().replace(':', '')
        if channel != self.active_channel and host.split('!')[0][1:] != connection.nickname:
            iter = self.servers[connection.server]['channels'][channel]['iter']
            del self.servers[connection.server]['channels'][channel]['users'][host.split('!')[0][1:]]
            string = self.list.get_value(iter, 0)
            color = self.list.get_value(iter, 1)
            if color != None:
                return None
            self.list.set_value(iter, 1, self.MainWindow.theme['ServerList']['JOIN'])
        return None