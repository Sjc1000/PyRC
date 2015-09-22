#!/usr/bin/env python3


import time


def timestamp():
    t = time.localtime(time.time())
    return '{:0>2}:{:0>2}:{:0>2}'.format(t.tm_hour, t.tm_min, t.tm_sec)


def run(c, username, *junk):
    MainWindow = c['MainWindow']
    MainWindow.servers[MainWindow.active_server]['connection'].send('PRIVMSG ' + MainWindow.active_channel + ' :\x01ACTION slaps ' + username + ' with a large trout!\x01')
    MainWindow.add_text(MainWindow.active_server, MainWindow.active_channel, '{} * {} slaps {} with a large trout!'.format(timestamp(), MainWindow.servers[MainWindow.active_server]['connection'].nickname, username))
    return None