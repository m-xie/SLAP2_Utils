import os
import re
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .datafile import DataFile


class MultiDataFiles:
    """
    Aggregate multiple SLAP2 DataFile instances that belong to the same
    acquisition but were split across files (e.g., multiple cycles).

    This mirrors the MATLAB `MultiDataFiles` class behavior:
    - Discover sibling `.dat` files by stripping an optional `-CYCLE<idx>` suffix
      from a provided filename and loading all matching files.
    - Sort constituent files chronologically by their first-cycle time inferred
      from `metaData.AcquisitionContainer` when available; otherwise preserve
      natural sorted order as a fallback.
    - Expose key `DataFile`-like attributes from the first file for convenience
      and compute aggregate counters like `numCycles` and `totalNumLines`.

    Notes
    -----
    The current Python `DataFile` implementation does not expose
    `getLineHeader` or `firstLineTimestamp`. Hence, for sorting we use a stable
    natural order on filenames as a reasonable approximation. If timestamp
    metadata becomes available, update `_sort_files_in_place` accordingly.
    """

    def __init__(self, filename: Optional[str] = None):
        if not filename:
            raise ValueError("filename must be provided in Python implementation")

        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: {filename}")

        base_dir, base_name = os.path.split(filename)
        name_no_ext, ext = os.path.splitext(base_name)
        if ext.lower() != ".dat":
            raise AssertionError("Not a SLAP2 .dat file")

        # Strip optional '-CYCLE-<digits>' suffix from basename to create a group stem
        # MATLAB used: regexprep(n_base,'-CYCLE-?[0-9]+$','')
        stem = re.sub(r"-CYCLE-?[0-9]+$", "", name_no_ext, flags=re.IGNORECASE)

        # Collect all .dat files whose name starts with the stem
        candidate_files = [
            os.path.join(base_dir, f)
            for f in os.listdir(base_dir)
            if f.lower().endswith(".dat") and os.path.splitext(f)[0].startswith(stem)
        ]

        if not candidate_files:
            raise FileNotFoundError("No matching .dat files found for multi-file aggregation")

        # Load DataFile objects
        self.hDataFiles: List[DataFile] = [DataFile(f) for f in candidate_files]

        # Sort in-place using a robust heuristic (see docstring)
        self._sort_files_in_place()

        # Mirror selected public attributes from the first file for convenience
        first = self.hDataFiles[0]
        self.header = first.header
        self.metaData = first.metaData
        self.lineDataStartIdxs = first.lineDataStartIdxs
        self.lineDataNumElements = first.lineDataNumElements
        self.datFileName = first.datFileName

        # Aggregates
        self.numCycles = int(np.sum([df.numCycles for df in self.hDataFiles]))
        self.totalNumLines = int(self.numCycles * int(self.header['linesPerCycle']))

    def _sort_files_in_place(self) -> None:
        """
        Sort constituent `DataFile` instances in-place.

        If future `DataFile` exposes a reliable per-file timestamp such as
        `firstLineTimestamp`, sort by that. For now, sort by a tuple of
        (cycle_index_extracted_from_name, filename) to achieve stable ordering.
        """
        def extract_cycle_index(df: DataFile) -> int:
            name = os.path.splitext(os.path.basename(df.datFileName))[0]
            m = re.search(r"-CYCLE-?([0-9]+)$", name, flags=re.IGNORECASE)
            if m:
                try:
                    return int(m.group(1))
                except Exception:
                    return 1_000_000_000
            # Fallback when suffix is not present: try to infer from TRIAL
            m2 = re.search(r"-TRIAL([0-9]+)$", name, flags=re.IGNORECASE)
            if m2:
                try:
                    return int(m2.group(1))
                except Exception:
                    return 1_000_000_000
            return 1_000_000_000

        self.hDataFiles.sort(key=lambda df: (extract_cycle_index(df), df.datFileName))

    # ----------------------------- Public API ------------------------------
    def delete(self) -> None:
        """Placeholder for MATLAB parity (no-op in Python)."""
        # In Python, garbage collection will handle resources. If needed,
        # add explicit close logic for memmaps or file handles here.
        pass

    def checkFileIntegrity(self) -> None:
        """
        Placeholder for MATLAB parity.

        The Python `DataFile` raises upon inconsistent headers or missing files
        during initialization. Extend here if deeper integrity checks are added
        in the future.
        """
        return None

    def getLineDataIdxs(
        self,
        lineIdx: Sequence[int],
        cycleIdx: Optional[Sequence[int]] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Map global (lineIdx, cycleIdx) to per-file indices and offsets.

        Returns
        -------
        tuple
            (lineDataStartIdx, lineDataNumElements, fileIdx, cycleIdx_file)
            All arrays are 1-D numpy arrays aligned with inputs.
        """
        lines_per_cycle = int(self.header['linesPerCycle'])

        lineIdx = np.asarray(lineIdx, dtype=np.int64).ravel()
        if cycleIdx is None:
            # Derive cycle indices from global line indices
            cycleIdx = np.floor((lineIdx - 1) / lines_per_cycle).astype(np.int64) + 1
            lineIdx = ((lineIdx - 1) % lines_per_cycle).astype(np.int64) + 1
        else:
            cycleIdx = np.asarray(cycleIdx, dtype=np.int64).ravel()

        if np.any(lineIdx < 1) or np.any(cycleIdx < 1):
            raise ValueError("Indices must be positive (Matlab-style)")
        if np.any(lineIdx > lines_per_cycle):
            raise AssertionError("lineIdx exceeds linesPerCycle")
        if np.any(cycleIdx > self.numCycles):
            raise AssertionError("cycleIdx exceeds numCycles")

        file_cycles = np.array([df.numCycles for df in self.hDataFiles], dtype=np.int64)
        file_cycles_end = np.cumsum(file_cycles)
        file_cycles_start = np.empty_like(file_cycles_end)
        file_cycles_start[0] = 1
        file_cycles_start[1:] = file_cycles_end[:-1] + 1

        # Determine which file each global cycle belongs to
        # fileIdx is 1-based for parity with MATLAB signatures returned
        fileIdx = np.sum((file_cycles_start[:, None] <= cycleIdx[None, :]), axis=0)
        fileIdx = fileIdx.astype(np.int64)

        cycleIdx_file = cycleIdx - file_cycles_start[fileIdx - 1] + 1

        bytes_per_cycle = int(self.header['bytesPerCycle'])
        cycle_offset = (cycleIdx_file - 1) * bytes_per_cycle // 2
        lineDataStartIdx = np.asarray(self.lineDataStartIdxs, dtype=np.int64)[lineIdx - 1] + cycle_offset
        lineDataNumElements = np.asarray(self.lineDataNumElements, dtype=np.int64)[lineIdx - 1]

        return lineDataStartIdx, lineDataNumElements, fileIdx, cycleIdx_file

    def getLineData(
        self,
        lineIndices: Sequence[int],
        cycleIndices: Optional[Sequence[int]] = None,
        iChannel: Optional[Sequence[int]] = None
    ) -> List[np.ndarray]:
        """
        Retrieve line data spanning multiple files. Returns a list aligned to
        the input index order.
        """
        _, _, fileIdxs, localCycleIdxs = self.getLineDataIdxs(lineIndices, cycleIndices)

        fileIdxs = np.asarray(fileIdxs, dtype=np.int64)
        localCycleIdxs = np.asarray(localCycleIdxs, dtype=np.int64)
        lineIndices = np.asarray(lineIndices, dtype=np.int64).ravel()

        unique_files = np.unique(fileIdxs)
        outputs: List[Optional[np.ndarray]] = [None] * lineIndices.shape[0]

        for uf in unique_files:
            mask = (fileIdxs == uf)
            li = lineIndices[mask]
            ci = localCycleIdxs[mask]
            block = self.hDataFiles[int(uf) - 1].getLineData(li, ci, iChannel)
            # `block` is a list aligned with the local mask ordering
            idxs = np.flatnonzero(mask)
            for j, k in enumerate(idxs):
                outputs[k] = block[j]

        # type: ignore - all entries must be filled by construction
        return outputs  # type: ignore[return-value]


