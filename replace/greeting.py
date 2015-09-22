#!/usr/bin/env python3


import time


def run():
    hour = time.localtime(time.time()).tm_hour
    if hour < 12:
        return 'Morning all.'
    elif hour < 18:
        return 'Afternoon all.'
    elif hour < 24:
        return 'Evening all.'