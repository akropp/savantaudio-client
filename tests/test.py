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