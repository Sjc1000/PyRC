#!/usr/bin/env python3


def run(c, server, nickname='PyRC', port=6667, password=None):
    if server in c['MainWindow'].servers:
        return None
    c['MainWindow'].global_action('add_server', server)
    c['MainWindow'].ui_plugins['ServerList'].servers[server]['connection'] = c['Connection'](server, port, nickname, password=password)
    handler = c['Handler']
    c['MainWindow'].ui_plugins['ServerList'].servers[server]['connection'].MainWindow = c['MainWindow']
    c['MainWindow'].ui_plugins['ServerList'].servers[server]['connection'].event_handler = handler.EventHandler( c['MainWindow'], c['MainWindow'].ui_plugins['ServerList'].servers[server]['connection'])
    c['MainWindow'].ui_plugins['ServerList'].servers[server]['connection'].connect()
    c['MainWindow'].global_action('activate_path', server, None)
    c['MainWindow'].global_action('change_nickname', server, nickname)
    return None