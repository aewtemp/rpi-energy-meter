"""
Module to represent and interact with samples taken by raspi power monitor
"""

import numpy
import cmath

from math import sqrt
from scipy import signal
from scipy.signal import hilbert

from statsmodels.tsa.stattools import ccf
from box import Box


class SAMPLES():
    def __init__(self, config: Box, phase: int, totals):
        self._samples = {
            't': numpy.array([0.00]*config.GENERAL.ADC_SAMPLES),
            'vac': numpy.array([0.00]*config.GENERAL.ADC_SAMPLES),
            'ct1': numpy.array([0.00]*config.GENERAL.ADC_SAMPLES),
            'ct2': numpy.array([0.00]*config.GENERAL.ADC_SAMPLES),
            'ct3': numpy.array([0.00]*config.GENERAL.ADC_SAMPLES),
            'ct4': numpy.array([0.00]*config.GENERAL.ADC_SAMPLES),
            'ct5': numpy.array([0.00]*config.GENERAL.ADC_SAMPLES),
            'ct6': numpy.array([0.00]*config.GENERAL.ADC_SAMPLES),
            'bias': numpy.array([0.00]*config.GENERAL.ADC_SAMPLES),
            }

        self._correction_factors = {
            'vac': config.VOLTMETER.get(str(phase)).VAC.FACTOR,
            'ct1': config.CTS.get(str(phase))["1"].FACTOR,
            'ct2': config.CTS.get(str(phase))["2"].FACTOR,
            'ct3': config.CTS.get(str(phase))["3"].FACTOR,
            'ct4': config.CTS.get(str(phase))["4"].FACTOR,
            'ct5': config.CTS.get(str(phase))["5"].FACTOR,
            'ct6': config.CTS.get(str(phase))["6"].FACTOR,
            'bias': config.VOLTMETER.get(str(phase)).BIAS.FACTOR,
        }

        self._phaseshifts = {
            'ct1': config.CTS.get(str(phase))["1"].SHIFT,
            'ct2': config.CTS.get(str(phase))["2"].SHIFT,
            'ct3': config.CTS.get(str(phase))["3"].SHIFT,
            'ct4': config.CTS.get(str(phase))["4"].SHIFT,
            'ct5': config.CTS.get(str(phase))["5"].SHIFT,
            'ct6': config.CTS.get(str(phase))["6"].SHIFT,
        }

        self._power = [
            {
                'Voltage': 0.00,
                'Current': 0.00,
                'Watts': 0.00,
                'PF': 0.00,
            } for _ in range(6)
        ]

        self._energy = [
            {
                'Total': float(totals[0]['Total']),
            } for _ in range(6)
        ]


    @property
    def samples(self):
        return self._samples

    def set_samples(self, samples, name):
        self._samples[name] = numpy.array(samples)

    @property
    def correction_factors(self):
        return self._correction_factors

    def set_correction_factor(self, factor, name):
        self._correction_factors[name] = factor

    @property
    def phaseshifts(self):
        return self._phaseshifts

    def set_phaseshift(self, shift, ct):
        self._phaseshifts[ct] = shift

    @property
    def t(self):
        return self._samples['t']
    @t.setter
    def t(self, value):
        self._samples['t'] = numpy.array(value)

    @property
    def samples_vac(self):
        return self._samples['vac']
    @samples_vac.setter
    def samples_vac(self, value):
        self._samples['vac'] = numpy.array(value) * self._correction_factors['vac']

    @property
    def samples_ct1(self):
        return self._samples['ct1']
    @samples_ct1.setter
    def samples_ct1(self, value):
        self._samples['ct1'] = numpy.array(value) * self._correction_factors['ct1']

    @property
    def samples_ct2(self):
        return self._samples['ct2']
    @samples_ct2.setter
    def samples_ct2(self, value):
        self._samples['ct2'] = numpy.array(value) * self._correction_factors['ct2']

    @property
    def samples_ct3(self):
        return self._samples['ct3']
    @samples_ct3.setter
    def samples_ct3(self, value):
        self._samples['ct3'] = numpy.array(value) * self._correction_factors['ct3']

    @property
    def samples_ct4(self):
        return self._samples['ct4']
    @samples_ct4.setter
    def samples_ct4(self, value):
        self._samples['ct4'] = numpy.array(value) * self._correction_factors['ct4']

    @property
    def samples_ct5(self):
        return self._samples['ct5']
    @samples_ct5.setter
    def samples_ct5(self, value):
        self._samples['ct5'] = numpy.array(value) * self._correction_factors['ct5']

    @property
    def samples_ct6(self):
        return self._samples['ct6']
    @samples_ct6.setter
    def samples_ct6(self, value):
        self._samples['ct6'] = numpy.array(value) * self._correction_factors['ct6']

    @property
    def samples_bias(self):
        return self._samples['bias']
    @samples_bias.setter
    def samples_bias(self, value):
        self._samples['bias'] = numpy.array(value) * self._correction_factors['bias']

    @property
    def power(self):
        return self._power


    def calculate_phaseshift(self, ct) -> int:
        """Calculates the Phaseshift of two measurements

        Args:
            ct (int): Current Transformer to take measurements from

        Returns:
            int: timeshift
        """

        str_ct = 'ct' + str(ct+1)

        vt = self.samples_vac
        ct = self.samples[str_ct]

        vt_h = hilbert(vt)
        ct_h = hilbert(ct)
        c = numpy.inner( vt_h, numpy.conj(ct_h) ) / numpy.sqrt( numpy.inner(vt_h,numpy.conj(vt_h)) * numpy.inner(ct_h,numpy.conj(ct_h)) )
        phase_shift = numpy.angle(c)

        return phase_shift


    def shift_phase(self, ct, amount=None) -> None:
        """Shifts a given current transformers measurements by a given amount

        Args:
            ct (int): Current transformer of which the measurements should be shifted
            amount (int): Amount by which the measurements are shifted
        """
        str_ct = 'ct' + str(ct+1)
        if amount is None:
            amount = self.phaseshifts[str_ct]

        values = self.samples[str_ct]
        valuesFFT = numpy.fft.rfft(values)
        # Remove phase shift from signal2
        shiftedFFT = valuesFFT * cmath.rect(1., amount)
        # Reverse Fourier transform
        shifted = numpy.fft.irfft(shiftedFFT)

        self.set_samples(shifted.real, str_ct)


    def calculate_power(self, phase, config):
        """Calculates Power values for all saved Measurements

        Returns:
            dict: Power values, voltage values, power factor values for all 6 CT-Channels
        """

        samples_v = self.samples_vac
        for i in range(len(self._power)):
            samples_ct = self.samples['ct' + str(i+1)]

            sum_raw_voltage = 0.00
            sum_squared_voltage = 0.00
            sum_raw_current = 0.00
            sum_squared_current = 0.00
            sum_inst_power = 0.00

            num_samples = len(samples_v)
            for y in range(0, num_samples):
                voltage = samples_v[y]
                current = samples_ct[y]

                # Process all data in a single function to reduce runtime complexity
                # Get the sum of all current samples individually
                sum_raw_voltage += voltage
                sum_raw_current += current

                # Squared voltage
                squared_voltage = voltage ** 2
                sum_squared_voltage += squared_voltage

                # Squared current
                squared_current = current ** 2
                sum_squared_current += squared_current

                # Calculate instant power for each ct sensor
                inst_power = voltage * current
                sum_inst_power += inst_power


            avg_raw_voltage = (sum_raw_voltage / num_samples)
            avg_raw_current = (sum_raw_current / num_samples)

            real_power = ((sum_inst_power / num_samples) - (avg_raw_current * avg_raw_voltage))

            mean_square_voltage = (sum_squared_voltage / num_samples)
            mean_square_current = (sum_squared_current / num_samples)

            rms_voltage = sqrt(abs(mean_square_voltage - (avg_raw_voltage ** 2)))
            rms_current = sqrt(abs(mean_square_current - (avg_raw_current ** 2)))
            # Ignore 100 mA as it is swinging around 0.
            rms_current = 0.00 if (-0.10 < rms_current < 0.10) else rms_current

            # Power Factor
            apparent_power = rms_voltage * rms_current

            try:
                power_factor = real_power / apparent_power
            except ZeroDivisionError:
                power_factor = 0.00

            # Cutoff handling
            if config.CTS[str(phase)][str(i+1)].CUTOFF != 0:
                if abs(real_power) < config.CTS[str(phase)][str(i+1)].CUTOFF:
                    real_power = 0.00
                    power_factor = 0.00

            self._power[i]['Voltage'] = round(rms_voltage, 2)
            self._power[i]['Current'] = round(rms_current, 2)
            self._power[i]['Watts'] = round(real_power, 2)
            self._power[i]['PF'] = round(power_factor, 2)

        return self.power
