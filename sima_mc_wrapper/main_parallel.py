#!/usr/bin/env python
# coding: utf-8

"""

Finds any .tif, .tiff, .h5 files in the requested directory and performs SIMA-based motion correction and fft-based bidirection 
offset correction, signal extraction, and neuropil correction. This code parallelizes the computation at the session level
by passing the multiple file paths (if there are more than one recordings) to the multiprocessing map function.

IMPORTANT RECOMENDATION: This pipeline requires the user to manually draw regions-of-interest (ROIs) on the mean
image (usually the motion-corrected output). The ROI zip file must end in "_RoiSet" with the extension ".zip".
If ROIs have not been drawn, it is recommended to use option 2 below (using files_to_analyze.py) and perform the
preprocessing in two runs/executions of this code (main_parallel). For the first run, perform only the motion
correction step. Take the H5 motion-corrected output and load it into FIJI (https://imagej.net/Fiji),
manually draw ROIs, and save the ROIs. Then (second run) edit files_to_analyze.py now setting signal_extraction
and neuropil_correction to True, and rerun this notebook/script (main_parallel).

Two simple ways to execute this in command line:  
A) main_parallel.py; then input the path_to_directory

B) main_parallel.batch_process(path_to_directory)

See these documentations for details
------------------------------------

https://github.com/losonczylab/sima
http://www.losonczylab.org/sima/1.3.2/
https://www.frontiersin.org/articles/10.3389/fninf.2014.00080/full

Required Packages
-----------------
Python 2.7, sima, glob, multiprocessing, numpy, h5py, pickle (optional if want to save displacement file)

Custom code requirements: sima_motion_correction, bidi_offset_correction, calculate_neuropil (written by Vijay Namboodiri), files_to_analyze

Parameters
----------

fdir : string
    root file directory containing the raw tif, tiff, h5 files 

Optional Parameters
-------------------

max_disp : list of two entries
    Each entry is an int. First entry is the y-axis maximum allowed displacement, second is the x-axis max allowed displacement.
    The number of pixel shift for each line cannot go above these values.
    Note: 50 pixels is approximately 10% of the FOV (512x512 pixels)
    
    Defaults to [30, 50]
    
save_displacement : bool 
    Whether or not to have SIMA save the calculated displacements over time. def: False; NOTE: if this is switched to True,
    it can double the time to perform motion correction.
    
    Defaults to False
    
Output
-------
motion corrected file (in the format of h5) with "_sima_mc" appended to the end of the file name

"*_sima_masks.npy" : numpy data file
    3D array containing 2D masks for each ROI

"*_extractedsignals.npy" : numpy data file
    array containing pixel-averaged activity time-series for each ROI

"_spatial_weights_*.h5" : h5 file
    contains spatial weighting masks of neuropil for each ROI

"_neuropil_signals_*.npy" : numpy data file
    array containing neuropil signals for each ROI

"_neuropil_corrected_signals_*.npy" : numpy data file
    array containing neuropil-corrected signals for each ROI

"*.json" : json file
    file containing the analysis parameters (fparams). Set by files_to_analyze.py or default parameters.
    to view the data, one can easily open in a text editor (eg. word or wordpad).

output_images : folder containing images

You will also find a folder containing plots that reflect how each executed preprocessing step performed. Examples are mean images for motion corrected data, ROI masks overlaid on mean images, extracted signals for each ROI, etc..
note: * is a wildcard indicating additional characters present in the file name

"""

# import native python packages
import glob
from fnmatch import fnmatch
import multiprocessing as mp
import os

# import custom codes
import sima_motion_bidi_correction
import calculate_neuropil
import single_file_process
import files_to_analyze


def batch_process(root_dir, max_disp=[30, 50], save_displacement=False):

    if not root_dir:  # if string is empty, load predefined list of files in files_to_analyze

        fparams = files_to_analyze.define_fparams()

    else:

        root_dir = root_dir + '\\'

        # declare initialize variables to do with finding files to analyze
        fparams = []
        fpaths = []
        types = ['*.tif', '*.tiff', '*.h5']
        exclude_strs = ['spatialweights', '_sima_mc', '_trim_dims', '_offset_vals']

        # find files to analyze
        for path, subdirs, files in os.walk(root_dir):  # os.walk grabs all paths and files in subdirectories
            for name in files:
                # make sure file of any image file
                if any([fnmatch(name, ext) for ext in types]) and not any(
                        [exclude_str in name for exclude_str in exclude_strs]):  # but don't include processed files
                    tmp_dict = {}
                    tmp_dict['fname'] = name
                    tmp_dict['fdir'] = path
                    tmp_dict['max_disp'] = max_disp
                    tmp_dict['save_displacement'] = save_displacement

                    print(tmp_dict['fname'])
                    fparams.append(tmp_dict)

    # print info to console
    num_files = len(fparams)
    if num_files == 0:
        raise Exception("No files to analyze!")
    print(str(num_files) + ' files to analyze')

    # determine number of cores to use and initialize parallel pool
    num_processes = min(mp.cpu_count(), num_files)
    print('Total CPU cores for parallel processing: ' + str(num_processes))
    pool = mp.Pool(processes=num_processes)

    # perform parallel processing; pass iterable list of file params to the analysis module selection code
    pool.map(single_file_process.process, fparams)

    ## for testing
    # for fparam in fparams:
    #    single_file_process.process(fparam)

    pool.close()
    pool.join()


if __name__ == "__main__":

    fdir = raw_input(r"Input root directory of tif, tiff, h5 files to analyze; note: Use FORWARD SLASHES to separate folder and leave "
                     r"the last backlash off!!  Otherwise leave blank to use files declared in file_to_analyze.py")

    batch_process(fdir)

