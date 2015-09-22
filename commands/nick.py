#!/usr/bin/env python3


def run(c, newnickname):
    MainWindow = c['MainWindow']
    MainWindow.servers[MainWindow.active_server]['connection'].send('NICK ' + newnickname)
    return None