"""
    -*- coding: utf-8 -*-
    Time    : 2021-05-21 9:25 p.m.
    Author  : Kevin Dunphy
    E-mail  : kevin.dunphy1989@gmail.com
    FileName: spectrogram.py
    
    {Description}
    -------------
    
"""

from signal_analysis_tools.timeseries import *
from scipy import fft
from typing import Union


class Spectrum:
    def __init__(self, frequencies: np.array, amplitude: np.array, bin_size: float, name: str = ''):
        self.data = np.array([*zip(frequencies, amplitude)], dtype=[('frequency', frequencies.dtype),
                                                                    ('amplitude', amplitude.dtype)])
        self.bin_size = bin_size
        self.name = name

    def num_samples(self):
        return len(self.data['frequencies'])

    def nyquist(self):
        return self.data['amplitude'][self.num_samples() // 2]

    def dc_offset(self):
        return self.data['amplitude'][0]

    def positive_content(self):
        return self.data['amplitude'][1:self.num_samples() // 2]

    def negative_content(self):
        return self.data['amplitude'][self.num_samples() // 2 + 1:]

    def to_timeseries(self):
        amplitude = fft.ifft(self.data['amplitude'] * self.num_samples() * self.bin_size)
        sample_rate = 1 / self.bin_size
        time_axis = np.arange(self.num_samples()) / sample_rate
        return Timeseries(time_axis, amplitude, sample_rate)

    def single_sided_power_spectrum(self, duration):
        return 2. / duration * np.conj(self.positive_content()) * self.positive_content()

    def double_sided_power_spectrum(self, duration):
        return 1. / duration * np.conj(self.data['amplitude']) * self.data['amplitude']


def pink(n):
    return 1. / np.sqrt(np.arange(n) + 1)


def random_phase(n: int):
    return np.random.uniform(0, 2 * np.pi, (n,))


def generate_spectrum(n: int = 65536,
                      magnitude: Union[float, callable] = 1.0,
                      phase: Union[float, callable] = random_phase,
                      fs: float = 0.0,
                      dc_offset: float = 0.0,
                      spectral_density=True):
    if fs == 0.0:
        f_res = 1.0
    else:
        f_res = fs / n

    # Calculate positive frequency magnitude
    if type(magnitude) is float or type(magnitude) is int:
        a = np.full(n // 2 - 1, fill_value=magnitude, dtype=float)
    elif callable(magnitude):
        try:
            a = magnitude(n // 2 - 1)
        except ValueError:
            raise ValueError("magnitude function must accept only one input argument: the number of elements.")
    else:
        raise ValueError("Magnitude must be either a float or a callable function")

    if type(phase) is float or type(phase) is int:
        theta = np.full(n // 2 - 1, fill_value=phase)
    elif callable(phase):
        try:
            theta = phase(n // 2 - 1)
        except ValueError:
            raise ValueError("phase function must accept only one input argument: the number of elements.")
    else:
        raise ValueError("phase must be either a float or a callable function")

    if spectral_density:
        a /= f_res
        dc_offset /= f_res

    pos_freq = a * np.exp(1j * theta)

    # Create a complex value for the frequency domain.
    spectrum = np.zeros((n,), dtype=complex)
    spectrum[0] = dc_offset + 0j
    spectrum[1:n // 2] = pos_freq
    spectrum[n // 2] = 0 + 0j
    spectrum[n // 2 + 1:] = np.flip(np.conj(pos_freq))

    # Create frequency axis
    frequencies = np.arange(n) * f_res

    return Spectrum(frequencies, spectrum, f_res)


class SpectrumAnalyzer:
    # Setup common graphics properties.
    TEXTBOX_PROPS = {'boxstyle': 'round', 'facecolor': 'white', 'alpha': 0.75}

    # Setup plotting styles.
    sns.plotting_context("paper")
    sns.set_style("darkgrid")