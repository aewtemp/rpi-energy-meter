"""Module to interact with a MCP3008 ADC via SPI bus"""

import subprocess
from pathlib import Path

base_path = Path(__file__).parent.resolve()
exec_path = base_path / "helper" / "mcp3008hwspi"


class MCP3008_2:
    def __init__(self, device=0):
        self.device = device

    def read(self, channels="01234567", samples=200):
        result = subprocess.run(
            [
                str(exec_path),
                "-r",
                "1250000",
                "-c",
                str(channels),
                "-f",
                "0",
                "-n",
                str(samples),
                "-b",
                "1",
                "-d",
                str(self.device),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        _data_out = result.stdout
        _samples = [[0] * 8 for _ in range(samples)]
        for i, line in enumerate(_data_out.split("\n")):
            if line == "":
                break
            _samples[i] = list(map(int, line.split(",")))
        return _samples
