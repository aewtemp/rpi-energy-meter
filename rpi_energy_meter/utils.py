"""
This module contains functions that are used in both, the main RpiEnergyMeter code and the calibration code
"""

import csv
import time
from datetime import datetime
from socket import AF_INET, SOCK_DGRAM, getfqdn, socket

import numpy
from influxdb_client import Point
from prettytable import PrettyTable

from .logging import logger

# Cache hostname — getfqdn() does a DNS lookup, no need to call it per point
_HOSTNAME = getfqdn()


def get_bias_voltage2(config, phase, adc, numMeasurements=10) -> dict:
    """Measures the Bias_V voltage on the Board in reference to a stable 3.3 V ADC Reference

    Args:
        numMeasurements (int): How often a measurement gets taken and averaged over before returning

    Returns:
        dict: time = time of the measurement; value = bias voltage
    """
    zeit = time.time()
    _samples = adc.read(channels=config.VOLTMETER.get(str(phase)).BIAS.CHANNEL, samples=numMeasurements)

    values = [sample[0] for sample in _samples]
    avg_reading = sum(values) / len(values)
    voltage = (avg_reading / config.GENERAL.ADC_RESOLUTION) * config.GENERAL.VREF

    return {"time": zeit, "value": voltage}


def collect_data2(config, phase, adc, measurements, numSamples) -> None:
    """Collects {numSamples} of raw data for every ADC channel and fills {measurements} as a dict with the values from {adc}

    Args:
        adc (MCP3008_2): Instance of MCP3008_2 to take values from
        measurements (SAMPLES): Instance of SAMPLES to be filled
        numSamples (int): Number of samples to take
    """

    # Initialize variables
    ct1_data = numpy.zeros(numSamples)
    ct2_data = numpy.zeros(numSamples)
    ct3_data = numpy.zeros(numSamples)
    v_data = numpy.zeros(numSamples)
    ct4_data = numpy.zeros(numSamples)
    ct5_data = numpy.zeros(numSamples)
    ct6_data = numpy.zeros(numSamples)

    t = numpy.zeros(numSamples)

    # Get time of reading for execution time
    time_start = time.time()
    # Start the gathering
    _data = adc.read(samples=numSamples)
    for i in range(len(_data)):
        bias_data = _data[i][config.VOLTMETER[str(phase)].BIAS.CHANNEL]

        ct1_data[i] = _data[i][config.CTS[str(phase)]["1"].CHANNEL] - bias_data
        ct2_data[i] = _data[i][config.CTS[str(phase)]["2"].CHANNEL] - bias_data
        ct3_data[i] = _data[i][config.CTS[str(phase)]["3"].CHANNEL] - bias_data

        v_data[i] = _data[i][config.VOLTMETER[str(phase)].VAC.CHANNEL] - bias_data
        t[i] = time.time()

        ct4_data[i] = _data[i][config.CTS[str(phase)]["4"].CHANNEL] - bias_data
        ct5_data[i] = _data[i][config.CTS[str(phase)]["5"].CHANNEL] - bias_data
        ct6_data[i] = _data[i][config.CTS[str(phase)]["6"].CHANNEL] - bias_data

    # Some info
    took = time.time() - time_start
    logger.debug(f"... took {took} seconds to take {8 * numSamples} ADC samples. Going to do calculations on them now")
    logger.debug(f"... that evaluates to {8 * numSamples / took} samples / second")
    logger.debug(f"... that evaluates to {8 * numSamples / took / 1000} samples / milli second")

    adc_factor_ct = (config.GENERAL.VREF / config.GENERAL.ADC_RESOLUTION) / (
        config.CTS.BURDEN_RESISTANCE / config.CTS.WINDING_RATIO
    )
    adc_factor_vac = (config.GENERAL.VREF / config.GENERAL.ADC_RESOLUTION) * (
        config.PHASES[str(phase)].VOLTAGE
        / (config.PHASES[str(phase)].TRANSFORMER_OUTPUT_VOLTAGE / config.PHASES.TRANSFORMER_VDIVIDER)
    )

    ct1_data *= adc_factor_ct
    ct2_data *= adc_factor_ct
    ct3_data *= adc_factor_ct
    v_data *= adc_factor_vac
    ct4_data *= adc_factor_ct
    ct5_data *= adc_factor_ct
    ct6_data *= adc_factor_ct

    # Fill given instance with data
    measurements.samples_ct1 = ct1_data
    measurements.samples_ct2 = ct2_data
    measurements.samples_ct3 = ct3_data
    measurements.samples_vac = v_data
    measurements.t = t
    measurements.samples_ct4 = ct4_data
    measurements.samples_ct5 = ct5_data
    measurements.samples_ct6 = ct6_data


def to_point(phase: int, measurements, amount: int, name: str, time: int):
    """Transforms SAMPLES measurements to a single InfluxDBv2 Point

    Args:
        phase (int): Phase on which the measurements were taken
        measurements (dict|list): Dictionary of samples or just a list of measurements
        amount (int): We will take the average over this integer (sum(measurements)/amount)
        name (str): Name of the measurement (_measurement in InfluxDBv2)
        time (int): Time since epoch in ms (usually time.time())

    Returns:
        influxdb_client.Point: InfluxDBv2 client API Point instance
    """
    _measurements = dict(measurements) if isinstance(measurements, dict) else measurements
    if amount > 1:
        if isinstance(_measurements, dict):
            for key, value in _measurements.items():
                _measurements[key] = sum(value) / amount
        else:
            _measurements = sum(_measurements) / amount

    _point = Point(name.split("_", maxsplit=1)[0])

    tags = {"host": _HOSTNAME, "phase": phase}
    if "_" in name:
        tags["sensor"] = int(name.split("_")[1])

    for tag, value in tags.items():
        _point = _point.tag(tag, value)

    if isinstance(_measurements, dict):
        for field, value in _measurements.items():
            _point = _point.field(field, value)
    else:
        field_name = name if amount > 1 else name.split("_", maxsplit=1)[0]
        _point = _point.field(field_name, _measurements)

    _point.time(time, write_precision="ms")
    return _point


def dump_data(phase, samples):
    now = datetime.now().strftime("%m-%d-%Y-%H-%M")
    filename = f"data-dump-phase{phase}-{now}.csv"
    ct1_data = samples.samples_ct1
    ct2_data = samples.samples_ct2
    ct3_data = samples.samples_ct3
    ct4_data = samples.samples_ct4
    ct5_data = samples.samples_ct5
    ct6_data = samples.samples_ct6
    v_data = samples.samples_vac
    with open(filename, "w") as f:
        headers = ["Sample#", "ct1", "ct2", "ct3", "ct4", "ct5", "ct6", "voltage"]
        writer = csv.writer(f)
        writer.writerow(headers)
        for i in range(len(v_data)):
            writer.writerow(
                [i, ct1_data[i], ct2_data[i], ct3_data[i], ct4_data[i], ct5_data[i], ct6_data[i], v_data[i]]
            )
    logger.info(f"... CSV written to {filename}.")


def print_results(config, phase: int, adc, results: dict):
    """Output a Table to the debugging console

    Args:
        results (dict): Dictionary containing all the results for ct1-ct6 + voltage
    """
    t = PrettyTable(["PHASE " + str(phase), "ct1", "ct2", "ct3", "ct4", "ct5", "ct6"])
    t.add_row(
        [
            "Watts",
            round(results[0]["Watts"], 3),
            round(results[1]["Watts"], 3),
            round(results[2]["Watts"], 3),
            round(results[3]["Watts"], 3),
            round(results[4]["Watts"], 3),
            round(results[5]["Watts"], 3),
        ]
    )
    t.add_row(
        [
            "Current",
            round(results[0]["Current"], 3),
            round(results[1]["Current"], 3),
            round(results[2]["Current"], 3),
            round(results[3]["Current"], 3),
            round(results[4]["Current"], 3),
            round(results[5]["Current"], 3),
        ]
    )
    t.add_row(
        [
            "P.F.",
            round(results[0]["PF"], 3),
            round(results[1]["PF"], 3),
            round(results[2]["PF"], 3),
            round(results[3]["PF"], 3),
            round(results[4]["PF"], 3),
            round(results[5]["PF"], 3),
        ]
    )
    t.add_row(["Voltage", round(results[0]["Voltage"], 3), "", "", "", "", ""])
    t.add_row(
        [
            "Bias_V",
            round(get_bias_voltage2(config, phase, adc)["value"] * config.VOLTMETER[str(phase)].BIAS.FACTOR, 3),
            "",
            "",
            "",
            "",
            "",
        ]
    )
    s = t.get_string()
    logger.debug("\n" + s)


def get_ip():
    # Acquires the Pi's local IP address for use in providing the user with a link to view the charts.
    s = socket(AF_INET, SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = None
    finally:
        s.close()
    return IP
