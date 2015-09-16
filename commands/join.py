#!/usr/bin/env python3


def run(c, *channel_list):
    MainWindow = c['MainWindow']
    if MainWindow.active_server not in MainWindow.servers:
        return None
    for channel in channel_list:
        channel = channel.lower()
        MainWindow.add_channel(MainWindow.active_server, channel)
        MainWindow.servers[MainWindow.active_server]['connection'].send('JOIN ' + channel)
    return None