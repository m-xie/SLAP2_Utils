import numpy as np
import pytest

from slap2_utils.multidatafiles import MultiDataFiles


class FakeDataFile:
    def __init__(self, name, num_cycles, first_timestamp, file_number):
        self.datFileName = name
        self.numCycles = num_cycles
        self.firstLineTimestamp = np.uint64(first_timestamp)
        self.file_number = file_number

    def getLineHeader(self, line_indices, cycle_indices):
        line_indices = np.asarray(line_indices).ravel()
        cycle_indices = np.asarray(cycle_indices).ravel()
        headers = [
            {
                "lineNumber": np.uint32(line - 1),
                "acqNumber": np.uint32(cycle),
                "xOffset_pix": self.file_number * 100 + int(line),
                "yOffset_pix": self.file_number * -100 - int(cycle),
                "zOffset_um": np.float32(self.file_number + cycle / 10),
            }
            for line, cycle in zip(line_indices, cycle_indices)
        ]
        return headers[0] if len(headers) == 1 else headers


def make_multifile():
    multifile = MultiDataFiles.__new__(MultiDataFiles)
    multifile.header = {"linesPerCycle": 3, "bytesPerCycle": 100}
    multifile.lineHeaderIdxs = np.array([11, 31, 51])
    multifile.lineDataStartIdxs = [31, 51, 71]
    multifile.lineDataNumElements = [10, 10, 10]
    multifile.hDataFiles = [
        FakeDataFile("later.dat", 1, 200, 2),
        FakeDataFile("earlier.dat", 2, 100, 1),
    ]
    multifile.numCycles = 3
    multifile.totalNumLines = 9
    return multifile


def test_multidatafiles_sorts_by_first_line_timestamp():
    multifile = make_multifile()

    multifile._sort_files_in_place()

    assert [datafile.datFileName for datafile in multifile.hDataFiles] == [
        "earlier.dat", "later.dat"
    ]


def test_multidatafiles_get_line_header_routes_and_preserves_order():
    multifile = make_multifile()
    multifile._sort_files_in_place()

    headers = multifile.getLineHeader([2, 1, 3], [3, 1, 2])

    assert [header["xOffset_pix"] for header in headers] == [202, 101, 103]
    assert [header["acqNumber"] for header in headers] == [1, 1, 2]


def test_multidatafiles_get_line_header_scalar():
    multifile = make_multifile()
    multifile._sort_files_in_place()

    header = multifile.getLineHeader(2, 3)

    assert isinstance(header, dict)
    assert header["xOffset_pix"] == 202


def test_multidatafiles_get_online_motion_uses_one_based_global_ids():
    multifile = make_multifile()
    multifile._sort_files_in_place()

    x, y, z = multifile.getOnlineMotion([9, 1, 5, 9])

    np.testing.assert_array_equal(x, [203.0, 101.0, 102.0, 203.0])
    np.testing.assert_array_equal(y, [-201.0, -101.0, -102.0, -201.0])
    np.testing.assert_allclose(z, [2.1, 1.1, 1.2, 2.1])
    assert x.shape == y.shape == z.shape == (4,)


def test_multidatafiles_get_online_motion_defaults_to_one_line_per_cycle():
    multifile = make_multifile()
    multifile._sort_files_in_place()

    x, _, _ = multifile.getOnlineMotion()

    np.testing.assert_array_equal(x, [101.0, 101.0, 201.0])


@pytest.mark.parametrize("line_ids", [[0], [10], [1.5], [np.nan]])
def test_multidatafiles_get_online_motion_rejects_invalid_ids(line_ids):
    multifile = make_multifile()

    with pytest.raises(ValueError, match="lineIds"):
        multifile.getOnlineMotion(line_ids)


def test_datafile_get_online_motion_uses_one_based_global_ids():
    from slap2_utils.datafile import DataFile

    datafile = DataFile.__new__(DataFile)
    datafile.header = {"linesPerCycle": 3}
    datafile.numCycles = 2
    datafile.getLineHeader = lambda lines, cycles: [
        {"xOffset_pix": line, "yOffset_pix": -cycle, "zOffset_um": line + cycle / 10}
        for line, cycle in zip(np.asarray(lines).ravel(), np.asarray(cycles).ravel())
    ]

    x, y, z = datafile.getOnlineMotion([6, 1, 4])

    np.testing.assert_array_equal(x, [3.0, 1.0, 1.0])
    np.testing.assert_array_equal(y, [-2.0, -1.0, -2.0])
    np.testing.assert_allclose(z, [3.2, 1.1, 1.2])
