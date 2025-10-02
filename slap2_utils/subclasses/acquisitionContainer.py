import h5py
from .slapROI import slapROI
import numpy as np

class AcquisitionContainer():
    """
        A class used to load a SLAP2 binary metadatafile for data processing. This is also an attribute for the datafile object

        Attributes
        ----------
        AcquisitionPlan : dict
            A dictionary that contains 3 subinstances of ['AcquisitionContainer'], ['AcquisitionPlan'], and ['acqParsePlan'].
        DmdPatternSequence : list
            A list containing information related to the patterning of the sequences.
        ParsePlan : dict
            A dictionary that contains various instances related to how region of interest is parsed through.
        ROIs : list
            A list that contains information related to the region of interests.
        ScannerParameters : dict
            A dictionary that stores information related to the scanned parameter (not implemented yet, consider removing).
        constructor : str
            A string that describes how the plan is constructed.
            
            
        Descriptions for methods:
        --------------------------

        Methods
        ----------
        __init__() :
            Fill the fields mentioned above.

        Return
        -------
            Self with populated fields. 
                
    """
    
    def __init__(self, metadatafile):
        self.AcquisitionPlan = {}
        self.DmdPatternSequence = None
        self.ParsePlan = {}
        self.ROIs = []
        self.ScannerParameters = ''
        self.constructor = ''


        acqParsePlan = {}
        with h5py.File(metadatafile, 'r') as hdf_file:
            # Read the contents of the HDF5 file into the metaData dictionary
            acq_plan_obj = hdf_file['AcquisitionContainer']['AcquisitionPlan']
            if isinstance(acq_plan_obj, h5py.Group):
                print('[WARNING] Failed on old SLAP2 metadata format. Trying on new format...')
                self.DmdPatternSequence = hdf_file['AcquisitionContainer']['DmdPatternSequence'][:]

                self.AcquisitionPlan = {}
                self.AcquisitionPlan['constructor'] = ''.join(chr(x[0]) for x in hdf_file['AcquisitionContainer']['AcquisitionPlan']['constructor'])
                self.AcquisitionPlan['fovSize'] = hdf_file['AcquisitionContainer']['AcquisitionPlan']['fovSize'][:].squeeze()

                _refs = []
                for index in range(len(hdf_file['AcquisitionContainer']['AcquisitionPlan']['superPixelIDs'][:])):
                    _refs.append(hdf_file['AcquisitionContainer']['AcquisitionPlan']['superPixelIDs'][:][index][0])
                self.AcquisitionPlan['superPixelIDs'] = [hdf_file[_ref][:].flatten() if len(hdf_file[_ref].shape) == 2 else np.zeros((0,0),dtype=np.uint32) for _ref in _refs]

                _refs = []
                for index in range(len(hdf_file['AcquisitionContainer']['AcquisitionPlan']['activeZs'][:])):
                    _refs.append(hdf_file['AcquisitionContainer']['AcquisitionPlan']['activeZs'][:][index][0])
                self.AcquisitionPlan['activeZs'] = [hdf_file[_ref][:].flatten() if len(hdf_file[_ref].shape) == 2 else np.zeros((0,0),dtype=np.uint32) for _ref in _refs]

                self.AcquisitionPlan['pixelDilationX'] = hdf_file['AcquisitionContainer']['AcquisitionPlan']['pixelDilationX'][:]
                _refs = []
                for index in range(len(hdf_file['AcquisitionContainer']['AcquisitionPlan']['pixelDilationY'][:])):
                    _refs.append(hdf_file['AcquisitionContainer']['AcquisitionPlan']['pixelDilationY'][:][index][0])
                self.AcquisitionPlan['pixelDilationY'] = [hdf_file[_ref][:].flatten() if len(hdf_file[_ref].shape) == 2 else np.zeros((0,0),dtype=np.uint32) for _ref in _refs]

                self.AcquisitionPlan['isSimpleRaster'] = hdf_file['AcquisitionContainer']['AcquisitionPlan']['isSimpleRaster'][:].squeeze()
                self.AcquisitionPlan['rasterOffsetXY'] = hdf_file['AcquisitionContainer']['AcquisitionPlan']['rasterOffsetXY'][:].squeeze()
                self.AcquisitionPlan['rasterSizeXY'] = hdf_file['AcquisitionContainer']['AcquisitionPlan']['rasterSizeXY'][:].squeeze()
                self.AcquisitionPlan['zTrajectory'] = hdf_file['AcquisitionContainer']['AcquisitionPlan']['zTrajectory'][:].squeeze()

                _refs = []
                for index in range(len(hdf_file['AcquisitionContainer']['AcquisitionPlan']['rasterROIMasks'][:])):
                    _refs.append(hdf_file['AcquisitionContainer']['AcquisitionPlan']['rasterROIMasks'][:][index][0])
                self.AcquisitionPlan['rasterROIMasks'] = [hdf_file[_ref][:].T for _ref in _refs]

                _refs = []
                for index in range(len(hdf_file['AcquisitionContainer']['AcquisitionPlan']['blockROIMasks'][:])):
                    _refs.append(hdf_file['AcquisitionContainer']['AcquisitionPlan']['blockROIMasks'][:][index][0])
                self.AcquisitionPlan['blockROIMasks'] = [hdf_file[_ref][:].T for _ref in _refs]

                _refs = []
                for index in range(len(hdf_file['AcquisitionContainer']['AcquisitionPlan']['pixelReplacementMaps'][:])):
                    _refs.append(hdf_file['AcquisitionContainer']['AcquisitionPlan']['pixelReplacementMaps'][:][index][0])
                self.AcquisitionPlan['pixelReplacementMaps'] = [hdf_file[_ref][:] for _ref in _refs]

                for i in range(hdf_file['AcquisitionContainer']['ROIs']['rois'][:].shape[0]):
                    roi_ref = hdf_file['AcquisitionContainer']['ROIs']['rois'][i][0]
                    self.ROIs.append(slapROI(hdf_file, roi_ref))
            else:
                #old file format
                # Do not load old place holder
                #self.AcquisitionPlan = hdf_file['AcquisitionContainer']['AcquisitionPlan'][:]
                self.DmdPatternSequence = hdf_file['AcquisitionContainer']['DmdPatternSequence'][:]

                for i in range(hdf_file['AcquisitionContainer']['ROIs']['rois'][:].shape[0]):
                    roi_ref = hdf_file['AcquisitionContainer']['ROIs']['rois'][i][0]
                    self.ROIs.append(slapROI(hdf_file, roi_ref))
                    
                    
                for _key in hdf_file['AcquisitionContainer']['ParsePlan'].keys():
                    try:
                        self.AcquisitionPlan[_key] = hdf_file['AcquisitionContainer']['ParsePlan'][_key][:]
                    except:
                        if _key == 'acqParsePlan':
                            _data = {}
                            for _subkey in hdf_file['AcquisitionContainer']['ParsePlan']['acqParsePlan'].keys():
                                _data[_subkey] = []
                                for _ref in (list(hdf_file['AcquisitionContainer']['ParsePlan']['acqParsePlan'][_subkey][:])):
                                    _data[_subkey].append(hdf_file[_ref[0]][:])
                                acqParsePlan[_key] = _data

                
                _refs = []
                for index in range(len(hdf_file['AcquisitionContainer']['ParsePlan']['pixelReplacementMaps'][:])):
                    _refs.append(hdf_file['AcquisitionContainer']['ParsePlan']['pixelReplacementMaps'][:][index][0])
                self.AcquisitionPlan['pixelReplacementMaps'] = [hdf_file[_ref][:] for _ref in _refs]
                self.AcquisitionPlan['acqParsePlan'] = acqParsePlan['acqParsePlan']