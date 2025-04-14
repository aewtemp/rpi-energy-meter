"""Module to interact with a MCP3008 ADC via SPI bus"""
import io
import subprocess

from spidev import SpiDev

class MCP3008_2:
    def __init__(self, device = 0):
        self.device = device

    def read(self, channels = '01234567', samples = 200):
        _data_out = subprocess.run(['./helpers/mcp3008hwspi', '-r', '1250000', '-c', str(channels), '-f', '0', '-n', str(samples), '-b', '1', '-d', str(self.device)], capture_output=True, text=True).stdout
        _samples = [[0] * 8] * samples
        i = 0
        for line in _data_out.split('\n'):
            if line == '':
                break
            _samples[i] = list(map(int, line.split(',')))
            i += 1
        return _samples


class MCP3008:
    def __init__(self, bus = 0, device = 0):
        self.bus, self.device = bus, device
        self.spi = SpiDev()
        self.open()
        self.spi.max_speed_hz = 1350000 # 1.35MHz

    def open(self):
        self.spi.open(self.bus, self.device)
    
    def read(self, channel = 0):
        # read SPI data from the MCP3008
        r = self.spi.xfer2([1, 8 + channel << 4, 0])
        data = ((r[1] & 3) << 8) + r[2]
        return data
            
    def close(self):
        self.spi.close()
