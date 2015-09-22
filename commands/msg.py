#!/usr/bin/env python3


def run(c, user, *message):
    MainWindow = c['MainWindow']
    if user.lower() not in MainWindow.servers[MainWindow.active_server]['channels']:
        MainWindow.add_channel(MainWindow.active_server, user.lower())
    MainWindow.servers[MainWindow.active_server]['connection'].privmsg(user.lower(), ' '.join(message))
    return None