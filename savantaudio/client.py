"""
savantaudio.client.py
~~~~~~~~~~~~~~~~

Client class to interact with Savant Audio switch
"""

import abc
import asyncio
from dataclasses import dataclass
from genericpath import exists
from typing import Dict, Optional, Sequence, Tuple, TypeVar
from enum import Enum
from xmlrpc.client import Boolean
import re
import logging
import datetime

_LOGGER = logging.getLogger(__name__)

class Connection:
    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port
        self._writer = None
    
    async def connect(self):
        if self._writer is None:
            _LOGGER.debug(f'Opening Connection to {self._host}:{self._port}')
            self._reader, self._writer = await asyncio.open_connection(self._host, self._port)
            self._ts = datetime.datetime.now()

    def reader(self):
        return self._reader
    
    @property
    def writer(self):
        return self._writer
    
    async def send(self, command: str) -> str:
        lock = asyncio.Lock()
        async with lock:
            while True:
                try:
                    if self._writer is None:
                        await self.connect()
                    self._ts = datetime.datetime.now()
                    self._writer.write(command.encode("ASCII") + b"\r\n")
                    await self._writer.drain()
                    data = await self._reader.readline()
                    response = data.decode().strip()
                    if len(response) > 0: 
                        yield response
                    else:
                        _LOGGER.debug(f'Failed to get response to {command}. Retrying')
                        await self.close()
                        continue
                    while True:
                        data = await self._reader.readline()
                        response = data.decode().strip()
                        if len(response) > 0: 
                            yield response
                        else:
                            return
                except ConnectionResetError as cre:
                    _LOGGER.debug(f'Connection reset: {cre}')
                    await self.close()
                except Exception as ex:
                    _LOGGER.exception(f'Connection got exception: {ex}', exc_info=ex)
                    await self.close()
                    raise
    
    def check(self):
        return self._writer.is_closing()
    
    async def close(self):
        if self._writer is not None:
            _LOGGER.debug(f'Closing Connection to {self._host}:{self._port}')
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except:
                pass #ignore
            self._writer = None


class Input:
    def __init__(self, switch, number: int, name: str):
        self._switch = switch
        self._number = number
        self._name = name
        self._coaxial = True
        self._trim = 0
        self._valid = False
    
    @property
    def number(self):
        return self._number
    
    @property
    def name(self):
        return self._name
    
    @property
    def coaxial(self):
        return self._coaxial
    
    @property
    def valid(self):
        return self._valid
    
    @property
    def trim(self):
        return self._trim
    
    def __str__(self):
        return f'Input_{self._number}{{{"Coaxial" if self._coaxial else "TOSLINK"}, trim={self._trim}dB}}'
       
    async def updated(self):
        _LOGGER.info(f'Output {self._number} Updated: {self}')
        await self._switch._updated("updated", self)

    async def parse(self, key: str, value: str):
        if key == 'trim':
            if self._trim != int(value[:-2]):
                self._trim = int(value[:-2])
                await self.updated()
            self._valid = True
        elif key == 'conf':
            if self._coaxial != (value == 'coaxial'):
                self._coaxial = value == 'coaxial'
                await self.updated()
        return True
        
    async def set_trim(self, trim: int):
        await self._switch.send_command(f'ainput-trim-set{self._number}:{trim}')
        pass
    
    async def set_coaxial(self, coax: bool):
        await self._switch.send_command(f'ainput-conf-set{self._number}:{"coaxial" if coax else "toslink"}')
        pass

    async def refresh(self):
        await self._switch.send_command(f'ainput-trim-get{self._number}')
        await self._switch.send_command(f'ainput-conf-get{self._number}')
        

class Output:
    def __init__(self, switch, number: int, name: str):
        self._switch = switch
        self._number = number
        self._name = name
        self._stereo = True
        self._passthru = False
        self._volume = 0
        self._mute = False
        self._delay = [0, 0]
        self._valid = False
    
    @property
    def number(self) -> int:
        return self._number
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def mute(self) -> bool:
        return self._mute
    
    @property
    def stereo(self) -> bool:
        return self._stereo
    
    @property
    def passthru(self) -> bool:
        return self._passthru
    
    @property
    def volume(self) -> int:
        return self._volume
    
    @property
    def delay(self) -> tuple:
        return self._delay
      
    def __str__(self):
        return f'Output_{self._number}{{{"Stereo" if self._stereo else "Mono"}, {"Passthru" if self._passthru else "Processed"}, volume={self._volume}dB, delay={self._delay[0]}/{self._delay[1]}ms}}'
   
    async def updated(self):
        _LOGGER.info(f'Output {self._number} Updated: {self}')
        await self._switch._updated("updated", self)

    async def parse(self, key: str, value: str):
        _LOGGER.debug(f"Output.parse({key} => {value}")
        if key == 'vol':
            self._volume = int(value[:-2])
            self._valid = True
        elif key == 'mute':
            self._mute = value == 'on'
        elif key == 'conf':
            self._passthru = value == 'passthru'
        elif key == 'mono':
            self._mute = value == 'on'
        elif key == 'delayleft':
            self._delay[0] = int(value[:-2])
        elif key == 'delayright':
            self._delay[1] = int(value[:-2])
        return True

    async def refresh(self):
        await self._switch.send_command(f'aoutput-vol-get{self._number}')
        await self._switch.send_command(f'aoutput-conf-get{self._number}')
        await self._switch.send_command(f'aoutput-mute-get{self._number}')
        await self._switch.send_command(f'aoutput-mono-get{self._number}')
        if self._number < 17 and self._switch._model == 'SSA-3220D':
            await self._switch.send_command(f'aoutput-delayboth-get{self._number}')
    
    async def set_volume(self, vol: int):
        await self._switch.send_command(f'aoutput-vol-set{self._number}:{vol}dB')
        pass
    
    async def set_mute(self, mute: bool):
        await self._switch.send_command(f'aoutput-mute-set{self._number}:{"on" if mute else "off"}')
        pass
    
    async def set_mono(self, mono: bool):
        await self._switch.send_command(f'aoutput-mono-set{self._number}:{"on" if mono else "off"}')
        pass
    
    async def set_passthru(self, passthru: bool):
        await self._switch.send_command(f'aoutput-conf-set{self._number}:{"passthru" if passthru else "processed"}')
        pass
    
    async def set_delay(self, left: int, right: int):
        await self._switch.send_command(f'aoutput-delayleft-set{self._number}:{left}')
        await self._switch.send_command(f'aoutput-delayrighy-set{self._number}:{right}')
        pass



class Switch:
    """Class for connecting to switch

    """

    def __init__(self, host: str, port: int, username: str = None, password: str = None, timeout: float = 10.0, model = 'SSA-3220') -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password    
        self._timeout = timeout
        self._inputs = []
        self._outputs = []
        self._links = {} # output -> input
        self._callback = None
        self._connection = Connection(self._host, self._port)
        self._fwrev = None
        self._fpgarev = None
        self._model = model
        if self._model == 'SSA-3220' or self._model == 'SSA-3220D':
            self._ninputs = 32
            self._noutputs = 20
        else:
            raise ValueError(f'Unknown model: {self._model}')
    
    async def connect(self):
        await self.refresh()
    
    def add_callback(self, callback):
        if self._callback is None:
            self._callback = callback
        else:
            cb = self._callback
            async def _cb(event: str, object):
                await cb(event, object)
                await callback(event, object)
            self._callback = _cb
    
    def __str__(self):
        return f"{{ host: {self._host}, port: {self._port}, fwrev: {self._fwrev}, fpga-rev: {self._fpgarev}, inputs: {self._ninputs}, outputs: {self._noutputs}, links: {self._links} }}"
    
    async def _updated(self, event: str, object):
        if self._callback is not None:
            await self._callback(event, object)
    
    async def send_command(self, command: str):
        try:
            _LOGGER.debug(f"send_command: command='{command}'")
            async for reply in self._connection.send(command):
                _LOGGER.debug(f"send_command: reply='{reply}'")
                await self.parse(reply)
        except Exception as ex:
            _LOGGER.exception(f"Got exception {ex}")
            raise

    async def refresh_link(self, output: int):
        await self.send_command(f'switch-get{output}')

    async def get_link(self, output: int):
        await self.refresh_link(output)
        if output in self._links:
            return self._links[output]
        else:
            return None

    async def refresh(self):
        async for reply in self._connection.send('fwrev'):
            m = re.search('fwrevPrimary: (.*)', reply)
            if m:
                self._fwrev = m.group(1)

        async for reply in self._connection.send('fpga-rev'):
            m = re.search('fpga-rev(.*)', reply)
            if m:
                self._fpgarev = m.group(1)

        for c in range(1, self._noutputs):
            await self.refresh_link(c)

        for i in range(1, self._ninputs+1):
            await self.input(i).refresh()

        for o in range(1, self._noutputs+1):
            await self.output(o).refresh()

    def input(self, num: int):
        while len(self._inputs) <= num:
            self._inputs.append(None)
        if self._inputs[num] is None:
            self._inputs[num] = Input(self, num, f'Input {num}')
        return self._inputs[num]

    def output(self, num: int):
        while len(self._outputs) <= num:
            self._outputs.append(None)
        if self._outputs[num] is None:
            self._outputs[num] = Output(self, num, f'Output {num}')
        return self._outputs[num]

    @property
    def inputs(self):
        return [input for input in self._inputs if input is not None]

    @property
    def outputs(self):
        return [output for output in self._outputs if output is not None]

    async def link(self, input: int, output: int):
        await self.send_command(f'switch-set{output}.{input}')

    async def unlink(self, input: int, output: int):
        link = await self.get_link(output)
        if link is not None and link == input:
            await self.send_command(f'switch-set{output}.disconnect')

    async def link_changed(self, output: int, input: int):
        _LOGGER.info(f'switch {output} connected to {input}')
        await self._updated('changed', (output, input))
    
    @property
    def links(self):
        return self._links

    async def parse(self, value: str):
        if value.startswith('err'):
            return False
        m = re.search('(ainput|aoutput)-([a-z\-]+)(\d+):(.*)', value)
        if m:
            if m.group(1) == 'ainput':
                await self.input(int(m.group(3))).parse(m.group(2), m.group(4))
            elif m.group(1) == 'aoutput':
                await self.output(int(m.group(3))).parse(m.group(2), m.group(4))
            else:
                raise ValueError(f'got unknown response: {value}')
        else:
            m = re.search('switch(\d+).(\d+)', value)
            if m:
                output = int(m.group(1))
                input = int(m.group(2))
                if input == 0:
                    if output in self._links:
                        del self._links[output]
                        await self.link_changed(output, input)
                else:
                    if output not in self._links or self._links[output] != input:
                        self._links[output] = input
                        await self.link_changed(output, input)
            else:
                raise ValueError(f'got unknown response: {value}')
        return True


