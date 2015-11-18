#!/usr/bin/env python3


def run(c, user, *message):
    if user.startswith('#') is True:
        return None
    ServerList = c['MainWindow'].ui_plugins['ServerList']
    channel = ServerList.active_channel
    server = ServerList.active_server
    connection = ServerList.servers[server]['connection']
    if user not in ServerList.servers[server]['channels']:
        c['MainWindow'].global_action('add_channel', server, user)
        c['MainWindow'].ui_action('UserList', 'add_user', server, user, user)
        c['MainWindow'].ui_action('UserList', 'add_user', server, user, connection.nickname)
    connection.privmsg(user, ' '.join(message))
    c['MainWindow'].ui_action('ChatBox', 'add_text_to', server, user, '{} - {}'.format(connection.nickname, ' '.join(message)))
    c['MainWindow'].global_action('activate_path', server, user)
    return None