#!/usr/bin/env python3


def run(c, window):
    MainWindow = c['MainWindow']
    Connection = MainWindow.servers[MainWindow.active_server]['connection']
    Connection.send('PART ' + window)
    MainWindow.remove_channel(MainWindow.active_server, window)
    return None