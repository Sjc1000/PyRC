#!/usr/bin/env python3


def run(c, user, CTCP_message):
    MainWindow = c['MainWindow']
    connection = MainWindow.servers[MainWindow.active_server]['connection']
    connection.CTCP(user, CTCP_message)
    return None