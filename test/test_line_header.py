import struct

import numpy as np
import pytest

from slap2_utils.utils.line_header import LINE_HEADER_MAGIC, parseLineHeader


def make_header(size=40, magic=LINE_HEADER_MAGIC):
    base = struct.pack(
        "<IIIIIhhQ",
        128,
        magic,
        17,
        23,
        0b01111011,
        -12,
        34,
        807_174_241_722,
    )
    if size == 40:
        return base + struct.pack("<ff", 12.5, -3.25)
    return base[:size]


def test_parse_40_byte_line_header():
    header = parseLineHeader(
        make_header(),
        fpgaSystemClock_Hz=200_000_000,
        referenceTimestamp=807_174_241_522,
    )

    assert header["lineSizeBytes"] == np.uint32(128)
    assert header["magicNumber"] == np.uint32(LINE_HEADER_MAGIC)
    assert header["lineNumber"] == np.uint32(17)
    assert header["acqNumber"] == np.uint32(23)
    assert header["rawFlags"] == np.uint32(0b01111011)
    assert header["xOffset_pix"] == -12
    assert header["yOffset_pix"] == 34
    assert header["timestamp"] == np.uint64(807_174_241_722)
    assert header["zOffset_um"] == np.float32(12.5)
    assert header["zFeedback_um"] == np.float32(-3.25)
    assert header["timestamp_s"] == pytest.approx(1e-6)
    assert header["timestamp_date"] is None
    assert header["flags"] == {
        "startOfAcq": True,
        "endOfAcq": True,
        "startOfCycle": True,
        "endOfCylce": True,
        "dmdSyncPin": True,
        "syncPending": True,
    }


def test_parse_32_byte_line_header_defaults_optional_z_fields():
    header = parseLineHeader(make_header(size=32))

    assert header["zOffset_um"] == np.float32(0)
    assert np.isnan(header["zFeedback_um"])
    assert np.isnan(header["timestamp_s"])


@pytest.mark.parametrize("size", [0, 31, 33, 39, 41])
def test_parse_line_header_rejects_unsupported_lengths(size):
    with pytest.raises(ValueError, match="32 or 40 bytes"):
        parseLineHeader(bytes(size))


def test_parse_line_header_rejects_wrong_magic_number():
    with pytest.raises(ValueError, match="magic number"):
        parseLineHeader(make_header(magic=1))
