#!/usr/bin/env python3


import socket
import time
import threads


def timestamp():
    t = time.localtime(time.time())
    return '{:0>2}:{:0>2}:{:0>2}'.format(t.tm_hour, t.tm_min, t.tm_sec)


class _Connection():

    def __init__(self, network, port=6667, nickname='PyRC_User',
                 username='PyRC_User', host='PyRC',
                 realname='PyRC - Python IRC Chat', password=None):
        self.server = network
        self.port = int(port)
        self.nickname = nickname
        self.username = username
        self.host = host
        self.realname = realname
        self.event_handler = None
        self.password = password
        self.MainWindow = None

    @threads.asthread(True)
    def connect(self):
        if self.event_handler is None:
            self.MainWindow.add_text(self.server, None, 'EventHandler has '
                                     'not been set. Quitting')
            return None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.MainWindow.add_text(self.server, None, 'Trying to connect '
                                 'to ' + self.server)
        for i in range(10):
            self.MainWindow.add_text(self.server, None, 'Attempt ' + str(i))
            try:
                self.socket.connect((self.server, self.port))
            except TimeoutError:
                self.MainWindow.add_text(self.server, None, 'Connection Timed out.')
                break
            except Exception as error_message:
                self.MainWindow.add_text(self.server, None, 'Something went wrong: ' + str(error_message))
                break
            else:
                self.MainWindow.add_text(self.server, None, 'Connected!')
                if 'raw' not in self.MainWindow.servers[self.server]['channels'] and self.event_handler.show_raw is True:
                    self.MainWindow.add_channel(self.server, 'raw')
                self.identify()
                self.main_loop()
                break
        return None

    def send(self, data):
        try:
            self.socket.send(bytes(data + '\r\n', 'utf-8'))
        except BrokenPipeError as Error:
            self.rejoin()
        return None

    def identify(self):
        if self.password is not None:
            self.send('PASS ' + self.password)
        self.send('NICK ' + self.nickname)
        self.send('USER {} {} {} :{}'.format(self.nickname, self.username,
                  self.host, self.realname))
        return None

    def main_loop(self):
        prev = b''
        while True:
            try:
                recv = self.socket.recv(1024)
            except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
                self.rejoin()
                pass
            if recv == '':
                for i in range(10):
                    recv = self.socket.recv(1024)
                    if recv != '':
                        break
                    if i == 9:
                        self.rejoin()
                        continue
            if recv.endswith(b'\r\n'):
                self.event_handler.handle(self, prev + recv)
                prev = b''
            elif b'\r\n' in recv:
                for line in recv.split(b'\r'):
                    if line.endswith(b'\n'):
                        self.event_handler.handle(self, prev + line)
                        prev = b''
                    else:
                        prev += line
            else:
                prev += recv
        return None

    def privmsg(self, channel, text):
        replace = {'\\x03': '\x03', '\\x02': '\x02', '\\x01': '\x01'}
        for check in replace:
            text = text.replace(check, replace[check])
        self.MainWindow.add_text(self.MainWindow.active_server, channel, '{} [{}] {}'.format(timestamp(), self.nickname, text))
        self.send('PRIVMSG {} :{}'.format(channel, text))
        return None

    def CTCP(self, user, message):
        self.MainWindow.add_text(self.server, self.MainWindow.active_channel, '{} -{}- CTCP request {}'.format(timestamp(), user, message))
        self.send('PRIVMSG {} :\x01{}\x01'.format(user, message))
        return None

    def rejoin(self):
        self.MainWindow.add_text(self.server, None, 'Waiting before the '
                                 'reconnect.')
        time.sleep(10)
        self.MainWindow.add_text(self.server, None, 'Reconnecting.')
        self.connect()
        return None