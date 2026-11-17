# slap2-utils
[![Tests](https://github.com/Peter-Hogg/SLAP2_Utils/actions/workflows/python-test.yml/badge.svg)](https://github.com/Peter-Hogg/SLAP2_Utils/actions/workflows/python-test.yml)[![Documentation](https://github.com/Peter-Hogg/SLAP2_Utils/actions/workflows/sphinx.yml/badge.svg)](https://peter-hogg.github.io/SLAP2_Utils/)[![DOI](https://joss.theoj.org/papers/10.21105/joss.08054/status.svg)](https://doi.org/10.21105/joss.08054)
## Overview
The `slap2-utils` library is designed to facilitate the reading of SLAP2 (Scanned Line Angular Projection Microscopy version 2) binary files using Python. This utility aims to support researchers and developers working with data from SLAP2 two-photon microscopes by providing an interface to manipulate and analyze these files directly in Python as an alternative to a Matlab-based workflow. The SLAP2 microscope is a commercially available kit from MBF Bioscience (https://www.mbfbioscience.com/products/slap2). The detailed documentation can be found by clicking the documentation icon above `Overview`.

## Features
- **Reading SLAP2 Binary Files**: Convert SLAP2 proprietary binary data into accessible formats for Python.
- **Metadata Parsing**: Extract and utilize metadata associated with SLAP2 data files.
- **Data Manipulation**: Tools to manipulate and process data points read from the binary file.
- **Trace Extraction**: Tools to extract and generate traces from ROIs imaged in integrated scan mode.
- **Data Inspection**: A GUI to inspect and review data stored in the binary file.

## Line headers and online motion

SLAP2 line headers contain the microscope's recorded online X/Y motion offsets
in pixels, Z offset in micrometers, FPGA timestamp, acquisition flags, and line
identifiers. They can be read from a single file with `DataFile` or across
cycle-split files with `MultiDataFiles`:

```python
from slap2_utils.datafile import DataFile
from slap2_utils.multidatafiles import MultiDataFiles

data_file = DataFile("recording.dat")
header = data_file.getLineHeader(1, 1)

multi_file = MultiDataFiles("recording-CYCLE1.dat")
x_pixels, y_pixels, z_um = multi_file.getOnlineMotion([1, 303, 605])
```

`getLineHeader` and `getOnlineMotion` use one-based indices for compatibility
with the existing reader API and MATLAB. `getOnlineMotion` accepts global line
IDs and preserves request order. These methods
expose offsets recorded by the microscope; they do not spatially warp or
motion-correct fluorescence data.

## Installation
Install with pip
```bash
pip install slap2-utils
```


Clone this repository

```bash
git clone https://github.com/Peter-Hogg/SLAP2_Utils.git
```
## Contributing

Contributions are welcome! If you'd like to contribute, please fork the repository and use a new branch for your contributions. Pull requests are welcome. Please report bugs, as we're still refining this library over time.

## License

This project is licensed under the Mozilla Public License Version 2.0 - see the LICENSE.md file for details.

## Credits and Acknowledgements
This library was developed by Peter Hogg and Jerry Tong. It's a rework of several Matlab tools from MBF with added utility functions. Thanks to all contributors who have helped in refining this tool and helped with the project.

