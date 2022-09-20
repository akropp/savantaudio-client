# Savant Audio Switch Client

[![image](https://img.shields.io/pypi/v/savantaudio-client.svg)](https://pypi.org/project/savantaudio-client/)

The savantaudio-client package allows users to download the contents of this [GiHub repository](https://github.com/akropp/savantaudio-client),  containing a client library to control Savant Audio Switches such as the SSA-3220/SSA-3220D.

## Installing

Install and update using [pip](https://pip.pypa.io/en/stable/quickstart/):

```bash
pip3 install savantaudio-client
```

Or you can clone this repo using:
```bash
    git clone https://github.com/akropp/savantaudio-client.git
```


## Usage

The client is based on asyncio, so all calls must be made in the context of an event loop.  A basic example which connects to a switch device and fetches all of the inputs/outputs is as follows:

```python
import logging
import asyncio
import savantaudio.client

logging.basicConfig(handlers=[logging.StreamHandler()], encoding='utf-8', level=logging.INFO)
savantaudio.client._LOGGER.setLevel(logging.DEBUG)
switch = savantaudio.client.Switch(host='192.168.1.216', port=8085)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(switch.refresh())
print(str(switch))
loop.run_until_complete(switch.link(11, 8))
loop.run_until_complete(switch.output(11).set_volume(-20))
print(str(switch.output(11)))
loop.run_until_complete(switch.unlink(11))
print(str(switch.output(11)))
```
