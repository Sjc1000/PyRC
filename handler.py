#!/usr/bin/env python3


import threads
import time



class EventHandler():

    def __init__(self, MainWindow, connection):
        self.MainWindow = MainWindow
        self.connection = connection

    def handle(self, data):
        data = data.decode('utf-8')
        data = data.replace('\r\n', '\n')
        for line in data.split('\n'):
            if line == '':
                continue
            print( line )
            words = line.split(' ')
            if hasattr(self, 'on' + words[0]):
                getattr(self, 'on' + words[0])(*words[1:])
            if hasattr(self, 'on' + words[1]) and len(words) > 2:
                getattr(self, 'on' + words[1])(*[words[0]] + words[2:])
            plugins = self.MainWindow.ui_plugins
            for plugin in plugins:
                if hasattr(plugins[plugin], 'on' + words[0]):
                    getattr(plugins[plugin], 'on' + words[0])(self.connection, *words[1:])
                if hasattr(plugins[plugin], 'on' + words[1]) and len(words) > 2:
                    getattr(plugins[plugin], 'on' + words[1])(self.connection, *[words[0]] + words[2:])
        return None

    def onPING(self, server):
        self.connection.send('PONG ' + server)
        return None

    def onNICK(self, host, new_nick):
        if host.split('!')[0][1:] == self.connection.nickname:
            self.connection.nickname = new_nick[1:]
        return None

    def onJOIN(self, host, channel):
        if channel.startswith(':') is True:
            channel = channel[1:]
        if host.split('!')[0][1:] == self.connection.nickname:
            self.MainWindow.global_action('add_channel', self.connection.server, channel)
        return None

    def onPART(self, host, channel):
        if host.split('!')[0][1:] == self.connection.nickname:
            self.MainWindow.global_action('remove_channel', self.connection.server, channel)
        return None