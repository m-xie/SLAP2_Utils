"""Parse binary line headers from SLAP2 data files."""

import struct

import numpy as np


LINE_HEADER_MAGIC = 322379495
_BASE_HEADER = struct.Struct("<IIIIIhhQ")
_Z_FIELDS = struct.Struct("<ff")


def decodeLineHeaderFlags(rawFlags):
    """Decode the flag bitfield stored in a SLAP2 line header."""
    rawFlags = int(rawFlags)
    return {
        "startOfAcq": bool(rawFlags & (1 << 0)),
        "endOfAcq": bool(rawFlags & (1 << 1)),
        "startOfCycle": bool(rawFlags & (1 << 3)),
        "endOfCylce": bool(rawFlags & (1 << 4)),
        "dmdSyncPin": bool(rawFlags & (1 << 5)),
        "syncPending": bool(rawFlags & (1 << 6)),
    }


def decodeLineHeaderTimestamp(timestamp, fpgaSystemClock_Hz=None,
                              referenceTimestamp=None):
    """Convert an FPGA timestamp to seconds relative to a reference tick."""
    if fpgaSystemClock_Hz is None or referenceTimestamp is None:
        return np.nan

    clockHz = float(fpgaSystemClock_Hz)
    if not np.isfinite(clockHz) or clockHz <= 0:
        return np.nan

    return (int(timestamp) - int(referenceTimestamp)) / clockHz


def parseLineHeader(data, fpgaSystemClock_Hz=None, referenceTimestamp=None):
    """Parse a 32-byte or 40-byte SLAP2 line header.

    Parameters
    ----------
    data : bytes-like
        Complete binary line header in little-endian byte order.
    fpgaSystemClock_Hz : float, optional
        FPGA clock rate used to derive ``timestamp_s``.
    referenceTimestamp : int, optional
        FPGA tick used as zero for ``timestamp_s``.

    Returns
    -------
    dict
        Parsed fields using the MATLAB reader's public field names.
    """
    raw = memoryview(data).cast("B")
    if len(raw) not in (32, 40):
        raise ValueError("SLAP2 line headers must contain exactly 32 or 40 bytes")

    (lineSizeBytes, magicNumber, lineNumber, acqNumber, rawFlags,
     xOffset_pix, yOffset_pix, timestamp) = _BASE_HEADER.unpack_from(raw)

    if magicNumber != LINE_HEADER_MAGIC:
        raise ValueError(
            "SLAP2 line-header magic number does not match the expected value"
        )

    if len(raw) == 40:
        zOffset_um, zFeedback_um = _Z_FIELDS.unpack_from(raw, 32)
    else:
        zOffset_um = 0.0
        zFeedback_um = np.nan

    timestamp_s = decodeLineHeaderTimestamp(
        timestamp,
        fpgaSystemClock_Hz=fpgaSystemClock_Hz,
        referenceTimestamp=referenceTimestamp,
    )

    return {
        "lineSizeBytes": np.uint32(lineSizeBytes),
        "magicNumber": np.uint32(magicNumber),
        "lineNumber": np.uint32(lineNumber),
        "acqNumber": np.uint32(acqNumber),
        "rawFlags": np.uint32(rawFlags),
        "xOffset_pix": int(xOffset_pix),
        "yOffset_pix": int(yOffset_pix),
        "timestamp": np.uint64(timestamp),
        "zOffset_um": np.float32(zOffset_um),
        "zFeedback_um": np.float32(zFeedback_um),
        "flags": decodeLineHeaderFlags(rawFlags),
        "timestamp_s": timestamp_s,
    }
