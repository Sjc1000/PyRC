#!/usr/bin/env python3


def run(c, *action):
    ServerList = c['MainWindow'].ui_plugins['ServerList']
    channel = ServerList.active_channel
    server = ServerList.active_server
    connection = ServerList.servers[server]['connection']
    c['MainWindow'].ui_action('ChatBox', 'add_text_to', server, channel, '* {} {}'.format(connection.nickname, ' '.join(action)))
    connection.privmsg(channel, '\x01ACTION ' + ' '.join(action) + '\x01')
    return None