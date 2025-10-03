import os
import numpy as np
import re

from .subclasses.metadata import MetaData
from .utils.file_header import load_file_header_v2


class DataFile():
    """
            A class used to load a SLAP2 binary datafile for data processing.

            Attributes
            ----------
            MAGIC_NUMBER : np.uint32
                A constant used to validate the data file.
            filename : str
                The name of the data file.
            metaDataFileName : str
                The name of the metadata file.
            datFileName : str
                The name of the data file with the '.dat' extension.
            rawData : list
                A list to store the raw data from the file.
            metaData : MetaData
                An instance of the MetaData class to handle metadata.
            StreamId : None
                A placeholder for stream ID.
            header : None
                A placeholder for the file header.
            lineHeaderIdxs : None
                A placeholder for the line header indices.
            fastZs : list
                A list to store fast Z values.
            zPixelReplacementMaps : None
                A placeholder for the Z pixel replacement maps.
            lineNumSuperPixels : None
                A placeholder for the number of super pixels per line.
            lineSuperPixelIDs : list
                A list to store super pixel IDs for each line.
            lineSuperPixelZIdxs : list
                A list to store Z indices for each line's super pixels.
            lineDataNumElements : list
                A list to store the number of elements in each line of data.
            lineDataStartIdxs : list
                A list to store the start indices of each line of data.
            numCycles : int
                The number of cycles in the data file.

            
            Descriptions for methods:
            --------------------------
           
            
            Methods
            ----------
            __init__() :
                Initialize the fields with values and call the _load_file() metbod.

            Return
            -------
                Self with populated fields.
            
            Methods
            ----------
            _load_file() :
                Loads the data and metadata files, and populates the attributes. Has no input besides the self object.

            Return
            -------
                Self with populated fields. This includes filename, metadataFileName, datFileName, fastZs, lineSuperPixelZIdxs, lineSuperPixelIDS, zPixelReplacementMap2, lineNumSuperPixels, lineSuperPixelIDs, lineFastZIdxs, rawData and header.
            
            Methods
            ----------
            load_file_header(rawData) :
                Loads the file header and validates the data format. Needs rawData as input with the self object.

            Return
            -------
                Return header and edited self with populated fields, including lineDataStartIdxs, lineDataNumElements, lineDataNumElements 
                
        """
    
    def __init__(self, datfile):  

        self.MAGIC_NUMBER = np.uint32(322379495)
        self.filename = datfile
        self.metaDataFileName = ''
        self.datFileName = ''
        self.rawData = []
        self.metaData = None
        self.StreamId = None
        self.header = None
        self.lineHeaderIdxs = None
        self.fastZs =  None
        self.zPixelReplacementMaps = None
        self.lineNumSuperPixels = None
        self.lineSuperPixelIDs = []
        self.lineSuperPixelZIdxs = []
        self.lineDataNumElements = []
        self.lineDataStartIdxs = []
        self.numCycles=0

        self._load_file()
         
        
    def _load_file(self):

        
        # Loading file names and check whether file is found
        base_dir, filename = os.path.split(self.filename)
        n_base = re.sub(r'-TRIAL\d+','',os.path.splitext(filename)[0],flags=re.IGNORECASE)
        n_base = re.sub(r'-CYCLE\d+','',n_base,flags=re.IGNORECASE)

        self.metaDataFileName = os.path.join(base_dir, n_base + '.meta')
        self.datFileName = os.path.join(base_dir, filename)

        if not os.path.isfile(self.metaDataFileName):
            raise FileNotFoundError(f'Metadata file not found: {self.metaDataFileName}')
        self.metaData = MetaData(self.metaDataFileName)
        # Subfunction of loading parse plan
        def load_parse_plan(self, metaData):   
            def filter_z_pixel_replacement_maps(z_maps):
                # Using list comprehension for simplified logic
                return [list(filter(lambda x: x[0] != x[1], map_)) for map_ in z_maps]

            if not metaData.AcquisitionContainer.newFormat:
                fastz = metaData.AcquisitionContainer.ParsePlan['zs'][:]
                final_fastz = [-10203] #initiating with a value thats never found
                for i in fastz:
                    final_fastz.append(i[0])

                self.fastZs = final_fastz

                #Check if it breaks
                self.lineSuperPixelZIdxs = metaData.AcquisitionContainer.ParsePlan['acqParsePlan']['sliceIdx']
                self.lineSuperPixelIDs = [x.T for x in metaData.AcquisitionContainer.ParsePlan['acqParsePlan']['superPixelID']]
                
                self.zPixelReplacementMaps = metaData.AcquisitionContainer.ParsePlan['pixelReplacementMaps']
                
                #Using list comprehension for simplified logic
                self.lineNumSuperPixels = [len(ids) for ids in self.lineSuperPixelIDs]
                self.lineFastZIdxs = np.zeros(len(self.lineSuperPixelZIdxs))
                for lineIdx in range(len(self.lineSuperPixelZIdxs)):
                    lineZIdxs_=self.lineSuperPixelZIdxs[lineIdx]
            
                    if len(lineZIdxs_) != 1:
                        self.lineFastZIdxs[lineIdx] = 0
                    else:
                        self.lineFastZIdxs[lineIdx] = lineZIdxs_[0][0] + 1
            else:
                # print('Using new metadata format...')

                self.fastZs = np.unique(np.concatenate([zs for zs in metaData.AcquisitionContainer.AcquisitionPlan['activeZs'] if zs.size > 0]))
                self.lineSuperPixelIDs = metaData.AcquisitionContainer.AcquisitionPlan['superPixelIDs']
                self.lineSuperPixelZIdxs = metaData.AcquisitionContainer.AcquisitionPlan['activeZs']
                self.zPixelReplacementMaps = metaData.AcquisitionContainer.AcquisitionPlan['pixelReplacementMaps']
                self.zPixelReplacementMapsNonRedudant = filter_z_pixel_replacement_maps(self.zPixelReplacementMaps)
                self.lineNumSuperPixels = np.prod([ids.size for ids in self.lineSuperPixelIDs])

                self.lineFastZIdxs = np.zeros(len(self.lineSuperPixelZIdxs))
                for lineIdx in range(len(self.lineSuperPixelZIdxs)):
                    lineZIdxs_=self.lineSuperPixelZIdxs[lineIdx]
                    if lineZIdxs_.size == 0:
                        self.lineFastZIdxs[lineIdx] = 0
                    else:
                        self.lineFastZIdxs[lineIdx] = lineZIdxs_[0]
            
        
        # Add additional attributes from the MetaData file
        load_parse_plan(self, self.metaData)

        if not os.path.isfile(self.datFileName):
            raise FileNotFoundError('Data file not found.')
        self.rawData = np.memmap(self.filename, dtype='uint32')
        self.header = self.load_file_header(self.rawData)
        

    # Function for loading file header:
    def load_file_header(self, rawData):
        raw_data = np.frombuffer(rawData, dtype=np.uint32)
        if raw_data.dtype != 'uint32':
            raw_data.dtype('uint32')

        # See if magic number matches, returns an error if that is not the case
        file_magic_number = raw_data[0]
        assert file_magic_number == self.MAGIC_NUMBER, 'Data format error. This is not a SLAP2 data file.'
        
        
        # Currently, we have only implemented file version 2
        file_format_version = raw_data[1]
        assert file_format_version <= 2, 'Unknown format version'
        if file_format_version == 2:
            header, self.numCycles = load_file_header_v2(self, raw_data)
        else:
            raise ValueError(f'Unknown file format version: {file_format_version}')

        # Load Indices
        raw_data  =  np.frombuffer(raw_data, dtype=np.uint16)
        if raw_data.dtype != 'uint16':
            raw_data.astype('uint16')

        # Load different fields in the object accordingly

        line_idxs = np.zeros(int(header['linesPerCycle']), dtype=int)
        line_size_bytes = np.zeros(int(header['linesPerCycle']), dtype=np.uint32)
        line_idxs[0] = header['firstCycleOffsetBytes'] // 2 + 1
        line_size_bytes[0] = raw_data[line_idxs[0]-1]
        for idx in range(1, int(header['linesPerCycle'])):
            line_idxs[idx] = line_idxs[idx - 1] + line_size_bytes[idx - 1] // 2
            line_size_bytes[idx] = raw_data[line_idxs[idx]-1]


        line_header_idxs = line_idxs
        self.lineDataStartIdxs = line_idxs + header['lineHeaderSizeBytes'] // 2
        self.lineDataNumElements = (line_size_bytes - header['lineHeaderSizeBytes']) // 2
        self.lineDataNumElements = [int(x) for x in self.lineDataNumElements]
        self.lineDataStartIdxs = [int(x) for x in self.lineDataStartIdxs] 



        # May need to update this conditional in the future
        #if not 'referenceTimestamp' in list(header.keys()):
        #    header.referenceTimestamp = np.uint64(0)
        #    first_line_header = self.get_line_header(1, 1)
        #    self.header.referenceTimestamp = first_line_header.timestamp
        
        #first_line_header = obj.get_line_header(1, 1)
        #obj.header.referenceTimestamp = first_line_header.timestamp
        return header

    def getLineData(self, lineIndices, cycleIndices, iChannel=None, method="Cython"):
        """Get line data from the data file.

        Parameters
        ----------
        lineIndices : array_like
            Vector of positive integers specifying line indices (matlab indexing)
        cycleIndices : array_like 
            Vector of positive integers specifying cycle indices (matlab indexing)
        iChannel : array_like, optional
            Vector of positive integers specifying channel indices (matlab indexing) (default is all channels)
        method : str, optional
            Method to use for data retrieval, either "Cython" or "Python" or "Numpy" (default is "Cython")

        Returns
        -------
        lineData : list
            Line data for the specified indices
        """
        # Default to all channels if not specified
        if iChannel is None:
            iChannel = np.arange(1, self.header['numChannels'] + 1)

        lineIndices = np.asarray(lineIndices, dtype=np.int64).ravel()
        cycleIndices = np.asarray(cycleIndices, dtype=np.int64).ravel()
        iChannel = np.asarray(iChannel, dtype=np.int64).ravel()

        if not np.all(lineIndices > 0) or not np.all(cycleIndices > 0) or not np.all(iChannel > 0):
            raise ValueError("All indices must be positive integers (Matlab indexing)")

        if np.any(lineIndices > self.header['linesPerCycle']):
            raise ValueError("Line indices must be <= linesPerCycle")

        if np.any(cycleIndices > self.numCycles):
            raise ValueError("Cycle indices must be <= numCycles")
        if len(cycleIndices) != len(lineIndices):
            raise ValueError("Number of cycle indices must match number of line indices")

        if np.any(iChannel > self.header['numChannels']):
            raise ValueError("Channel indices must be <= numChannels")
        
        hMemmap = np.memmap(self.datFileName, dtype='int16', mode='r')
        
        try:
            try:
                from .fast_line_data import fast_get_line_data
                lineData = fast_get_line_data(
                    hMemmap,
                    self.lineDataNumElements,
                    self.lineDataStartIdxs,
                    int(self.header['numChannels']),
                    int(self.header['firstCycleOffsetBytes']),
                    int(self.header['bytesPerCycle']),
                    lineIndices,
                    cycleIndices,
                    iChannel
                )
            except ImportError:
                lineData = []
                for idx in range(len(lineIndices)):
                    samples_per_channel = int(self.lineDataNumElements[lineIndices[idx]-1]) // int(self.header['numChannels'])
                    tmpData = np.empty((samples_per_channel, len(iChannel)), dtype=np.int16)
                    precomputed_offset = (self.lineDataStartIdxs[lineIndices[idx]-1]
                                          + (cycleIndices[idx] - 1) * int(self.header['bytesPerCycle']) // 2)
                    for ch in range(len(iChannel)):
                        offset = samples_per_channel * (iChannel[ch]-1) + precomputed_offset - 1
                        tmpData[:, ch] = hMemmap[offset:offset + samples_per_channel]
                    lineData.append(tmpData)
        finally:
            if hasattr(hMemmap, '_mmap'):
                hMemmap._mmap.close()
            del hMemmap

        return lineData