#!/usr/bin/env python3


from gi.repository import Gtk, GObject, GLib, Pango, Gdk
import imp
import os
import json
import time
import connection
import handler
import threads


class IdleCall():
    def __init__(self):
        pass

    def __call__(self, function):
        def run(*args, **kwargs):
            GLib.idle_add(function, *args, **kwargs)
            return None
        return run


class MainWindow(Gtk.Window):

    servers = {}
    commands = {}
    theme = None

    def __init__(self):
        Gtk.Window.__init__(self, title='PyRC')
        self.set_size_request(400, 300)
        self.set_border_width(10)
        self.make_grid()
        self.load_ui()
        self.show_all()
        self.ui_action('ChatBox', 'add_text', 'PyRC starting.')
        self.ui_action('ChatBox', 'add_text', 'Loading commands')
        self.connect('delete-event', Gtk.main_quit)
        self.commands = self.load_commands()
        self.ui_action('ChatBox', 'add_text', 'Running startup commands.')
        self.ui_action('ChatBox', 'add_text', 'Please use /server <server> [nickname] [port] [password] to join. <> are needed. [] are optional.')
        self.run_startup()

    def load_commands(self):
        files = os.listdir('Commands/')
        output = {}
        for f in files:
            if f.endswith('.py') is False:
                continue
            name = f.replace('.py', '')
            output[name] = imp.load_source(name, 'Commands/' + f)
            self.ui_action('InputBox', 'command_list_append', '/' + name)
        return output

    def run_startup(self):
        with open('startup.json', 'r') as sfile:
            data = sfile.read()
            commands = json.loads(data)['commands']
        for command in commands:
            self.send(command)
        return None

    def make_grid(self):
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(10)
        self.grid.set_row_spacing(5)
        self.add(self.grid)
        return None

    def load_ui(self):
        self.ui_plugins = {}
        items = {}
        files = os.listdir('UI/')
        for f in files:
            if '.py' not in f:
                continue
            name = f.replace('.py', '')
            if name.startswith('_'):
                continue
            source = imp.load_source(name, 'UI/' + f)
            self.ui_plugins[name] = getattr(source, name)(self)
        for control in self.ui_plugins:
            if hasattr(self.ui_plugins[control], 'prebuild'):
                getattr(self.ui_plugins[control], 'prebuild')()
        for control in self.ui_plugins:
            self.ui_plugins[control].build()
        for name in self.ui_plugins:
            self.ui_action('ChatBox', 'clear_text')
        return None

    def send(self, data):
        if data.startswith('/'):
            self.run_command(*data[1:].split(' '))
        return None

    def run_command(self, command, *params):
        if command not in self.commands:
            return False
        objects = {'MainWindow': self, 
                   'Connection': connection.Connection,
                   'IdleCall': IdleCall,
                   'Handler': handler}
        p = [x for x in params if x.startswith('--') is False and 
             params[params.index(x)-1].startswith('--') is False]
        o = {x[2:]:params[params.index(x)+1] for x in params if x.startswith('--')}
        self.commands[command].run(objects, *p, **o)
        return None
    
    def ui_action(self, ui_plugin, method, *params):
        if ui_plugin not in self.ui_plugins:
            return False
        try:
            runner = getattr(self.ui_plugins[ui_plugin], method)
            runner(*params)
        except Exception as Error:
            print( Error )
            return False
        return True

    def global_action(self, method, *params):
        for plugin in self.ui_plugins:
            if hasattr(self.ui_plugins[plugin], method):
                getattr(self.ui_plugins[plugin], method)(*params)
        return None


def main():
    window = MainWindow()
    Gtk.main()
    return None


if __name__ == '__main__':
    main()