"""
This module contains functions that are used in both, the main RpiEnergyMeter code and the calibration code
"""

import time
import sys
import numpy
import docker
# import subprocess

from config import *
from influxdb_client import Point
from socket import getfqdn
from cmath import sqrt
from time import sleep
from textwrap import dedent


def get_bias_voltage(adc, numMeasurements=10) -> float:
    """Measures the Bias_V voltage on the Board in reference to a stable 3.3 V ADC Reference

    Args:
        numMeasurements (int): How often a measurement gets taken and averaged over before returning

    Returns:
        dict: time = time of the measurement; value = bias voltage
    """
    _samples = []

    zeit = time.time()
    while len(_samples) <= numMeasurements:
        data = adc.read(adc_channel_bias)
        _samples.append(data)

    avg_reading = sum(_samples) / len(_samples)
    voltage = (avg_reading / ADC_RESOLUTION) * VREF
    
    _sample = {
        'time' : zeit,
        'value' : voltage
    }
    
    return _sample

def get_bias_voltage2(adc, numMeasurements=10) -> float:
    """Measures the Bias_V voltage on the Board in reference to a stable 3.3 V ADC Reference

    Args:
        numMeasurements (int): How often a measurement gets taken and averaged over before returning

    Returns:
        dict: time = time of the measurement; value = bias voltage
    """
    _samples = []
    values = []

    zeit = time.time()
    _samples = adc.read(channels=adc_channel_bias, samples=numMeasurements)

    for sample in _samples:
        values.append(sample[0])

    avg_reading = sum(values) / len(values)
    voltage = (avg_reading / ADC_RESOLUTION) * VREF
    
    _sample = {
        'time' : zeit,
        'value' : voltage
    }
    
    return _sample


def generate_bias_value():
    """JUST FOR TESTING
    This function just returns a static value of 1.665 - Voltage

    Returns:
        float: SAMPLE Bias Voltage
    """
    return (VREF / ADC_RESOLUTION) / 2


def collect_data(adc, measurements, numSamples) -> None:
    """Collects {numSamples} of raw data for every ADC channel and fills {measurements} as a dict with the values from {adc}

    Args:
        adc (MCP3003): Instance of MCP3008 to take values from
        measurements (SAMPLES) Instance of SAMPLES to be filled
        numSamples (int): Number of samples to take
    """

    # Initialize variables
    ct1_data = numpy.array([0.00]*numSamples)
    ct2_data = numpy.array([0.00]*numSamples)
    ct3_data = numpy.array([0.00]*numSamples)
    v_data   = numpy.array([0.00]*numSamples)
    ct4_data = numpy.array([0.00]*numSamples)
    ct5_data = numpy.array([0.00]*numSamples)
    ct6_data = numpy.array([0.00]*numSamples)

    t = numpy.array([0.00]*numSamples)

    # Get time of reading for execution time
    time_start = time.time()
    # Start the gathering
    for i in range(numSamples):
        bias_data = adc.read(adc_channel_bias)
        
        ct1_data[i] = adc.read(adc_channel_ct1)
        ct2_data[i] = adc.read(adc_channel_ct2)
        ct3_data[i] = adc.read(adc_channel_ct3)

        v_data[i] = adc.read(adc_channel_vac)
        t[i] = time.time()

        ct4_data[i] = adc.read(adc_channel_ct4)
        ct5_data[i] = adc.read(adc_channel_ct5)
        ct6_data[i] = adc.read(adc_channel_ct6)

    # Some info
    took = time.time() - time_start
    logger.debug(f"... took {took} seconds to take {9 * numSamples} ADC samples. Going to do calculations on them now")
    logger.debug(f"... that evaluates to {9 * numSamples / took} samples / second")
    logger.debug(f"... that evaluates to {9 * numSamples / took / 1000} samples / milli second")

    # Calculate the shit out of that electricity
    for i in range(numSamples):
        ct1_data[i] = (ct1_data[i] - bias_data)
        ct2_data[i] = (ct2_data[i] - bias_data)
        ct3_data[i] = (ct3_data[i] - bias_data)
        v_data[i] = (v_data[i] - bias_data)
        ct4_data[i] = (ct4_data[i] - bias_data)
        ct5_data[i] = (ct5_data[i] - bias_data)
        ct6_data[i] = (ct6_data[i] - bias_data)

    ct1_data *= (VREF / ADC_RESOLUTION) / (CT_WINDING_RATIO * CT_BURDEN_RESISTOR)
    ct2_data *= (VREF / ADC_RESOLUTION) / (CT_WINDING_RATIO * CT_BURDEN_RESISTOR)
    ct3_data *= (VREF / ADC_RESOLUTION) / (CT_WINDING_RATIO * CT_BURDEN_RESISTOR)
    v_data *= (VREF / ADC_RESOLUTION) * RATIO_GRID_VDIV
    ct4_data *= (VREF / ADC_RESOLUTION) / (CT_WINDING_RATIO * CT_BURDEN_RESISTOR)
    ct5_data *= (VREF / ADC_RESOLUTION) / (CT_WINDING_RATIO * CT_BURDEN_RESISTOR)
    ct6_data *= (VREF / ADC_RESOLUTION) / (CT_WINDING_RATIO * CT_BURDEN_RESISTOR)


    # Fill given instance with data
    measurements.samples_ct1 = ct1_data
    measurements.samples_ct2 = ct2_data
    measurements.samples_ct3 = ct3_data
    measurements.samples_vac = v_data
    measurements.t = t
    measurements.samples_ct4 = ct4_data
    measurements.samples_ct5 = ct5_data
    measurements.samples_ct6 = ct6_data



def collect_data2(adc, measurements, numSamples) -> None:
    """Collects {numSamples} of raw data for every ADC channel and fills {measurements} as a dict with the values from {adc}

    Args:
        adc (MCP3003_2): Instance of MCP3008_2 to take values from
        measurements (SAMPLES) Instance of SAMPLES to be filled
        numSamples (int): Number of samples to take
    """

    # Initialize variables
    ct1_data = numpy.array([0.00]*numSamples)
    ct2_data = numpy.array([0.00]*numSamples)
    ct3_data = numpy.array([0.00]*numSamples)
    v_data   = numpy.array([0.00]*numSamples)
    ct4_data = numpy.array([0.00]*numSamples)
    ct5_data = numpy.array([0.00]*numSamples)
    ct6_data = numpy.array([0.00]*numSamples)

    t = numpy.array([0.00]*numSamples)

    # Get time of reading for execution time
    time_start = time.time()
    # Start the gathering
    _data = adc.read(samples=numSamples)
    for i in range(len(_data)):
        bias_data = _data[i][adc_channel_bias]
        
        ct1_data[i] = _data[i][adc_channel_ct1] - bias_data
        ct2_data[i] = _data[i][adc_channel_ct2] - bias_data
        ct3_data[i] = _data[i][adc_channel_ct3] - bias_data

        v_data[i] = _data[i][adc_channel_vac] - bias_data
        t[i] = time.time()

        ct4_data[i] = _data[i][adc_channel_ct4] - bias_data
        ct5_data[i] = _data[i][adc_channel_ct5] - bias_data
        ct6_data[i] = _data[i][adc_channel_ct6] - bias_data

    # Some info
    took = time.time() - time_start
    logger.debug(f"... took {took} seconds to take {8 * numSamples} ADC samples. Going to do calculations on them now")
    logger.debug(f"... that evaluates to {8 * numSamples / took} samples / second")
    logger.debug(f"... that evaluates to {8 * numSamples / took / 1000} samples / milli second")

    ct1_data *= (VREF / ADC_RESOLUTION) / (CT_WINDING_RATIO * CT_BURDEN_RESISTOR)
    ct2_data *= (VREF / ADC_RESOLUTION) / (CT_WINDING_RATIO * CT_BURDEN_RESISTOR)
    ct3_data *= (VREF / ADC_RESOLUTION) / (CT_WINDING_RATIO * CT_BURDEN_RESISTOR)
    v_data *= (VREF / ADC_RESOLUTION) * RATIO_GRID_VDIV
    ct4_data *= (VREF / ADC_RESOLUTION) / (CT_WINDING_RATIO * CT_BURDEN_RESISTOR)
    ct5_data *= (VREF / ADC_RESOLUTION) / (CT_WINDING_RATIO * CT_BURDEN_RESISTOR)
    ct6_data *= (VREF / ADC_RESOLUTION) / (CT_WINDING_RATIO * CT_BURDEN_RESISTOR)


    # Fill given instance with data
    measurements.samples_ct1 = ct1_data
    measurements.samples_ct2 = ct2_data
    measurements.samples_ct3 = ct3_data
    measurements.samples_vac = v_data
    measurements.t = t
    measurements.samples_ct4 = ct4_data
    measurements.samples_ct5 = ct5_data
    measurements.samples_ct6 = ct6_data




def generate_data(measurements, numSamples,
        phase_voltage=230.00,
        current_ct2=8.00,
        current_ct3=2.00,
        current_ct4=3.00,
        current_ct5=0.50,
        current_ct6=50.00) -> None:
    """This functions propagates given measurements instance values with generated sine wave values

    Args:
        measurements (SAMPLES) Instance of SAMPLES to be filled
        numSamples (int): Number of samples to generate
        phase_voltage (float, optional): RMS Voltage to be generated. Defaults to 230.00.
        current_ct2 (float, optional): Current for the channel. Defaults to 8.00.
        current_ct3 (float, optional): Current for the channel. Defaults to 2.00.
        current_ct4 (float, optional): Current for the channel. Defaults to 3.00.
        current_ct5 (float, optional): Current for the channel. Defaults to 0.50.
        current_ct6 (float, optional): Current for the channel. Defaults to 10.00.
    """
    # Get time of reading for execution time
    time_start = time.time()

    time_per_sample = ADC_SAMPLERATE ** -1
    sine_frequency = GRID_FREQUENCY

    end_time = time_per_sample * numSamples
    t = numpy.arange(0.0, end_time, time_per_sample)
    amp_v = (phase_voltage * sqrt(2))
    amp_ct1 = (current_ct2 + current_ct3 + current_ct4 + current_ct5 - current_ct6) * sqrt(2)
    amp_ct2 = (current_ct2 * sqrt(2))
    amp_ct3 = (current_ct3 * sqrt(2))
    amp_ct4 = (current_ct4 * sqrt(2))
    amp_ct5 = (current_ct5 * sqrt(2))
    amp_ct6 = (current_ct6 * sqrt(2))

    ct1_data = numpy.array([0.00]*numSamples)
    ct2_data = numpy.array([0.00]*numSamples)
    ct3_data = numpy.array([0.00]*numSamples)
    v_data   = numpy.array([0.00]*numSamples)
    t        = numpy.array([0.00]*numSamples)
    ct4_data = numpy.array([0.00]*numSamples)
    ct5_data = numpy.array([0.00]*numSamples)
    ct6_data = numpy.array([0.00]*numSamples)

    # Get time of reading for execution time
    time_start = time.time()

    ct1 = amp_ct1.real * numpy.sin(2 * numpy.pi * sine_frequency * t + 0.45)
    ct2 = amp_ct2.real * numpy.sin(2 * numpy.pi * sine_frequency * t + 0.30)
    ct3 = amp_ct3.real * numpy.sin(2 * numpy.pi * sine_frequency * t + 0.15)
    v = amp_v.real * numpy.sin(2 * numpy.pi * sine_frequency * t + 0)
    ct4 = amp_ct4.real * numpy.sin(2 * numpy.pi * sine_frequency * t - 0.30)
    ct5 = amp_ct5.real * numpy.sin(2 * numpy.pi * sine_frequency * t - 0.45)
    ct6 = amp_ct6.real * numpy.sin(2 * numpy.pi * sine_frequency * t - 0.60)

    # Start the gathering
    for i in range(numSamples):
        ct1_data[i] = ct1[i]
        ct2_data[i] = ct2[i]
        ct3_data[i] = ct3[i]
        t[i]        = time.time()
        v_data[i]   = v[i]
        ct4_data[i] = ct4[i]
        ct5_data[i] = ct5[i]
        ct6_data[i] = ct6[i]

    # Some info
    took = time.time() - time_start
    logger.debug(f"... took {took} seconds to GENERATE {9 * numSamples} ADC samples and take calculations on them directly")
    logger.debug(f"... that evaluates to {9 * numSamples / took} samples / second")
    logger.debug(f"... that evaluates to {9 * numSamples / took / 1000} samples / milli second")

    # Output
    measurements.samples_ct1 = ct1_data
    measurements.samples_ct2 = ct2_data
    measurements.samples_ct3 = ct3_data
    measurements.samples_vac = v_data
    measurements.t = t
    measurements.samples_ct4 = ct4_data
    measurements.samples_ct5 = ct5_data
    measurements.samples_ct6 = ct6_data


def to_point(phase: int, measurements: dict, amount: int, name: str, time: int):
    """Transforms SAMPLES measurements to a single InfluxDBv2 Point

    Args:
        phase (int) Phase on which the measurements were taken
        measurements (dict|list): Dictionary of samples or just a list of measurements
        amount (int): We will take the average over this integer (sum(measurements)/amount)
        name (str): Name of the measurement (_measurement in InfluxDBv2)
        time (int): Time since epoch in ms (usually time.time())

    Returns:
        influxdb_client.POINT: InfluxDBv2 client API POINT class instance

    """
    
    _measurements = measurements
    _point = object()
    if amount > 1:
        if type(_measurements) is dict:
            for key, value in measurements.items():
                _measurements[key] = sum(_measurements[key]) / amount
        else:
                _measurements = sum(_measurements) / amount

        _point = Point(name.split('_')[0])

        tags = {}
        tags['host'] = getfqdn()
        tags['phase'] = phase

        if name.find('_') != -1:
            tags['sensor'] = int(name.split('_')[1])

        for tag, value in tags.items():
            _point = _point.tag(tag, value)

        if type(_measurements) is dict:
            for field, value in _measurements.items():
                _point = _point.field(field, value)
        else:
                _point = _point.field(name, _measurements)

    else:
        _point = Point(name.split('_')[0])

        tags = {}
        tags['host'] = getfqdn()
        tags['phase'] = phase

        if name.find('_') != -1:
            tags['sensor'] = int(name.split('_')[1])

        for tag, value in tags.items():
            _point = _point.tag(tag, value)

        if type(_measurements) is dict:
            for field, value in _measurements.items():
                _point = _point.field(field, value)
        else:
                _point = _point.field(name.split('_')[0], _measurements)


    _point.time(time, write_precision='ms')

    return _point
