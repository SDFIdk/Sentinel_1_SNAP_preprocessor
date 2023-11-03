import sys
from flood_preprocessing import Preprocessor
from denoiser import Denoiser
from clip_256 import Clipper
from snap_converter import SNAP_preprocessor

if __name__== '__main__':

    ### ----------------------------------- ########### ----------------------------------- ###
    ### ----------------------------------- USER INPUTS ----------------------------------- ###
    ### ----------------------------------- ########### ----------------------------------- ###

    user = None
    password = None
    # Change user/password vars to login for https://scihub.copernicus.eu/apihub
    # If both variables are set to 'None', script will look for .netrc file for authentication
    #  See https://sentinelsat.readthedocs.io/en/stable/api_overview.html#authentication

    # input_dir = "D:/s1_snap_netcdf/"
    # output_dir = "D:/s1_snap_geotiff/"

    safe_dir = 'D:/s1_raw_data_ribe/'
    # netcdf_dir = 'input/'
    netcdf_dir = 'D:/s1_test_nc/'
    output_dir = 'output/'
    # input/output will be created if not present

    shape = 'ribe_aoi/ribe_aoi.shp'
    # path to .shp file in unzipped shape dir

    snap_graph = 'new_preproc_graph.xml'
    #xml file with SNAP preprocessing stack. 
    # TODO ensure xml is available on github!

    gpt_exe = 'C:/Users/b307579/AppData/Local/Programs/snap/bin/gpt.exe'
    # Path to SNAPs gpt.exe. SNAP is required for this program to run.

    mean_dict = 'clipped_data_means.pkl'
    # pkl file with SAFE data averages relevant to all input files
    # TODO build this in somehow...

    crs = 'EPSG:25832'
    # CRS in EPSG:XXXXX format. Reverts to EPSG:4326 if invalid 

    polarization = ['VV', 'VH']
    # list of strings or single string. Accepts any combination of VV, VH, HV, HH.

    unit = 'decibel'
    # if 'decibel', script will output to decibel (10*log(10)), else does not convert.

    denoise_mode = 'SAR2SAR'
    # denoise_mode = 'mean'
    # if 'SAR2SAR', script will use ML based denoising.
    # if 'SAR2SAR', self check will look for a .pkl file and check that it has relevant files.
    
# TODO option for FTP export

preprocessor = Preprocessor(netcdf_dir, output_dir)
clipper = Clipper(output_dir)
denoiser = Denoiser(output_dir, safe_dir, shape)

# preprocessor.self_check(crs, polarization, unit, denoise_mode, mean_dict)
# TODO check for checkpoint folder (SAR2SAR) 
# TODO check that gpt exe points to SNAP

SNAP_preprocessor.safe_preprocessing(safe_dir, snap_graph, netcdf_dir, gpt_exe)
# TODO add the SAFE mean extractor


preprocessor.convert_to_geotiff(polarization)
# TODO fix the metadata!

clipper.start_clipper(shape, crs)

preprocessor.to_linear(max_zero = True)

# denoiser.select_denoiser(denoise_mode, mean_dict)
# TODO fix (and locate) warnings about TF deprecations
# BUG enable GPU properly
#   tensorflow may need to be rewritten entirely
# SAR2SAR may need to be recreated entirely to comply with tf v2

# preprocessor.to_db()

# preprocessor.warp_files_to_crs(crs)
# # BUG possibly deprecated now
# # TODO crate gdal options in Preprocessing without gdal. Pass string somehow? 
# #   import gdaloptions as gdalopts ? only imports single thing, should be more efficient

# preprocessor.realign_rasters()

# clipper.start_clipper(shape, crs)

# preprocessor.sort_output(polarization)