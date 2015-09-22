#!/usr/bin/env python3


from gi.repository import Gtk, GObject, GLib, Pango, Gdk
import imp
import os
import re
import time
import webbrowser
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
    nick_replace_suffix = ''

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
        usertext = self.make_username()
        grid.attach(inputbox, 2, 11, 12, 1)
        grid.attach(server, 0, 0, 2, 11)
        grid.attach(chat, 2, 1, 10, 10)
        grid.attach(users, 12, 0, 2, 11)
        grid.attach(usertext, 1, 11, 1, 1)
        self.add(grid)
        self.create_tags()

    def create_tags(self):
        buff = self.chatbox.get_buffer()
        self.bold = buff.create_tag('bold', weight=Pango.Weight.BOLD)
        self.italic = buff.create_tag('italic', style=Pango.Style.ITALIC)
        self.underline = buff.create_tag('underline', underline=Pango.Underline.SINGLE)
        self.red = buff.create_tag('red', foreground='#DD0000')
        self.blue = buff.create_tag('blue', foreground='#0000AA')
        self.green = buff.create_tag('green', foreground='#007700')
        self.purple = buff.create_tag('purple', foreground='#770077')
        self.orange = buff.create_tag('orange', foreground='#ff5400')
        self.white = buff.create_tag('white', foreground='#FFFFFF')
        self.black = buff.create_tag('black', foreground='#000000')
        self.brown = buff.create_tag('brown', foreground='#770000')
        self.yellow = buff.create_tag('yellow', foreground='#EEEE00')
        self.lgreen = buff.create_tag('lgreen', foreground='#00EE00')
        self.cyan = buff.create_tag('cyan', foreground='#00AAAA')
        self.lcyan = buff.create_tag('lcyan', foreground='#00EEEE')
        self.lblue = buff.create_tag('lblue', foreground='#0000EE')
        self.pink = buff.create_tag('pink', foreground='#EE00EE')
        self.grey = buff.create_tag('grey', foreground='#888888')
        self.lgrey = buff.create_tag('lgrey', foreground='#EEEEEE')

        self.red_background = buff.create_tag('red_background', background='#DD0000')
        self.blue_background = buff.create_tag('blue_background', background='#0000AA')
        self.green_background = buff.create_tag('green_background', background='#007700')
        self.purple_background = buff.create_tag('purple_background', background='#770077')
        self.orange_background = buff.create_tag('orange_background', background='#ff5400')
        self.white_background = buff.create_tag('white_background', background='#FFFFFF')
        self.black_background = buff.create_tag('black_background', background='#000000')
        self.brown_background = buff.create_tag('brown_background', background='#770000')
        self.yellow_background = buff.create_tag('yellow_background', background='#EEEE00')
        self.lgreen_background = buff.create_tag('lgreen_background', background='#00EE00')
        self.cyan_background = buff.create_tag('cyan_background', background='#00AAAA')
        self.lcyan_background = buff.create_tag('lcyan_background', background='#00EEEE')
        self.lblue_background = buff.create_tag('lblue_background', background='#0000EE')
        self.pink_background = buff.create_tag('pink_background', background='#EE00EE')
        self.grey_background = buff.create_tag('grey_background', background='#888888')
        self.lgrey_background = buff.create_tag('lgrey_background', background='#EEEEEE')

        self.hyperlink = buff.create_tag('hyperlink', foreground='#0000AA', underline=Pango.Underline.SINGLE)
        self.timestamp = buff.create_tag('timestamp', foreground='#770077', weight=Pango.Weight.BOLD)
        self.hyperlink.connect('event', self.link_clicked)
        self.hidden = buff.create_tag('hidden', invisible=True)

        self.colors = [self.white, self.black, self.blue, self.green,
                       self.red, self.brown, self.purple, self.orange,
                       self.yellow, self.lgreen, self.cyan, self.lcyan,
                       self.lblue, self.pink, self.grey, self.lgrey]
        self.colors_background = [self.white_background, self.black_background, self.blue_background, self.green_background,
                       self.red_background, self.brown_background, self.purple_background, self.orange_background,
                       self.yellow_background, self.lgreen_background, self.cyan_background, self.lcyan_background,
                       self.lblue_background, self.pink_background, self.grey_background, self.lgrey_background]
        return None

    def make_grid(self):
        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(10)
        return grid

    def make_username(self):
        self.usertext = Gtk.Label()
        return self.usertext

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
                with open('tabreplace.json', 'r') as afile:
                    autoreplace = json.loads(afile.read())
                if any(word[1:] in command for command in self.commands) and word.startswith('/'):
                    for command in self.commands:
                        if word[1:] in command:
                            match = '/' + command
                elif word in autoreplace:
                    print( word )
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
                    match = match_list[0] + self.nick_replace_suffix
                if match == None:
                    return True
                output = text.split(' ')[:-1] + [match]
                self.repl = word
                self.set_inputbox_text(' '.join(output))
            return True
        if key.get_keycode() == (True, 65):
            text = self.inputbox.get_text()
            word = text.split(' ')[-1]
            with open('autoreplace.json', 'r') as afile:
                autoreplace = json.loads(afile.read())
            if word in autoreplace:
                print( len(text.split(' ')))
                if len(text.split(' ')) <= 1:
                    output = [autoreplace[word]] + ['']
                else:
                    output = text.split(' ')[:-1] + [autoreplace[word]] + ['']
                self.set_inputbox_text(' '.join(output))
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
        self.server_list = Gtk.TreeStore(str, str)
        self.server_view = Gtk.TreeView(self.server_list)
        self.server_view.set_activate_on_single_click(True)
        self.server_view.set_hexpand(True)
        self.server_view.connect('row-activated', self.serverlist_clicked)
        text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Servers', text, text=0, foreground=1)
        self.server_view.append_column(column)
        scroll_window.add(self.server_view)
        return scroll_window

    @threads.asthread(True)
    def serverlist_clicked(self, TreeView, TreePath, TreeViewColumn):
        model = TreeView.get_model()
        itr = model.get_iter(TreePath)
        string = model.get_value(itr, 0)
        
        if ':' in str(TreePath):
            self.active_channel = string
            parent = model.iter_parent(itr)
            self.active_server = model.get_value(parent, 0)
            self.change_treeview_color(self.active_server, self.active_channel, 'black')
        else:
            self.active_server = string
            self.active_channel = None
            self.change_treeview_color(self.active_server, self.active_channel, 'black')
        self.redraw_chat()
        self.scroll_chatbox()
        self.redraw_userlist()
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
            itr = self.server_list.append(None, [server_name, 'black'])
            self.servers[server_name] = {'iter': itr, 'channels': {}, 'text': [], 'connection': None}
        else:
            self.activate_path(server_name)
        return None

    def add_channel(self, server_name, channel):
        itr = self.servers[server_name]['iter']
        ch_iter = self.server_list.append(itr, [channel, 'black'])
        self.servers[server_name]['channels'][channel] = {'iter': ch_iter, 'text': [], 'users': {}}
        return None

    def remove_channel(self, server_name, channel):
        itr = self.servers[server_name]['iter']
        ch_iter = self.servers[server_name]['channels'][channel]['iter']
        del self.servers[server_name]['channels'][channel]
        self.server_list.remove(ch_iter)
        return None

    @_IdleCall()
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
            self.color_textview()
        return None

    @_IdleCall()
    def change_treeview_color(self, server, channel=None, color='black'):
        if channel == self.active_channel and server == self.active_server and color != 'black':
            return None
        if channel == None:
            itr = self.servers[server]['iter']
        else:
            itr = self.servers[server]['channels'][channel]['iter']
        self.server_list[itr][1] = color
        return None

    @_IdleCall()
    def append_chat(self, text):
        cbuffer = self.chatbox.get_buffer()
        endpos = cbuffer.get_end_iter()
        cbuffer.insert(endpos, '\n'+text, len('\n'+text))
        self.color_textview()
        return None

    def add_user(self, server, channel, username, user_modes=None):
        if username == None or username == '':
            return None
        if server not in self.servers:
            self.add_server(server)
            self.add_channel(server, channel)
        mode = None
        pfx = self.servers[server]['supported']['PREFIX'][0]
        modes = pfx.split(')')[0][1:]
        prefixes = pfx.split(')')[1]
        if username[0] in prefixes:
            index = prefixes.index(username[0])
            mode = [modes[index]]
            username = username[1:]
        elif user_modes is not None:
            mode = user_modes
            username = username
        self.servers[server]['channels'][channel]['users'][username] = mode
        if self.active_server == server and self.active_channel == channel:
            self.redraw_userlist()
        return None

    def remove_user(self, server, channel, user):
        del self.servers[server]['channels'][channel]['users'][user]
        if self.active_server == server and self.active_channel == channel:
            self.redraw_userlist()
        return None


    @threads.asthread(True)
    def redraw_userlist(self):
        self.draw_userlist()
        return None

    @_IdleCall()
    def draw_userlist(self):
        self.user_list.clear()
        if self.active_channel == None:
            return None
        users = self.servers[self.active_server]['channels'][self.active_channel]['users']
        ulist = ((x,users[x]) for x in users)
        sort = sorted(ulist, key=self.sort_userlist)
        for tup in sort:
            user = tup[0]
            if user not in users:
                self.add_user(self.active_server, self.active_server, user)
            mode = '' if tup[1] is None else tup[1]
            ms = self.servers[self.active_server]['supported']['PREFIX'][0]
            modes = ms.split(')')[0][1:]
            prefixes = ms.split(')')[1]
            output = ''
            for m in mode:
                output += prefixes[modes.index(m)]
            
            u_iter = self.user_list.insert(-1)
            self.user_list.set_value(u_iter, 0, output + user)
        return None

    def sort_userlist(self, user):
        username = user[0]
        output = ord(username[0].lower())
        mode = None if user[1] is None else user[1][0]
        if mode == 'o':
            output = output * 1
        elif mode == 'v':
            output = output * 27
        else:
            output = output * 27 * 27
        return output

    @threads.asthread(True)
    def redraw_chat(self):
        self.draw_chat()
        return None

    @_IdleCall()
    def draw_chat(self):
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
        cbuffer.insert(cstart, '\n'.join(text))
        self.color_textview()
        if self.active_server != None and self.active_channel == None:
            inputbox_text = 'Try using /join #channel to join a channel!'
        else:
            inputbox_text = ''
        self.inputbox.set_placeholder_text(inputbox_text)
        return None

    @threads.asthread(True)
    def color_textview(self):
        self.parse_colors()
        self.run_matches()
        return None

    @_IdleCall()
    def run_matches(self):
        matches = {'^\d+:\d+:\d+\s(.*?)\s\((.*?)\)\shas joined\s(.*)$': {'0': self.green, '2': self.italic, '1': self.bold, '3': self.bold},
                   '^\d+:\d+:\d+\s(.*?|\[.*?\])\s(?:.*?sets mode\s(.*?)\son (\w+))?': {'1': self.bold, '2': self.italic, '3': self.bold},
                   '^\d+:\d+:\d+ (\w+ \((.*?)\) has (?:quit|left) (.*?) ?.*?$)': {'1': self.orange, '2': self.italic, '3': self.bold},
                   '^\d+:\d+:\d+.*?(?:\]|\*\s\w+)\s((.*?{}.*?$))'.format(self.servers[self.active_server]['connection'].nickname): {'1': self.red, '2': self.bold},
                   r'((https?:\/\/|www.)(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))': {'1': self.hyperlink},
                   '^(\d+:\d+:\d+)\s': {'1': self.timestamp}}
        buff = self.chatbox.get_buffer()
        start_iter = buff.get_start_iter()
        end_iter = buff.get_end_iter()
        text = buff.get_text(start_iter, end_iter, True)
        counter = 0
        for line in text.split('\n'):
            for regex in matches:
                match = re.search(regex, line)
                if match:
                    for item in matches[regex]:
                        start = match.start(int(item))
                        end = match.end(int(item))
                        match_start = buff.get_iter_at_offset(start + counter)
                        match_end = buff.get_iter_at_offset(end + counter)
                        buff.apply_tag(matches[regex][item], match_start, match_end)
            counter += len(line)+1
        return None

    @_IdleCall()
    def parse_colors(self):
        buff = self.chatbox.get_buffer()
        start = buff.get_start_iter()
        end = buff.get_end_iter()
        text = buff.get_text(start, end, True)
        matches = re.finditer('(\\x03\0?(\d+(?:\,\0?\d+)?))(.*?)(\\x03|\n|$|\\x0f)', text)

        for match in matches:
            if match:
                start = buff.get_iter_at_offset(match.start(1))
                end = buff.get_iter_at_offset(match.end(1))
                buff.apply_tag(self.hidden, start, end)

                start = buff.get_iter_at_offset(match.start(4))
                end = buff.get_iter_at_offset(match.end(4))
                buff.apply_tag(self.hidden, start, end)

                color = match.group(2)
                if ',' in color:
                    fg = int(color.split(',')[0])
                    bg = int(color.split(',')[1])
                else:
                    fg = int(color)
                    bg = 0
                if fg in range(len(self.colors)):
                    tstart = buff.get_iter_at_offset(match.start(3))
                    tend = buff.get_iter_at_offset(match.end(3))
                    buff.apply_tag(self.colors[fg], tstart, tend)
                if bg in range(len(self.colors)):
                    tstart = buff.get_iter_at_offset(match.start(3))
                    tend = buff.get_iter_at_offset(match.end(3))
                    buff.apply_tag(self.colors_background[bg], tstart, tend)

        bold = re.finditer('(\\x02)(.*?)(\\x02|\n|$|\\x0f)', text)
        for match in bold:
            if match:
                textstart = buff.get_iter_at_offset(match.start(2))
                textend = buff.get_iter_at_offset(match.end(2))
                lstart = buff.get_iter_at_offset(match.start(1))
                lend = buff.get_iter_at_offset(match.end(1))
                rstart = buff.get_iter_at_offset(match.start(3))
                rend = buff.get_iter_at_offset(match.end(3))

                buff.apply_tag(self.bold, textstart, textend)
                buff.apply_tag(self.hidden, lstart, lend)
                buff.apply_tag(self.hidden, rstart, rend)
        return None

    def link_clicked(self, tag, textview, event, itr):
        if event.get_event_type() == Gdk.EventType.BUTTON_PRESS:
            buff = textview.get_buffer()
            left = buff.get_text(buff.get_start_iter(), itr, True)
            right = buff.get_text(itr, buff.get_end_iter(), True)
            link = re.search(r'((https?:\/\/|www.)(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))', left.split(' ')[-1] + right.split(' ')[0])
            if link:
                link = link.group(1)
                webbrowser.open(link)
            return True
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