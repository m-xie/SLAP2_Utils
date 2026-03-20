# Subclasses of the primary SLAP2 Datafile
import h5py
import numpy as np
from .slapROI import slapROI
from .acquisitionContainer import AcquisitionContainer

class MetaData():

    """
            A class used to load a SLAP2 binary metadatafile for data processing. This is also an attribute for the datafile object

            Attributes
            ----------
            metadatafile : str
                The name of the metadata file.
            AcquisitionContainer : ``AcquisitionContainer``
                An instance of the AcquisitionContainer class that contain information related to the acquisition.
            acqDurationCycles : list
                A list containing 2 int values for cycle duration
            acqDuration_s : int
                The total time (in seconds) for the whole acquisition.
            acquisitionPathIdx : int
                The number that represent the path that the acquisitiion take place (either 1 or 2).
            acquisitionPathName : str
                The string that reiterate which path the acquisition takes place (either 'path 1' or 'path 2')  .
            aomActive : int
                Binary number that reporesent whether aom is action (0 = false, 1 = yes).
            aomVoltage : float
                The number of voltage in aom (in float).
            channelsSave : int
                The number that represent which channel saved the data. 
            dmdPixelsPerColumn : int
                The number of pixel along the column of the dmd. 
            dmdPixelsPerRow : int
                The number of pixel along the row of the dmd.    
            enableStack : list
                Binary number that reporesent whether stack is enabled (0 = false, 1 = yes).
            linePeriod_s : float
                The time it takes to conduct 1 slice (1/linePeriod_s gives the line rate for the microscope).
            remoteFocusPosition_um : int
                A number that represent the remoteFocusPosition for the center of the stack. 
            samplesPerLine : int
                The line rate for the microscope (1/samplesPerLine gives the linePeriod_s).

            
            Descriptions for methods:
            --------------------------

            Methods
            ----------
            __init__() :
                Fill the fields mentioned above. The method also loads the AcquisitionContainer using the __init__() method for the AcquisitionContainer

            Return
            -------
                Self with populated fields. 
                
            """

    def __init__(self, metadatafile):
        self.metadatafile = metadatafile
        self.AcquisitionContainer = None
        self.acqDurationCycles = ''
        self.acqDuration_s = ''
        self.acquisitionPathIdx = ''
        self.acquisitionPathName = ''
        self.aomActive = ''
        self.aomVoltage = ''
        self.channelsSave = ''
        self.dmdPixelsPerColumn = ''
        self.dmdPixelsPerRow = ''
        self.enableStack = ''
        self.linePeriod_s = ''
        self.machineConfiguration = []
        self.remoteFocusPosition_um = ''
        self.samplesPerLine = ''
        self.aomPowerFractionTarget = None

        def group_to_dict(hdf5_group, rfs):
            output = {}
            for key in hdf5_group.keys():
                if isinstance(hdf5_group[key], h5py.Group):
                    output[key] = group_to_dict(hdf5_group[key], rfs)
                else:
                    if isinstance(hdf5_group[key][:], np.ndarray) and hdf5_group[key][:].squeeze().ndim > 0 and hdf5_group[key][:].squeeze().size > 0 and isinstance(hdf5_group[key][:].squeeze()[0], h5py.Reference):
                        output[key] = []
                        for ref in hdf5_group[key][:].squeeze():
                            output[key].append(rfs[ref][:].squeeze())
                    else:
                        output[key] = hdf5_group[key][:].squeeze()
            return output
        
        with h5py.File(metadatafile, 'r') as hdf_file:
        # Read the contents of the HDF5 file into the metaData dictionary

            metaData = dict(hdf_file)
            for _key in metaData.keys():
                if _key == 'acquisitionPathName':
                    self.acquisitionPathName = ''.join(chr(x[0]) for x in hdf_file['acquisitionPathName'][:])
                elif _key == 'machineConfiguration':
                    num_devices = hdf_file[_key]['instanceName'].shape[1]
                    refs = hdf_file['#refs#']
                    for i in range(num_devices):
                        device_config_dict = {}
                        for prop in ['instanceName', 'instanceClass']:
                            device_config_dict[prop] = ''.join(chr(int(x)) for x in refs[hdf_file[_key][prop][0,i]][:].flatten())
                        
                        try:
                            device_config_dict['configuration'] = group_to_dict(refs[hdf_file[_key]['configuration'][0,i]], refs)
                        except:
                            # TODO: Handle the error case
                            print(f"Warning: No configuration found for device {device_config_dict['instanceName']}")
                            device_config_dict['configuration'] = None
                        self.machineConfiguration.append(device_config_dict)
                else:
                    try:
                        metaData[_key] = hdf_file[_key][:].squeeze()
                        setattr(self, _key, hdf_file[_key][:].squeeze())
                    except:   
                        metaData[_key] = hdf_file[_key]
                        
                
            self.AcquisitionContainer = AcquisitionContainer(self.metadatafile)
