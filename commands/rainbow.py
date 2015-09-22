#!/usr/bin/env python3

import random

def run(c, *text):
    output = ['\x03' + str(random.choice(range(1,15))) + x + '\x03' for x in ' '.join(text)]
    print( output )
    MainWindow = c['MainWindow']
    channel = MainWindow.active_channel
    server = MainWindow.active_server
    connection = MainWindow.servers[server]['connection']
    connection.privmsg(channel, ''.join(output))
    return None