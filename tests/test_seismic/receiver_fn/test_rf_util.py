#!/usr/bin/env python
"""Unit testing for seismic resampling functions
"""

import itertools

import numpy as np
import obspy

import seismic.receiver_fn.rf_util as rf_util
from seismic.stream_processing import zne_order, zrt_order

def _rms(signal, axis=-1):
    return np.sqrt(np.mean(np.square(signal), axis))
# end func


def test_phase_weighting():
    # Create test signals with matching amplitudes everywhere, but a maxture of coherent and
    # random phases. Verify the phase weights are small where the phases are random.
    N = 30
    L = 100
    np.random.seed(20200219)
    phases = np.random.uniform(-np.pi, np.pi, (N, L))
    phases[:, (L//4):(L//2)] = np.linspace(-np.pi, np.pi, (L//2) - (L//4))
    phases[:, (3*L//4):L] = np.linspace(-np.pi, np.pi, L - (3*L//4))
    amplitudes = np.zeros_like(phases)
    amplitudes[:, :(L//2)] = np.linspace(0, 2, L//2)
    amplitudes[:, (L//2):] = np.linspace(2, 0, L - L//2)
    signals = amplitudes * np.cos(phases)
    test_traces = [obspy.Trace(d) for d in signals]
    weights = rf_util.phase_weights(test_traces)
    signals_weighted = signals * weights

    # Check that coherent sections have unit weights.
    # Some edge padding is added to ignore edge effects. This may be improved by zero
    # padding in rf_util.phase_weights.
    edge_padding = (1, 1)
    assert np.allclose(weights[(L//4 + edge_padding[0]):(L//2 - edge_padding[1])], 1, rtol=0.025)
    edge_padding = (3, 4)
    assert np.allclose(weights[(3*L//4 + edge_padding[0]):(L - edge_padding[1])], 1, rtol=0.025)

    # Check that RMS signal in coherent sections is about the same as the original signal.
    assert np.allclose(_rms(signals_weighted[:, (L//4):(L//2)]), _rms(signals[:, (L//4):(L//2)]), rtol=0.025)

    # Check that RMS signal in incoherent sections is much less than in the original signal,
    # indicating that incoherent samples are suppressed.
    assert np.all(_rms(signals_weighted[:, :(L//4)]) < 0.5 * _rms(signals[:, :(L//4)]))
    assert np.all(_rms(signals_weighted[:, (L//2):(3*L//4)]) < 0.5 * _rms(signals[:, (L//2):(3*L//4)]))

# end func


def test_trace_ordering():
    test_stream = obspy.Stream([obspy.Trace(np.random.rand(20)) for _ in range(3)])

    # Test ZNE ordering
    ordered = ('BHZ', 'BHN', 'BHE')
    for perm in itertools.permutations(ordered):
        for i, tr in enumerate(test_stream):
            tr.stats.channel = perm[i]
        # end for
        test_stream.traces.sort(key=zne_order)
        assert tuple(tr.stats.channel for tr in test_stream) == ordered
    # end for

    # Test ZRT ordering
    ordered = ('BHZ', 'BHR', 'BHT')
    for perm in itertools.permutations(ordered):
        for i, tr in enumerate(test_stream):
            tr.stats.channel = perm[i]
        # end for
        test_stream.traces.sort(key=zrt_order)
        assert tuple(tr.stats.channel for tr in test_stream) == ordered
    # end for

# end func


if __name__ == "__main__":
    test_phase_weighting()
    test_trace_ordering()
# end if
