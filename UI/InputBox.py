#!/usr/bin/env python3


from gi.repository import Gtk
import json
import difflib
import time


def timestamp():
    t = time.localtime(time.time())
    return '[{:0>2}:{:0>2}:{:0>2}]'.format(t.tm_hour, t.tm_min, t.tm_sec)


class InputBox():

    commands = []
    nicks = []
    prefix = None
    possible = []

    def __init__(self, MainWindow):
        self.MainWindow = MainWindow
        self.position = [2, 9, 7, 1]

    def build(self):
        self.input = Gtk.Entry()
        self.input.name = 'InputBox'
        self.input.connect('activate', self.activate)
        self.input.connect('key-press-event', self.key_press)
        self.MainWindow.grid.attach(self.input, *self.position)
        return None

    def focus(self):
        self.input.grab_focus()
        return None

    def activate(self, Entry):
        text = Entry.get_text()
        replace = {'\\b': '\x02', '\\c': '\x03', '\\i': '\x1C', '\\u': '\x1F', '\\r': '\x16'}
        for r in replace:
            text = text.replace(r, replace[r])
        print( text )
        Entry.set_text('')
        if text.startswith('/'):
            self.MainWindow.run_command(*text[1:].split(' '))
        else:
            server = self.MainWindow.ui_plugins['ServerList'].active_server
            channel = self.MainWindow.ui_plugins['ServerList'].active_channel
            if channel == None:
                return None
            ServerList = self.MainWindow.ui_plugins['ServerList']
            ServerList.servers[server]['connection'].privmsg(channel, text)
            display_text = '{} - {}'.format(ServerList.servers[server]['connection'].nickname, text)
            self.MainWindow.ui_action('ChatBox', 'add_text_to', server, channel, display_text)
        return None

    def key_press(self, Entry, Key):
        if Key.get_keycode() == (True, 23):
            text = Entry.get_text()
            prefix = text.split(' ')[-1]
            if len(self.possible) == 0:
                if text.startswith(prefix) and prefix.startswith('/'):
                    self.possible = list(self.commands)
                else:
                    self.possible = list(self.nicks)         
            if self.prefix == None:
                self.prefix = prefix
            self.possible = [x for x in self.possible if x.lower().startswith(self.prefix.lower())]
            for i, x in enumerate(self.possible):
                if self.prefix.lower() in x.lower():
                    words = text.split(' ')[:-1] + [x]
                    Entry.set_text('')
                    Entry.set_text(' '.join(words))
                    Entry.set_position(-1)
                    del self.possible[i]
                    break
            return True
        if Key.get_keycode() == (True, 108) or Key.get_keycode() == (True, 64):
            text = Entry.get_text()
            prefix = text.split(' ')[-1]
            with open('UI/tabreplace.json', 'r') as tfile:
                replacements = json.loads(tfile.read())
            if prefix in replacements:
                Entry.set_text('')
                Entry.set_text(' '.join(text.split(' ')[:-1] + [replacements[prefix]]))
                Entry.set_position(-1)
                return True
            return True
        self.possible = []
        self.prefix = None
        return None

    def command_list_append(self, command):
        self.commands.append(command)
        return None

    def nick_list_clear(self):
        self.nicks = []
        return None

    def nick_list_append(self, nick):
        self.nicks.append(nick)
        return None