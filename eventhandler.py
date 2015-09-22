#!/usr/bin/env python3


import threads
import time


def timestamp():
    t = time.localtime(time.time())
    return '{:0>2}:{:0>2}:{:0>2}'.format(t.tm_hour, t.tm_min, t.tm_sec)


class _EventHandler():
    def __init__(self, MainWindow):
        self.MainWindow = MainWindow
        self.show_raw = True

    def handle(self, connection, data):
        data = data.decode('utf-8').replace('\r\n', '\n')
        for line in data.split('\n'):
            if line == '':
                continue
            if self.show_raw is True:
                self.MainWindow.add_text(connection.server, 'raw', line)
            split = line.split(' ')
            if hasattr(self, 'on' + split[0]):
                getattr(self, 'on' + split[0])(connection, *split[1:])
            if len(split) < 2:
                continue
            if hasattr(self, 'on' + split[1]):
                getattr(self, 'on' + split[1])(connection, *[split[0]] + split[2:])
        return None

    def onPING(self, connection, host):
        connection.send('PONG ' + host)
        return None

    def on001(self, connection, *data):
        self.MainWindow.add_text(connection.server, None, ' '.join(data[2:])[1:])
        return None

    def on002(self, connection, *data):
        self.MainWindow.add_text(connection.server, None, ' '.join(data[2:])[1:])
        return None

    def on003(self, connection, *data):
        self.MainWindow.add_text(connection.server, None, ' '.join(data[2:])[1:])
        return None

    def on004(self, connection, *data):
        server_name = data[2]
        self.MainWindow.servers[connection.server]['server_name'] = server_name
        return None

    def on005(self, connection, host, nickname, *supported):
        self.MainWindow.add_text(connection.server, None, ' '.join(supported))
        if 'supported' not in self.MainWindow.servers[connection.server]:
            self.MainWindow.servers[connection.server]['supported'] = {}
        if 'commands' not in self.MainWindow.servers[connection.server]:
            self.MainWindow.servers[connection.server]['commands'] = []
        for command in supported:
            if command.startswith(':'):
                break
            if '=' in command:
                split = command.split('=')
                command = split[0]
                params = [x for x in split[1].split(',')]
                self.MainWindow.servers[connection.server]['supported'][command] = params
            else:
                self.MainWindow.servers[connection.server]['commands'].append(command)
        return None

    def on251(self, connection, host, nickname, *servers):
        self.MainWindow.add_text(connection.server, None, ' '.join(servers)[1:])
        return None

    def on252(self, connection, host, nickname, ops, *text):
        self.MainWindow.add_text(connection.server, None, 'There are '
                                 + str(ops) + ' IRC Operators online.')
        return None

    # TODO: MOTD stuffs here.

    def onPRIVMSG(self, connection, host, channel, *message):
        if channel == connection.nickname:
            channel = host.split('!')[0][1:]
        channel = channel.lower()
        if channel not in self.MainWindow.servers[connection.server]['channels']:
            self.MainWindow.add_channel(connection.server, channel)
        if message[0].startswith(':\x01ACTION'):
            self.MainWindow.add_text(connection.server, channel, '{} * {} {}'.format(timestamp(), host.split('!')[0][1:], ' '.join(message[1:]).replace('\x01', '')))
        else:
            self.MainWindow.add_text(connection.server, channel, timestamp() + ' [' + host.split('!')[0][1:] + '] ' + ' '.join(message)[1:])
        if any(connection.nickname in x for x in message):
            self.MainWindow.change_treeview_color(connection.server, channel, 'blue')
        else:
            self.MainWindow.change_treeview_color(connection.server, channel, 'red')
        return None

    def onJOIN(self, connection, host, channel):
        channel = channel.lower()
        if channel.startswith(':'):
            channel = channel[1:]
        if channel not in self.MainWindow.servers[connection.server]['channels']:
            self.MainWindow.add_channel(connection.server, channel)
        if host.split('!')[0][1:] == connection.nickname:
            self.MainWindow.activate_path(connection.server, channel)
        else:
            self.MainWindow.add_user(connection.server, channel, host.split('!')[0][1:])
        self.MainWindow.add_text(connection.server, channel, '{} {} ({}) has joined {}'.format(timestamp(), host.split('!')[0][1:], host[1:],channel))
        self.MainWindow.change_treeview_color(connection.server, channel, '#AA00AA')
        return None

    def onPART(self, connection, host, channel, *message):
        if channel.startswith(':'):
            channel = channel[1:]
        channel = channel.lower()
        if host.split('!')[0][1:].lower() == connection.nickname.lower():
            #self.MainWindow.remove_channel(connection.server, channel)
            return None
        else:
            self.MainWindow.add_text(connection.server, channel, '{} {} ({}) has left {}'.format(timestamp(), host.split('!')[0][1:], host[1:], channel))
            self.MainWindow.remove_user(connection.server, channel, host.split('!')[0][1:])
        self.MainWindow.change_treeview_color(connection.server, channel, '#AA00AA')
        return None

    def on353(self, connection, host, nickname, eq, channel, *userlist):
        channel = channel.lower()
        userlist = [userlist[0][1:]] + [x for x in userlist[1:]]
        for user in userlist:
            self.MainWindow.add_user(connection.server, channel, user)
        return None

    def onQUIT(self, connection, host, *quit_message):
        nickname = host.split('!')[0][1:]
        channels = self.MainWindow.servers[connection.server]['channels']
        for channel in channels:
            if nickname in channels[channel]['users']:
                self.MainWindow.add_text(connection.server, channel, '{} {}'
                    ' ({}) has quit {} ({})'.format(timestamp(),
                    host.split('!')[0][1:], host[1:],channel,
                    ' '.join(quit_message)))
                self.MainWindow.remove_user(connection.server, channel, nickname)
                self.MainWindow.change_treeview_color(connection.server, channel, '#AA00AA')
        return None

    def onNOTICE(self, connection, host, channel, *message):
        if channel == connection.nickname:
            channel = self.MainWindow.active_channel
        if channel == 'AUTH':
            channel = None
        server = connection.server
        self.MainWindow.add_text(server, channel, '{} -{}- {}'.format(timestamp(), host.split('!')[0][1:], ' '.join(message)[1:]))
        return None

    def onNICK(self, connection, host, newnickname):
        old = host.split('!')[0][1:]
        channels = self.MainWindow.servers[connection.server]['channels']
        for channel in channels:
            print( channel )
            if old in channels[channel]['users']:
                modes = channels[channel]['users'][old]
                print( modes )
                self.MainWindow.remove_user(connection.server, channel, old)
                self.MainWindow.add_user(connection.server, channel, newnickname[1:], modes)
                self.MainWindow.add_text(connection.server, channel, '{} {} is now known as {}'.format(timestamp(), old, newnickname[1:]))
                self.MainWindow.change_treeview_color(connection.server, channel, '#AA00AA')
        if host.split('!')[0][1:] == connection.nickname:
            connection.nickname = newnickname[1:]
        if host.split('!')[0][1:].lower() in self.MainWindow.servers[connection.server]['channels']:
            text = self.MainWindow.servers[connection.server]['channels'][host.split('!')[0][1:].lower()]['text']
            self.MainWindow.remove_channel(connection.server, host.split('!')[0][1:].lower())
            self.MainWindow.add_channel(connection.server, newnickname[1:].lower())
            self.MainWindow.add_text(connection.server, newnickname[1:].lower(), '\n'.join(text))
            if self.MainWindow.active_channel == host.split('!')[0][1:]:
                time.sleep(0.2)
                self.MainWindow.activate_path(connection.server, newnickname[1:].lower())
        return None

    def onMODE(self, connection, setter, channel, mode, user=None):
        channel = channel.lower()
        if user == None:
            user = setter.split('!')[0][1:]
            if mode[0] == '+':
                self.MainWindow.servers[connection.server]['usermode'] = [x for x in mode]
            if mode[0] == '-':
                for x in mode[1:]:
                    self.MainWindow.servers[connection.server]['usermode'].pop(self.MainWindow.servers[connection.server]['usermode'].index(x))
            return None
        users = self.MainWindow.servers[connection.server]['channels'][channel]['users']
        if mode[0] == '-':
            users[user] = [x for x in users[user] if x not in mode]
            if len(users[user]) == 0:
                users[user] = None
        if mode[0] == '+':
            if user in users:
                if users[user] == None:
                    users[user] = []
                users[user] = users[user] + [x for x in mode[1:]]
        if self.MainWindow.active_server == connection.server and self.MainWindow.active_channel == channel:
            self.MainWindow.redraw_userlist()
        self.MainWindow.add_text(connection.server, channel, '{} {} sets mode {} on {}'.format(timestamp(), setter.split('!')[0][1:], mode, user))
        self.MainWindow.change_treeview_color(connection.server, channel, '#AA00AA')
        return None


"""
:card.freenode.net NOTICE * :*** Looking up your hostname...

:card.freenode.net NOTICE * :*** Checking Ident
:card.freenode.net NOTICE * :*** Couldn't look up your hostname

:card.freenode.net NOTICE * :*** No Ident response
:card.freenode.net 001 PyRC_User :Welcome to the freenode Internet Relay Chat Network PyRC_User
:card.freenode.net 002 PyRC_User :Your host is card.freenode.net[38.229.70.22/6667], running version ircd-seven-1.1.3
:card.freenode.net 003 PyRC_User :This server was created Thu Sep 18 2014 at 18:48:25 UTC
:card.freenode.net 004 PyRC_User card.freenode.net ircd-seven-1.1.3 DOQRSZaghilopswz CFILMPQSbcefgijklmnopqrstvz bkloveqjfI
:card.freenode.net 005 PyRC_User CHANTYPES=# EXCEPTS INVEX CHANMODES=eIbq,k,flj,CFLMPQScgimnprstz CHANLIMIT=#:120 PREFIX=(ov)@+ MAXLIST=bqeI:100 MODES=4 NETWORK=freenode KNOCK STATUSMSG=@+ CALLERID=g :are supported by this server
:card.freenode.net 005 PyRC_User CASEMAPPING=rfc1459 CHARSET=ascii NICKLEN=16 CHANNELLEN=50 TOPICLEN=390 ETRACE CPRIVMSG CNOTICE DEAF=D MONITOR=100 FNC TARGMAX=NAMES:1,LIST:1,KICK:1,WHOIS:1,PRIVMSG:4,NOTICE:4,ACCEPT:,MONITOR: :are supported by this server
:card.freenode.net 005 PyRC_User EXTBAN=$,ajrxz WHOX CLIENTVER=3.0 SAFELIST ELIST=CTU :are supported by this server
:card.freenode.net 251 PyRC_User :There are 155 users and 81256 invisible on 26 servers
:card.freenode.net 252 PyRC_User 24 :IRC Operators online
:card.freenode.net 253 PyRC_User 8 :unknown connection(s)
:card.freenode.net 254 PyRC_User 62153 :channels formed
:card.freenode.net 255 PyRC_User :I have 3911 clients and 4 servers
:card.freenode.net 265 PyRC_User 3911 8011 :Current local users 3911, max 8011
:card.freenode.net 266 PyRC_User 81411 101901 :Current global users 81411, max 101901
:card.freenode.net 250 PyRC_User :Highest connection count: 8015 (8011 clients) (5109069 connections received)
:card.freenode.net 375 PyRC_User :- card.freenode.net Message of the Day - 
:card.freenode.net 372 PyRC_User :-  
:card.freenode.net 372 PyRC_User :- Welcome to card.freenode.net in Washington, DC, US, kindly sponsored by
:card.freenode.net 372 PyRC_User :- Team Cymru (http://www.team-cymru.org).
:card.freenode.net 372 PyRC_User :-  
:card.freenode.net 372 PyRC_User :- CARD, ORSON SCOTT [1951-].  Born in Richland, Washington, Card grew up in
:card.freenode.net 372 PyRC_User :- California, Arizona, and Utah.  He lived in Brazil for two years as an
:card.freenode.net 372 PyRC_User :- unpaid missionary for the Mormon Church.  Author of the Ender and Alvin
:card.freenode.net 372 PyRC_User :- Maker books, Card's science fiction and fantasy work is strongly influenced
:card.freenode.net 372 PyRC_User :- by his Mormon cultural background.  The first author to win the Hugo and
:card.freenode.net 372 PyRC_User :- Nebula novel awards two years in a row, Card currently lives in Greensboro,
:card.freenode.net 372 PyRC_User :- North Carolina, US.
:card.freenode.net 372 PyRC_User :-  
:card.freenode.net 372 PyRC_User :-  
:card.freenode.net 372 PyRC_User :- Welcome to freenode - supporting the free and open source
:card.freenode.net 372 PyRC_User :- software communities since 1998.
:card.freenode.net 372 PyRC_User :-  
:card.freenode.net 372 PyRC_User :- By connecting to freenode you indicate that you have read and
:card.freenode.net 372 PyRC_User :- accept our policies as set out on http://www.freenode.net
:card.freenode.net 372 PyRC_User :- freenode runs an open proxy scanner. Please join #freenode for
:card.freenode.net 372 PyRC_User :- any network-related questions or queries, where a number of
:card.freenode.net 372 PyRC_User :- volunteer staff and helpful users will be happy to assist you.
:card.freenode.net 372 PyRC_User :-  
:card.freenode.net 372 PyRC_User :- You can meet us at FOSSCON (http://www.fosscon.org) where we get
:card.freenode.net 372 PyRC_User :- together with like-minded FOSS enthusiasts for talks and
:card.freenode.net 372 PyRC_User :- real-life collaboration.
:card.freenode.net 372 PyRC_User :-  
:card.freenode.net 372 PyRC_User :- We would like to thank Private Internet Access
:card.freenode.net 372 PyRC_User :- (https://www.privateinternetaccess.com/) and the other
:card.freenode.net 372 PyRC_User :- organisations that help keep freenode and our other projects
:card.freenode.net 372 PyRC_User :- running for their sustained support.
:card.freenode.net 372 PyRC_User :-  
:card.freenode.net 372 PyRC_User :- In particular we would like to thank the sponsor
:card.freenode.net 372 PyRC_User :- of this server, details of which can be found above.
:card.freenode.net 372 PyRC_User :-  
:card.freenode.net 376 PyRC_User :End of /MOTD command.
:PyRC_User MODE PyRC_User :+i
"""