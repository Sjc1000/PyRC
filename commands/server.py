#!/usr/bin/env python3


def run(c, server, port=6667, password=None, nickname='PyRC_User', username='PyRC_User',
        host='PyRC', realname='PyRC - Python IRC Chat'):
    print('testing')
    MainWindow = c['MainWindow']
    if server in MainWindow.servers:
        self.activate_path(server)
        return None
    MainWindow.add_server(server)
    MainWindow.activate_path(server)
    EventHandler = c['_EventHandler']
    events = EventHandler(MainWindow)
    Connection = c['_Connection']
    con = Connection(server, port, nickname, username, host, realname, password)
    con.event_handler = events
    con.MainWindow = MainWindow
    MainWindow.servers[server]['connection'] = con
    con.connect()
    return None