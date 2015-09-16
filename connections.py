#!/usr/bin/env 


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
                self.MainWindow.add_text(self.server, None, 'Connection timed out.')
                continue
            except OSError as error_message:
                message = str(error_message)
                message = message[message.find(']')+1:]
                self.MainWindow.add_text(self.server, None, 'Error:' + message)
                return False
            except Exception as error_message:
                self.MainWindow.add_text(self.server, None, 'Something went wrong: ' + str(error_message))
                return False
            else:
                self.MainWindow.add_text(self.server, None, 'Connected!')
                if 'raw' not in self.MainWindow.servers[self.server]['channels'] and self.event_handler.show_raw is True:
                    self.MainWindow.add_channel(self.server, 'raw')
                self.identify()
                self.main_loop()
                return True
        self.MainWindow.add_text(self.server, None, 'Could not connect to the server.')
        return False

    def send(self, data):
        try:
            self.socket.send(bytes(data + '\r\n', 'utf-8'))
        except BrokenPipeError:
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
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
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
        self.MainWindow.add_text(self.MainWindow.active_server, self.MainWindow.active_channel, '{} [{}] {}'.format(timestamp(), self.nickname, text))
        self.send('PRIVMSG {} :{}'.format(channel, text))
        return None

    def rejoin(self):
        self.MainWindow.add_text(self.server, None, 'Waiting before the '
                                 'reconnect.')
        time.sleep(10)
        self.MainWindow.add_text(self.server, None, 'Reconnecting.')
        connected = self.connect()
        return None