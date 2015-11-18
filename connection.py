#!/usr/bin/env python3


import socket
import time
import threads


def timestamp():
    t = time.localtime(time.time())
    return '{:0>2}:{:0>2}:{:0>2}'.format(t.tm_hour, t.tm_min, t.tm_sec)


class Connection():

    def __init__(self, network, port=6667, nickname='PyRC_User',
                 username='PyRC_User', host='PyRC',
                 realname='PyRC - Python IRC Chat', password=None):
        self.server = network
        self.port = int(port)
        self.nickname = nickname
        self.username = username
        self.host = host
        self.realname = realname
        self.password = password
        self.event_handler = None
        self.MainWindow = None

    @threads.asthread(True)
    def connect(self):
        if self.event_handler is None:
            return None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for i in range(10):
            try:
                self.socket.connect((self.server, self.port))
            except TimeoutError:
                break
            except Exception as error_message:
                break
            else:
                self.identify()
                self.main_loop()
                break
        return None

    def send(self, data):
        try:
            print( data )
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
                self.event_handler.handle(prev + recv)
                prev = b''
            elif b'\r\n' in recv:
                for line in recv.split(b'\r'):
                    if line.endswith(b'\n'):
                        self.event_handler.handle(prev + line)
                        prev = b''
                    else:
                        prev += line
            else:
                prev += recv
        return None

    def privmsg(self, channel, text):
        replace = {'\\x03': '\x03', '\\x02': '\x02', '\\x01': '\x01', '\\x0f': '\x0f', '\\italics': '\x1D',
                   '\\bold': '\x02', '\\color': '\x03', '\\i': '\x1D', '\\b': '\x02', '\\c': '\x03'}
        for check in replace:
            text = text.replace(check, replace[check])
        self.send('PRIVMSG {} :{}'.format(channel, text))
        return None

    def CTCP(self, user, message):
        self.send('PRIVMSG {} :\x01{}\x01'.format(user, message))
        return None

    def rejoin(self):
        time.sleep(10)
        self.connect()
        return None