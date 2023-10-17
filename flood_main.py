import sys
from flood_preprocessing import Preprocessor
from denoiser import Denoiser
from clip_256 import Clipper

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

    input_dir = 'input/'
    output_dir = 'output/'
    # input/output will be created if not present

    shape = 'ribe_aoi/ribe_aoi.shp'
    # path to .shp file in unzipped shape dir

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

preprocessor = Preprocessor(input_dir, output_dir)
clipper = Clipper(output_dir)
denoiser = Denoiser(output_dir)

preprocessor.self_check(crs, polarization, unit, denoise_mode)
# TODO check for checkpoint folder (SAR2SAR) 
    # SAR2SAR may need to be recreated entirely to comply with tf v2

preprocessor.convert_to_geotiff(polarization)

clipper.clip_to_256(shape, crs)

preprocessor.to_linear()

denoiser.select_denoiser(denoise_mode)
# TODO fix (and locate) warnings about TF deprecations
# BUG enable GPU properly
#   tensorflow may need to be rewritten entirely

preprocessor.to_db()

# preprocessor.warp_files_to_crs(crs)
# TODO crate gdal options in Preprocessing without gdal. Pass string somehow? 
#   import gdaloptions as gdalopts ? only imports single thing, should be more efficient

preprocessor.realign_rasters()

preprocessor.clip_to_256(shape)

preprocessor.sort_output(polarization)