#!/usr/bin/env python3


def run(c, channels):
    server = c['MainWindow'].ui_plugins['ServerList'].active_server
    connection = c['MainWindow'].ui_plugins['ServerList'].servers[server]['connection']
    if isinstance(channels, str):
        channels = [channels]
    for channel in channels:
        if channel.startswith('#') is False:
            channel = '#' + channel
        channel = channel.replace('\n', '').replace('\r', '')
        connection.send('PART ' + channel.strip())
    return None