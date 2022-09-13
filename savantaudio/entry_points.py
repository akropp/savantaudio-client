"""
savantaudio.entry_points.py
~~~~~~~~~~~~~~~~~~~~~~

This module contains the entry-point functions for the savantaudio module,
that are referenced in setup.py.
"""

from os import remove
from sys import argv
import sys
import re

import asyncio
import client

def print_links(switch):
    print("Links:")
    for output, input in switch.links.items():
        print(f'{switch.input(input)} => {switch.output(output)}')

def main() -> None:
    """Main package entry point.

    Delegates to other functions based on user input.
    """

    try:
        user_cmd = argv[1]
        if user_cmd == 'install':
            pass
        elif user_cmd == 'dump':
            switch = client.Switch(host=argv[2], port=argv[3])
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(switch.connect())
            print(str(switch))
            for input in switch.inputs:
                print(str(input))
            for output in switch.outputs:
                print(str(output))
            print_links(switch)
        elif user_cmd == 'link':
            switch = client.Switch(host=argv[2], port=argv[3])
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(switch.connect())
            loop.run_until_complete(switch.link(int(argv[4]), int(argv[5])))
            print_links(switch)
        elif user_cmd == 'unlink':
            switch = client.Switch(host=argv[2], port=argv[3])
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(switch.connect())
            loop.run_until_complete(switch.unlink(int(argv[4]), int(argv[5]) if len(argv) > 5 else None))
            print_links(switch)
        elif user_cmd == 'set-volume':
            switch = client.Switch(host=argv[2], port=argv[3])
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(switch.connect())
            loop.run_until_complete(switch.output(int(argv[4])).set_volume(int(argv[5])))
            print(str(switch.output(int(argv[4]))))
        elif user_cmd == 'get-volume':
            switch = client.Switch(host=argv[2], port=argv[3])
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(switch.connect())
            print(str(switch.output(int(argv[4])).volume))
        else:
            RuntimeError('please supply a command for savantaudio - e.g. install.')
    except IndexError:
        RuntimeError('please supply a command for savantaudio - e.g. install.')
    return None

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
