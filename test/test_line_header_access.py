import os

import numpy as np
import pytest

import slap2_utils.datafile as datafile_module
from slap2_utils.datafile import DataFile
from slap2_utils.utils.line_header import LINE_HEADER_MAGIC


@pytest.fixture
def datafile():
    test_dir = os.path.dirname(__file__)
    return DataFile(os.path.join(test_dir, "testFile.dat"))


def test_get_line_header_reads_real_fixture(datafile):
    header = datafile.getLineHeader(1, 1)

    assert header["lineSizeBytes"] == np.uint32(40)
    assert header["magicNumber"] == np.uint32(LINE_HEADER_MAGIC)
    assert header["lineNumber"] == np.uint32(0)
    assert header["acqNumber"] == np.uint32(1)
    assert header["xOffset_pix"] == 0
    assert header["yOffset_pix"] == 0
    assert header["timestamp"] == np.uint64(807_174_241_522)
    assert header["zOffset_um"] == np.float32(0)
    assert header["timestamp_s"] == pytest.approx(0.0)


def test_get_line_header_batches_and_broadcasts_cycle(datafile):
    headers = datafile.getLineHeader([1, 2], 1)

    assert isinstance(headers, list)
    assert [header["lineNumber"] for header in headers] == [0, 1]
    assert [header["timestamp"] for header in headers] == sorted(
        header["timestamp"] for header in headers
    )


def test_get_line_header_preserves_request_order(datafile):
    headers = datafile.getLineHeader([2, 1], [2, 1])

    assert headers[0]["lineNumber"] == np.uint32(1)
    assert headers[0]["acqNumber"] == np.uint32(1)
    assert headers[1]["lineNumber"] == np.uint32(0)
    assert headers[1]["acqNumber"] == np.uint32(1)


def test_get_line_header_empty_request(datafile):
    assert datafile.getLineHeader([], []) == []


@pytest.mark.parametrize(
    "line_indices,cycle_indices,message",
    [
        ([0], [1], "positive integers"),
        ([1], [0], "positive integers"),
        ([303], [1], "linesPerCycle"),
        ([1], [345], "numCycles"),
        ([1, 2], [1, 2, 3], "match"),
        ([1.5], [1], "integers"),
    ],
)
def test_get_line_header_rejects_invalid_indices(
        datafile, line_indices, cycle_indices, message):
    with pytest.raises(ValueError, match=message):
        datafile.getLineHeader(line_indices, cycle_indices)


def test_datafile_records_first_line_timestamp(datafile):
    assert datafile.firstLineTimestamp == np.uint64(807_174_241_522)


def test_datafile_with_no_complete_cycles_skips_first_line_header(monkeypatch):
    datafile = DataFile.__new__(DataFile)
    datafile.MAGIC_NUMBER = np.uint32(LINE_HEADER_MAGIC)
    datafile.rawData = np.zeros(6, dtype=np.int16)
    datafile.rawData.view(np.uint32)[0] = LINE_HEADER_MAGIC
    datafile.rawData.view(np.uint32)[1] = 2
    datafile.rawData.view(np.uint32)[2] = 40
    datafile.firstLineTimestamp = None

    header = {
        "firstCycleOffsetBytes": 8,
        "lineHeaderSizeBytes": 40,
        "bytesPerCycle": 40,
        "linesPerCycle": 1,
    }
    monkeypatch.setattr(
        datafile_module,
        "load_file_header_v2",
        lambda _datafile, _raw_data: (header, 0),
    )

    datafile.load_file_header()

    assert datafile.numCycles == 0
    assert datafile.firstLineTimestamp is None
