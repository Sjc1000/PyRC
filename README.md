# PyRC
PyRC - A python IRC client built in python and can be modded with python.
It is still in development, quite early stages of it too, so not everything works and not everything is there.
If you do use it, expect only base functionality, I am a solo dev and I work on it as much as I can.

## Supports

- Multiple Servers
- Custom commands
- Tab completion of nicknames. It first checks if the string you entered is in a nickname, then it attempts to find the closest match. ( More details below )
- Tab replace. Kind of like auto replace, but happens when you press tab.

## Tab Completion

I tried something a little different for the tab completion.
At first it acts like a normal one, for example if you type

Hello usern

and there is a user called username, it will select them.
if you press tab again, itl select someone called usernone etc etc.

If it doesn't find a match this way, itl try to find the closest match.

If you enter stph and there is a user called Stephen it will select them.
If you enter stvn and there is a user called Stephen and Steven it will select Steven.

## Requirements

- Python3
- GTK3 ( sudo apt-get install python3-gi )
