# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Raspberry Pi energy meter for real-time 3-phase electrical power monitoring. Uses MCP3008 ADC chips (via SPI) and current transformers to measure voltage, current, power factor, and harmonics. Data is written to InfluxDB v2 for time-series storage.

**Target hardware:** Raspberry Pi 3B with 32-bit OS (Debian >11 or Ubuntu >20.04), custom PCB with 3× MCP3008 ADCs.

## Commands

### Install / Setup
```bash
pip install -e .
# or
pip install -r requirements.txt
```

### Run
```bash
# Normal mode (continuous measurement → InfluxDB)
rpi-energy-meter -c config.toml

# Debug mode (single measurement, generates Plotly HTML charts)
rpi-energy-meter -c config.toml debug

# Calibration mode (interactive phase-shift tuning)
rpi-energy-meter -c config.toml calibration

# Performance benchmark
rpi-energy-meter -c config.toml speedtest

# Lint (runs pylint)
rpi-energy-meter tests
```

### Code quality tools (configured in pyproject.toml)
```bash
black rpi_energy_meter/
isort rpi_energy_meter/
pylint rpi_energy_meter/
mypy rpi_energy_meter/
```

## Architecture

### Data flow
```
MCP3008 ADC (SPI) → collect_data2() → SAMPLES object → shift_phase() (FFT) → calculate_power() → InfluxDB v2
```

### Key modules

| File | Role |
|------|------|
| `energy_meter.py` | Orchestrator: initializes hardware, routes commands, manages measurement loop |
| `samples.py` | `SAMPLES` class: stores raw ADC data, applies Hilbert-transform phase correction, calculates power metrics |
| `utils.py` | `collect_data2()` batch ADC reading, InfluxDB point construction, calibration helpers |
| `mcp3008.py` | SPI hardware interface for MCP3008 ADC chips |
| `config.py` | TOML config loader/writer using `python-box` and `tomli` |
| `influxv2_interface.py` | InfluxDB v2 batch writer (500 pts/batch, 10 s flush, auto-retry) |
| `plotting.py` | Plotly HTML chart generation for debug/calibration output |

### Hardware layout
- 3 MCP3008 chips on SPI0, chip selects 0–2 (one per phase)
- Each chip: 6 CT channels + 1 voltage channel + 1 bias reference
- Sampling: 3250 Hz ADC rate, 400 samples per measurement (~123 ms window)

### Configuration (`config.toml`)
Copy `config.toml.example` → `config.toml`. Key sections:
- `[GENERAL]`: ADC reference voltage, resolution, sample rate, sample count
- `[INFLUX]`: InfluxDB v2 host/port/token/org/bucket
- `[PHASES]`: Phase count, grid frequency, transformer ratios, per-phase voltages
- `[VOLTMETER_N]`: Per-phase voltage calibration (bias, VAC, channel)
- `[CTS_N_M]`: Per-CT config — channel, description, type (`mains`/`consumption`/`production`), phase shift (`SHIFT`), calibration factor (`FACTOR`), accumulated energy (`KWH`)

Accumulated kWh values are written back to `config.toml` on each measurement cycle — do not hand-edit `KWH` fields while the service is running.

### Systemd deployment
See `examples/rpi-energy-meter.service`. Uses `KillSignal=SIGINT` for graceful shutdown.
