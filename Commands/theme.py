#!/usr/bin/env python3


import os
import json
from gi.repository import Gdk, Gtk


def run(c, theme):
    directory = os.path.realpath(__file__).split('/')
    themes = os.listdir('/'.join(directory[:-2]) + '/Themes/')
    try:
        with open('/'.join(directory[:-2]) + '/Themes/' + theme + '.json') as tfile:
            c['MainWindow'].theme = json.loads(tfile.read())
    except OSError:
        return None 
    provider = Gtk.CssProvider()
    provider.load_from_path('/'.join(directory[:-2]) + '/Themes/' + theme + '.css')
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    c['MainWindow'].global_action('start_theme', theme)
    c['MainWindow'].ui_action('ChatBox', 'colorize')
    return None