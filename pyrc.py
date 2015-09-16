#!/usr/bin/env python3


from gi.repository import Gtk, GObject, GLib
import imp
import os
import time
import json
import difflib
import threads
from eventhandler import _EventHandler
from connections import _Connection


class _IdleCall():
    def __init__(self):
        pass

    def __call__(self, function):
        def run(*args, **kwargs):
            GLib.idle_add(function, *args, **kwargs)
            return None
        return run


class MainWindow(Gtk.Window):

    servers = {}
    commands = {}
    active_server = None
    active_channel = None
    repl = ''

    def __init__(self):
        Gtk.Window.__init__(self, title='PyRC')
        self.set_size_request(400, 200)
        self.connect('delete-event', Gtk.main_quit)
        self.make_ui()
        self.show_all()
        self.command_loader()
        self.reload_loop()
        self.run_startup()

    def command_loader(self):
        files = os.listdir('commands/')
        for f in files:
            if f.endswith('.py') is False:
                continue
            name = f.replace('.py', '')
            self.commands[name] = imp.load_source(name, 'commands/' + f)
        return None

    @threads.asthread(True)
    def run_startup(self):
        time.sleep(2)
        with open('startup.json', 'r') as sfile:
            startup = json.loads(sfile.read())

        for command in startup['commands']:
            self.send_input(command)
        return None

    @threads.asthread(True)
    def reload_loop(self):
        while True:
            files = os.listdir('commands/')
            for f in files:
                if f.endswith('.py') is False:
                    continue
                name = f.replace('.py', '')
                self.commands[name] = imp.load_source(name, 'commands/' + f)
            time.sleep(60)
        return None

    def make_ui(self):
        grid = self.make_grid()
        inputbox = self.make_inputbox()
        server = self.make_serverlist()
        chat = self.make_chatbox()
        users = self.make_userlist()
        grid.attach(inputbox, 2, 11, 12, 1)
        grid.attach(server, 0, 0, 2, 11)
        grid.attach(chat, 2, 1, 10, 10)
        grid.attach(users, 12, 0, 2, 11)
        self.add(grid)
        return None

    def make_grid(self):
        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(10)
        return grid

    def make_chatbox(self):
        scroll_window = Gtk.ScrolledWindow()
        self.chatbox = Gtk.TextView()
        self.chatbox.set_editable(False)
        self.chatbox.set_hexpand(True)
        self.chatbox.set_vexpand(True)
        self.chatbox.set_wrap_mode(Gtk.WrapMode.WORD)
        chatbuffer = self.chatbox.get_buffer()
        self.chatbox_endmark = chatbuffer.create_mark('end', chatbuffer.get_start_iter(), False)
        scroll_window.add(self.chatbox)
        return scroll_window

    def make_userlist(self):
        scroll_window = Gtk.ScrolledWindow()
        self.user_list = Gtk.ListStore(str)
        self.user_view = Gtk.TreeView(self.user_list)
        self.user_view.set_hexpand(True)
        text_render = Gtk.CellRendererText()
        text_column = Gtk.TreeViewColumn('Users', text_render, text=0)
        self.user_view.append_column(text_column)
        scroll_window.add(self.user_view)
        return scroll_window

    def make_inputbox(self):
        self.inputbox = Gtk.Entry()
        self.inputbox.set_placeholder_text('Welcome to PyRC. Use /server servername to get started!')
        self.inputbox.connect('activate', self.inputbox_input)
        self.inputbox.connect('key-press-event', self.input_changed)
        return self.inputbox

    def input_changed(self, entry, key):
        if key.get_keycode() == (True, 23):
            text = self.inputbox.get_text()
            word = text.split(' ')[-1]
            match = None
            if len(word) > 1:
                with open('autoreplace.json', 'r') as afile:
                    autoreplace = json.loads(afile.read())
                if word in autoreplace:
                    match = self.autoreplace(autoreplace, word)
                elif self.active_channel is not None and self.active_server is not None:
                    userlist = [x for x in self.servers[self.active_server]['channels'][self.active_channel]['users']]
                    if word in userlist:
                        userlist = userlist[userlist.index(word)+1:]
                        word = self.repl
                    match_list = [x for x in userlist if word.lower() in x.lower()]
                    if len(match_list) == 0:
                        match_list = difflib.get_close_matches(word, userlist)
                    if len(match_list) == 0:
                        word = [x for x in userlist if self.repl.lower() in x.lower()]
                        return True
                    match = match_list[0]
                if match == None:
                    return True
                output = text.split(' ')[:-1] + [match]
                self.repl = word
                self.set_inputbox_text(' '.join(output))
            return True
        return None

    def autoreplace(self, replacements, word):
        output = replacements[word]
        if output.startswith('func: '):
            function = imp.load_source('replace_func', 'replace/' + output.replace('func: ', '') + '.py')
            return function.run()
        return output

    @_IdleCall()
    def set_inputbox_text(self, text):
        self.inputbox.set_text('')
        self.inputbox.set_text(text)
        self.inputbox.set_position(len(text))
        return None

    def make_serverlist(self):
        scroll_window = Gtk.ScrolledWindow()
        self.server_list = Gtk.TreeStore(str)
        self.server_view = Gtk.TreeView(self.server_list)
        self.server_view.set_activate_on_single_click(True)
        self.server_view.set_hexpand(True)
        self.server_view.connect('row-activated', self.serverlist_clicked)
        text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Servers', text, text=0)
        self.server_view.append_column(column)
        scroll_window.add(self.server_view)
        return scroll_window

    @_IdleCall()
    def serverlist_clicked(self, TreeView, TreePath, TreeViewColumn):
        model = TreeView.get_model()
        itr = model.get_iter(TreePath)
        string = model.get_value(itr, 0)
        
        if ':' in str(TreePath):
            self.active_channel = string
            parent = model.iter_parent(itr)
            self.active_server = model.get_value(parent, 0)
        else:
            self.active_server = string
            self.active_channel = None
        self.redraw_chat()
        self.redraw_userlist()
        self.scroll_chatbox()
        return None

    @_IdleCall()
    def inputbox_input(self, widget):
        text = widget.get_text()
        widget.set_text('')
        self.send_input(text)
        return None

    def send_input(self, text):
        print( text )
        objects = {'MainWindow': self}
        for item in globals():
            if item.startswith('_') and item.startswith('__') is False:
                objects[item] = globals()[item]
        if text.startswith('/'):
            data = text.split(' ')
            command = data[0][1:]
            print( command )
            args = [x for x in data[1:] if x.startswith('--') is False and data[data.index(x)-1].startswith('--') is False]
            kwargs = {x.replace('--', ''):data[data.index(x)+1] for x in data[1:] if x.startswith('--')}
            if command in self.commands:
                self.commands[command].run(objects, *args, **kwargs)
        else:
            if self.active_channel == None:
                return None
            self.servers[self.active_server]['connection'].privmsg(self.active_channel, text)
        return None

    #@_IdleCall()
    def add_server(self, server_name):
        if server_name not in self.servers:
            itr = self.server_list.append(None, [server_name])
            self.servers[server_name] = {'iter': itr, 'channels': {}, 'text': [], 'connection': None}
        else:
            self.activate_path(server_name)
        return None

    #@_IdleCall()
    def add_channel(self, server_name, channel):
        itr = self.servers[server_name]['iter']
        ch_iter = self.server_list.append(itr, [channel])
        self.servers[server_name]['channels'][channel] = {'iter': ch_iter, 'text': [], 'users': {}}
        return None

    @_IdleCall()
    def remove_channel(self, server_name, channel):
        itr = self.servers[server_name]['iter']
        ch_iter = self.servers[server_name]['channels'][channel]['iter']
        del self.servers[server_name]['channels'][channel]
        self.server_list.remove(ch_iter)
        return None

    #@_IdleCall()
    def activate_path(self, server, channel=None):
        if server != self.active_server:
            return None
        if channel is None:
            itr = self.servers[server]['iter']
        elif channel in self.servers[server]['channels']:
            itr = self.servers[server]['channels'][channel]['iter']
        self.active_channel = channel
        self.active_server = server
        self.focus_path(itr)
        return None

    @_IdleCall()
    def focus_path(self, itr):
        path = self.server_list.get_path(itr)
        self.server_view.expand_to_path(path)
        self.server_view.set_cursor(path)
        self.redraw_chat()
        return None

    #@_IdleCall()
    def add_text(self, server, channel=None, text=None):
        if channel == None:
            self.servers[server]['text'].append(text)
        else:
            self.servers[server]['channels'][channel]['text'].append(text)
        if server == self.active_server and channel == self.active_channel:
            self.append_chat(text)
            self.scroll_chatbox()
        return None

    @_IdleCall()
    def append_chat(self, text):
        cbuffer = self.chatbox.get_buffer()
        cbuffer.insert_at_cursor('\n' + text)
        return None

    def add_user(self, server, channel, username):
        if username == None or username == '':
            return None
        mode = None
        prefixes = self.servers[server]['supported']['PREFIX'][0]
        if username[0] in prefixes.split(')')[1]:
            mode = prefixes.split(')')[1][prefixes.split(')')[1].find(username[0])]
            username = username[1:]
        self.servers[server]['channels'][channel]['users'][username] = mode
        if self.active_server == server and self.active_channel == channel:
            self.redraw_userlist()
        return None

    def remove_user(self, server, channel, user):
        del self.servers[server]['channels'][channel]['users'][user]
        if self.active_server == server and self.active_channel == channel:
            self.redraw_userlist()
        return None


    @_IdleCall()
    def redraw_userlist(self):
        self.user_list.clear()
        if self.active_channel == None:
            return None
        users = self.servers[self.active_server]['channels'][self.active_channel]['users']
        for user in dict(users):
            mode = '' if users[user] is None else users[user]
            u_iter = self.user_list.insert(-1)
            self.user_list.set_value(u_iter, 0, mode + user)
        return None

    @_IdleCall()
    def redraw_chat(self):
        server = self.active_server
        channel = self.active_channel
        if channel is None:
            text = self.servers[server]['text']
        else:
            text = self.servers[server]['channels'][channel]['text']
        cbuffer = self.chatbox.get_buffer()
        cstart = cbuffer.get_start_iter()
        cend = cbuffer.get_end_iter()
        cbuffer.delete(cstart, cend)
        cbuffer.insert(cstart, '\n'.join(text), len('\n'.join(text)))
        if self.active_server != None and self.active_channel == None:
            inputbox_text = 'Try using /join #channel to join a channel!'
        else:
            inputbox_text = ''
        self.inputbox.set_placeholder_text(inputbox_text)
        return None

    @threads.asthread(True)
    def scroll_chatbox(self):
        time.sleep(0.3)
        self.auto_scroll()
        return None

    @_IdleCall()
    def auto_scroll(self):
        cbuffer = self.chatbox.get_buffer()
        insert_mark = cbuffer.get_insert()
        cbuffer.place_cursor(cbuffer.get_end_iter())
        self.chatbox.scroll_to_mark(insert_mark, 0.0, False, 0.0, 0.0)
        return None


def main():
    program = MainWindow()
    Gtk.main()
    return None

if __name__ == '__main__':
    main()