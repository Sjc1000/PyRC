#!/usr/bin/env python3


from gi.repository import Gtk, GLib, Pango, Gdk
import webbrowser
import re
import threading
import time


def timestamp():
    t = time.localtime(time.time())
    return '[{:0>2}:{:0>2}:{:0>2}]'.format(t.tm_hour, t.tm_min, t.tm_sec)


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


class ChatBox():

    timestamp = True
    active_channel = None
    active_server = None
    force_scroll_window = False
    servers = {}
    tags = {}

    def __init__(self, MainWindow):
        self.MainWindow = MainWindow
        self.position = [2, 0, 6, 9]

    def build(self):
        self.prev_scroll_val = None
        self.scroll_window = Gtk.ScrolledWindow()
        self.box = Gtk.TextView()
        self.box.name = 'ChatBox'
        self.box.set_editable(False)
        self.box.set_hexpand(True)
        self.box.set_vexpand(True)
        self.box.set_wrap_mode(Gtk.WrapMode.WORD)
        self.scroll_window.add(self.box)
        self.MainWindow.grid.attach(self.scroll_window, *self.position)
        self.box.connect('size-allocate', self.auto_scroll)

    def start_theme(self, theme_name):
        buffer = self.box.get_buffer()
        tag_table = buffer.get_tag_table()
        for tag in self.MainWindow.theme['ChatBox']['tags']:
            if tag_table.lookup(tag) is not None:
                tag_table.remove(self.tags[tag])
            converted = {}
            for item in self.MainWindow.theme['ChatBox']['tags'][tag]:
                value = self.MainWindow.theme['ChatBox']['tags'][tag][item]
                if isinstance(value, dict) is False and isinstance(value, bool) is False and value.startswith('!'):
                    value = eval(value[1:])
                converted[item] = value
            if 'connect' in converted:
                for event in converted['connect']:
                #event = converted['connect']
                    function = converted['connect'][event]
                    del converted['connect']
                    self.tags[tag] = buffer.create_tag(tag, **converted)
                    self.tags[tag].connect(event, getattr(self, function))
            else:
                self.tags[tag] = buffer.create_tag(tag, **converted)
        return None

    def url_clicked(self, tag, textview, event, itr):
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

    #@IdleCall()
    def auto_scroll(self, *args):
        vadj = self.scroll_window.get_vadjustment()
        if vadj.get_value() == self.prev_scroll_val or self.force_scroll_window == True:
            vadj.set_value(vadj.get_upper() - vadj.get_page_size())
        if vadj.get_value() != vadj.get_upper() - vadj.get_page_size() and self.force_scroll_window:
            self.auto_scroll()
        self.prev_scroll_val = vadj.get_upper() - vadj.get_page_size()
        self.force_scroll_window = False
        return None

    @IdleCall()
    def clear_and_add(self, text, end='\n'):
        self.clear_text()
        self.add_text(text, end)
        return None

    @IdleCall()
    def add_text(self, text, end='\n'):
        buff = self.box.get_buffer()
        if isinstance(text, list):
            text = '\n'.join(text)
        buff.insert(buff.get_end_iter(), text+end)
        self.colorize()
        return None

    @IdleCall()
    def clear_text(self):
        buff = self.box.get_buffer()
        buff.delete(buff.get_start_iter(), buff.get_end_iter())
        return None

    def on001(self, connection, *data):
        self.add_text_to(connection.server, None, ' '.join(data[2:])[1:])
        return None

    def on002(self, connection, *data):
        self.add_text_to(connection.server, None, ' '.join(data[2:])[1:])
        return None

    def on003(self, connection, *data):
        self.add_text_to(connection.server, None, ' '.join(data[2:])[1:])
        return None

    def on004(self, connection, *data):
        self.add_text_to(connection.server, None, ' '.join(data[2:]))
        return None

    def on005(self, connection, *data):
        self.add_text_to(connection.server, None, ' '.join(data[2:])[1:])
        return None

    def on251(self, connection, *data):
        self.add_text_to(connection.server, None, ' '.join(data[2:])[1:])
        return None

    def on002(self, connection, *data):
        self.add_text_to(connection.server, None, ' '.join(data[2:])[1:])
        return None

    def add_server(self, server):
        self.servers[server] = {'channels': {}, 'text': ['Created server "' + server + '"']}
        return None

    def add_channel(self, server, channel):
        self.servers[server]['channels'][channel] = {'text': [], 'users': {}}
        return None

    @asthread(True)
    def activate_path(self, server, channel, clicked=False):
        if channel != None and server != self.active_server and clicked is False:
            return None
        if channel == None:
            text = self.servers[server]['text']
        else:
            text = self.servers[server]['channels'][channel]['text']
        self.clear_text()
        self.active_server = server
        self.active_channel = channel
        self.add_text('\n'.join(text))
        self.force_scroll_window = True
        return None

    def add_text_to(self, server, channel=None, data=None):
        if self.timestamp is True:
            data = timestamp() + ' ' + data
        if channel == None:
            self.servers[server]['text'].append(data)
        else:
            self.servers[server]['channels'][channel]['text'].append(data)
        if server == self.active_server and channel == self.active_channel:
            self.add_text(data)
            self.colorize()
        return None

    @IdleCall()
    def colorize(self):
        if len(self.tags) == 0:
            return None
        matches = self.MainWindow.theme['ChatBox']['matches']
        buffer = self.box.get_buffer()
        start = buffer.get_start_iter()
        end = buffer.get_end_iter()
        text = buffer.get_text(start, end, True)
        counter = 0
        for line in text.split('\n'):
            for match in matches:
                try:
                    result = re.finditer(match, line, re.S)
                except TypeError:
                    print( 'Error' )
                    continue
                for item in result:
                    for tag in matches[match]:
                        try:
                            start = buffer.get_iter_at_offset(item.start(int(tag)) + counter)
                            end = buffer.get_iter_at_offset(item.end(int(tag)) + counter)
                            for c in matches[match][tag].split(','):
                                color = self.tags[c]
                                buffer.apply_tag(color, start, end)
                        except IndexError:
                            continue
            counter += len(line)+1
        return None

    def onNICK(self, connection, host, new_nickname):
        new_nickname = new_nickname[1:]
        for channel in self.servers[connection.server]['channels']:
            for nickname in self.servers[connection.server]['channels'][channel]['users']:
                if nickname == host.split('!')[0][1:]:
                    self.add_text_to(connection.server, channel, '{} is now known as {}'.format(nickname, new_nickname))
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
            self.servers[connection.server]['channels'][channel]['users'][user] = status
        return None

    def onPRIVMSG(self, connection, host, channel, *message):
        if channel == connection.nickname:
            channel = host.split('!')[0][1:]
        if channel not in self.servers[connection.server]['channels']:
            self.add_channel(connection.server, channel)
        if '\x01ACTION' in message[0]:
            message = ' '.join(message[1:]).replace('\x01', '')
            self.add_text_to(connection.server, channel, '* {} {}'.format(host.split('!')[0][1:], message))
        else:
            self.add_text_to(connection.server, channel, '{} - {}'.format(host.split('!')[0][1:], ' '.join(message)[1:]))
        return None

    def onJOIN(self, connection, host, channel):
        channel = channel.strip().replace(':', '')
        if connection.nickname == host.split('!')[0][1:]:
            self.add_channel(connection.server, channel)
        else:
            self.servers[connection.server]['channels'][channel]['users'][host.split('!')[0][1:]] = None
        self.add_text_to(connection.server, channel, '{} ({}) has joined {}'.format(host.split('!')[0][1:], host[1:], channel))
        if connection.server == self.active_server and connection.nickname == host.split('!')[0][1:]:
            self.activate_path(connection.server, channel)
        return None

    def onPART(self, connection, host, channel, *quit_message):
        channel = channel.strip()
        self.add_text_to(connection.server, channel, '{} ({}) has left {} ({})'.format(host.split('!')[0][1:], host[1:], channel, ' '.join(quit_message)[1:]))
        return None

    def onQUIT(self, connection, host, *quit_message):
        for channel in self.servers[connection.server]['channels']:
            if host.split('!')[0][1:] in self.servers[connection.server]['channels'][channel]['users']:
                self.add_text_to(connection.server, channel, '{} ({}) has quit {} ({})'.format(host.split('!')[0][1:], host[1:], channel, ' '.join(quit_message)[1:]))
        return None