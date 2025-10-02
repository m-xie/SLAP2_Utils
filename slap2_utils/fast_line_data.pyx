# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

import numpy as np
cimport numpy as np
from libc.stdint cimport int16_t, int64_t

np.import_array()

def fast_get_line_data(
    const int16_t[:] hMemmap,
    list lineDataNumElements,
    list lineDataStartIdxs,
    int numChannels,
    int firstCycleOffsetBytes,
    int bytesPerCycle,
    np.ndarray[np.int64_t, ndim=1] lineIndices_np,
    np.ndarray[np.int64_t, ndim=1] cycleIndices_np,
    np.ndarray[np.int64_t, ndim=1] iChannel_np
):
    """
    Extracts line data from a memory-mapped int16 binary file
    for specified lines, cycles, and channels.

    Parameters
    ----------
    hMemmap : memoryview of int16
        Memory-mapped data array from the binary file.
    lineDataNumElements : list of int
        Number of elements for each line.
    lineDataStartIdxs : list of int
        Start indices (in bytes) for each line.
    numChannels : int
        Total number of channels in the data.
    firstCycleOffsetBytes : int
        Offset in bytes to the first cycle in the file.
    bytesPerCycle : int
        Number of bytes per cycle.
    lineIndices_np : np.ndarray[np.int64_t, ndim=1]
        Array of line indices (1-based).
    cycleIndices_np : np.ndarray[np.int64_t, ndim=1]
        Array of cycle indices (1-based).
    iChannel_np : np.ndarray[np.int64_t, ndim=1]
        Array of channel indices (1-based).

    Returns
    -------
    list of np.ndarray
        Each entry is a 2D NumPy array (samples_per_channel, num_channels)
        containing the extracted data for one line/cycle.
    """
    cdef:
        const int64_t[:] lineIndices = lineIndices_np
        const int64_t[:] cycleIndices = cycleIndices_np
        const int64_t[:] iChannel = iChannel_np
        int num_indices = lineIndices_np.shape[0]
        int num_channels = iChannel_np.shape[0]
        list lineData = [None] * num_indices
        int idx, line_idx, samples_per_channel, line_start_offset
        int ch_idx, i, precomputed_offset, channel_offset
        int16_t[:, :] result_view

    for idx in range(num_indices):
        line_idx = lineIndices[idx] - 1
        samples_per_channel = lineDataNumElements[line_idx] // numChannels
        line_start_offset = lineDataStartIdxs[line_idx] * 2
        result = np.empty((samples_per_channel, num_channels), dtype=np.int16)
        lineData[idx] = result
        result_view = result
        precomputed_offset = (line_start_offset + bytesPerCycle * (cycleIndices[idx] - 1)) // 2
        for ch_idx in range(num_channels):
            channel_offset = precomputed_offset + samples_per_channel * (iChannel[ch_idx] - 1)
            for i in range(samples_per_channel):
                result_view[i, ch_idx] = hMemmap[i + channel_offset - 1]

    return lineData