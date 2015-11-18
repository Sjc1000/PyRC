#!/usr/bin/env python3


def run(c, *data):
    data = ' '.join(data)
    ServerList = c['MainWindow'].ui_plugins['ServerList']
    server = ServerList.active_server
    ServerList.servers[server]['connection'].send(data)
    return None